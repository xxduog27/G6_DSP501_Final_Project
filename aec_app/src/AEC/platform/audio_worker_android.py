import threading
import numpy as np
from time import sleep

try:
    from jnius import autoclass, jarray
except Exception:
    autoclass = None

try:
    from pyaec import Aec
    AEC_AVAILABLE = True
except Exception:
    AEC_AVAILABLE = False

SAMPLE_RATE = 16000
FRAME_SIZE = 160
BYTES_PER_SAMPLE = 2

class AndroidAudioWorker(threading.Thread):
    def __init__(self, use_aec=True):
        super().__init__(daemon=True)
        self.use_aec = use_aec and AEC_AVAILABLE
        self.running = False
        self.recorder = None
        self.player = None
        self.aec = None

        self.AudioRecord = None
        self.AudioTrack = None
        self.AudioFormat = None
        self.AudioManager = None
        self.MediaRecorder = None
        self.AudioAttributes = None

        if autoclass:
            try:
                self.AudioRecord = autoclass('android.media.AudioRecord')
                self.AudioTrack = autoclass('android.media.AudioTrack')
                self.AudioFormat = autoclass('android.media.AudioFormat')
                self.AudioManager = autoclass('android.media.AudioManager')
                self.MediaRecorder = autoclass('android.media.MediaRecorder')
                self.AudioAttributes = autoclass('android.media.AudioAttributes')
            except Exception:
                pass

    def setup(self):
        if not self.AudioRecord or not self.AudioTrack or not self.AudioFormat or not self.MediaRecorder:
            return False

        CHANNEL_IN_MONO = self.AudioFormat.CHANNEL_IN_MONO
        CHANNEL_OUT_MONO = self.AudioFormat.CHANNEL_OUT_MONO
        ENCODING_PCM_16BIT = self.AudioFormat.ENCODING_PCM_16BIT

        min_rec = self.AudioRecord.getMinBufferSize(SAMPLE_RATE, CHANNEL_IN_MONO, ENCODING_PCM_16BIT)
        min_play = self.AudioTrack.getMinBufferSize(SAMPLE_RATE, CHANNEL_OUT_MONO, ENCODING_PCM_16BIT)

        rec_buf_size = max(min_rec, FRAME_SIZE * BYTES_PER_SAMPLE * 8)
        play_buf_size = max(min_play, FRAME_SIZE * BYTES_PER_SAMPLE * 8)

        # Constructor direct (ổn với nhiều phiên bản)
        self.recorder = self.AudioRecord(self.MediaRecorder.AudioSource.MIC,
                                         SAMPLE_RATE, CHANNEL_IN_MONO,
                                         ENCODING_PCM_16BIT, rec_buf_size)

        self.player = self.AudioTrack(self.AudioManager.STREAM_MUSIC,
                                      SAMPLE_RATE, CHANNEL_OUT_MONO,
                                      ENCODING_PCM_16BIT, play_buf_size,
                                      self.AudioTrack.MODE_STREAM)
        if self.use_aec:
            try:
                self.aec = Aec(FRAME_SIZE, int(SAMPLE_RATE * 0.4), SAMPLE_RATE, False)
            except Exception:
                self.aec = None
                self.use_aec = False
        return True

    def start_worker(self):
        if self.running:
            return
        if not self.setup():
            return
        self.running = True
        self.start()

    def stop_worker(self):
        self.running = False
        try:
            self.join(timeout=2.0)
        except Exception:
            pass

    def run(self):
        try:
            self.recorder.startRecording()
            self.player.play()
        except Exception:
            self.running = False
            return

        last_out = b'\x00' * (FRAME_SIZE * BYTES_PER_SAMPLE)

        while self.running:
            try:
                read_bytes = FRAME_SIZE * BYTES_PER_SAMPLE
                buf = jarray('b', read_bytes)
                ret = self.recorder.read(buf, 0, read_bytes)
                if ret <= 0:
                    sleep(0.001)
                    continue

                in_samples = np.frombuffer(bytes(buf), dtype=np.int16)
                ref = np.frombuffer(last_out, dtype=np.int16)

                if self.use_aec and self.aec is not None:
                    try:
                        processed = self.aec.cancel_echo(in_samples, ref)
                        out_bytes = np.array(processed, dtype=np.int16).tobytes()
                    except Exception:
                        out_bytes = bytes(buf)
                else:
                    out_bytes = bytes(buf)

                self.player.write(jarray('b', out_bytes), 0, len(out_bytes))
                last_out = out_bytes
            except Exception:
                break

        try:
            self.recorder.stop()
            self.player.stop()
            self.recorder.release()
            self.player.release()
        except Exception:
            pass