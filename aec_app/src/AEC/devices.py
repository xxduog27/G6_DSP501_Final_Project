import pyaudio

def list_devices():
    p = pyaudio.PyAudio()
    devices = []
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        devices.append({
            "index": info["index"],
            "name": info["name"],
            "max_input": info.get("maxInputChannels", 0),
            "max_output": info.get("maxOutputChannels", 0),
        })
    p.terminate()
    return devices