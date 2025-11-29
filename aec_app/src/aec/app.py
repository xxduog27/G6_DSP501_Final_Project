import toga
from toga.style import Pack
from toga.style.pack import COLUMN

from audio_worker import AudioWorker
from devices import list_devices


class AecApp(toga.App):
    def startup(self):
        self.worker = None
        devices = list_devices()
        input_devices = [d for d in devices if d["max_input"] > 0]
        output_devices = [d for d in devices if d["max_output"] > 0]

        self.input_choices = [f'{d["index"]}: {d["name"]}' for d in input_devices]
        self.output_choices = [f'{d["index"]}: {d["name"]}' for d in output_devices]

        self.input_select = toga.Selection(items=self.input_choices)
        self.output_select = toga.Selection(items=self.output_choices)

        self.use_aec_switch = toga.Switch("Use AEC", value=False)
        self.dither_switch = toga.Switch("Dither", value=False)
        self.soft_clip_switch = toga.Switch("Soft Clip", value=False)

        self.frame_size_slider = toga.Slider(min=80, max=480, value=160)
        self.buffer_frames_slider = toga.Slider(min=1, max=8, value=4)

        start_btn = toga.Button("Start", on_press=self.start_audio)
        stop_btn = toga.Button("Stop", on_press=self.stop_audio)

        controls = toga.Box(children=[
            toga.Label("Input Device"),
            self.input_select,
            toga.Label("Output Device"),
            self.output_select,
            self.use_aec_switch,
            self.dither_switch,
            self.soft_clip_switch,
            toga.Label("Frame Size"),
            self.frame_size_slider,
            toga.Label("Buffer Frames"),
            self.buffer_frames_slider,
            start_btn,
            stop_btn
        ], style=Pack(direction=COLUMN, padding=10))

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = controls
        self.main_window.show()

    def _parse_index(self, selection):
        if selection.value is None:
            return None
        try:
            return int(selection.value.split(":")[0])
        except Exception:
            return None

    def start_audio(self, widget):
        in_idx = self._parse_index(self.input_select)
        out_idx = self._parse_index(self.output_select)

        frame_size = int(self.frame_size_slider.value)
        buffer_frames = int(self.buffer_frames_slider.value)

        self.worker = AudioWorker(
            input_device_index=in_idx,
            output_device_index=out_idx,
            use_aec=self.use_aec_switch.value,
            sample_rate=16000,
            frame_size=frame_size,
            buffer_frames=buffer_frames,
            dither=self.dither_switch.value,
            soft_clip=self.soft_clip_switch.value,
        )
        self.worker.start_worker()

    def stop_audio(self, widget):
        if self.worker:
            self.worker.stop_worker()
            self.worker = None


def main():
    return AecApp("AEC App", "org.example.aec")


if __name__ == "main":
    main().main_loop()