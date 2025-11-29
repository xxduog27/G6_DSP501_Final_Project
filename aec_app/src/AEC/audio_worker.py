import threading
import time
import pyaudio
import numpy as np

try:
    from pyaec import Aec
    AEC_AVAILABLE = True
except Exception:
    AEC_AVAILABLE = False


class AudioWorker(threading.Thread):
    def __init__(
            self,
            input_device_index=None,
            output_device_index=None,
            use_aec=True,
            sample_rate=16000,
            frame_size=160,          # 10ms @ 16kHz
            buffer_frames=4,         # tổng buffer = frame_size * buffer_frames
            prefer_wasapi=True,
            dither=False,
            soft_clip=False,
    ):
        super().__init__(daemon=True)
        self.in_idx = input_device_index
        self.out_idx = output_device_index
        self.use_aec = use_aec and AEC_AVAILABLE
        self.rate = sample_rate
        self.frame_size = frame_size
        self.buffer_frames = buffer_frames
        self.prefer_wasapi = prefer_wasapi
        self.dither = dither
        self.soft_clip = soft_clip

        self.format = pyaudio.paInt16
        self.channels = 1
        self.filter_length = int(self.rate * 0.4)

        self._running = threading.Event()
        self._running.clear()

        self._p = None
        self._in = None
        self._out = None
        self._aec = None

    def _maybe_dither(self, samples: np.ndarray):
        if not self.dither:
            return samples
        noise = np.random.uniform(-1, 1, samples.shape) * 0.5
        out = samples.astype(np.float32) + noise
        out = np.clip(out, -32768, 32767).astype(np.int16)
        return out

    def _maybe_soft_clip(self, samples: np.ndarray):
        if not self.soft_clip:
            return samples
        x = samples.astype(np.float32) / 32768.0
        y = np.tanh(2.0 * x)
        return (y * 32768.0).astype(np.int16)

    def start_worker(self):
        if self.is_alive():
            return
        self._running.set()
        self.start()

    def stop_worker(self):
        self._running.clear()
        try:
            self.join(timeout=2.0)
        except Exception:
            pass

    def run(self):
        self._p = pyaudio.PyAudio()

        if self.use_aec:
            try:
                self._aec = Aec(self.frame_size, self.filter_length, self.rate, False)
            except Exception:
                self._aec = None
                self.use_aec = False

        fpb = self.frame_size * self.buffer_frames

        self._in = self._p.open(
            format=self.format, channels=self.channels, rate=self.rate,
            input=True, input_device_index=self.in_idx,
            frames_per_buffer=fpb
        )

        self._out = self._p.open(
            format=self.format, channels=self.channels, rate=self.rate,
            output=True, output_device_index=self.out_idx,
            frames_per_buffer=fpb
        )

        last_output_bytes = b'\x00' * (self.frame_size * 2)

        while self._running.is_set():
            try:
                in_data = self._in.read(self.frame_size, exception_on_overflow=False)
                in_samples = np.frombuffer(in_data, dtype=np.int16)
                ref_samples = np.frombuffer(last_output_bytes, dtype=np.int16)

                if self.use_aec and (self._aec is not None):
                    processed = self._aec.cancel_echo(in_samples, ref_samples)
                    samples = np.array(processed, dtype=np.int16)
                else:
                    samples = in_samples

                samples = self._maybe_soft_clip(samples)
                samples = self._maybe_dither(samples)

                out_data = samples.tobytes()
                self._out.write(out_data)
                last_output_bytes = out_data

            except Exception:
                time.sleep(0.001)

        try:
            self._in.close()
        except Exception:
            pass
        try:
            self._out.close()
        except Exception:
            pass
        try:
            self._p.terminate()
        except Exception:
            pass