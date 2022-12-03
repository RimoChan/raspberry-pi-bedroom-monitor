import time
import logging
from typing import Optional

import pyaudio
import numpy as np
import librosa.core.convert

from 打点 import start_http_server, save
from utils import 冷却时间


n_fft = 1024
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 11025
RECORD_SECONDS = 14


start_http_server(9193)


def 录音() -> np.ndarray:
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    frames = []
    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
    stream.stop_stream()
    stream.close()
    p.terminate()
    y = np.frombuffer(b''.join(frames), dtype=np.int16) / 32768.0
    return y


def 奸(音) -> Optional[dict]:
    if 音 is None:
        return None
    map = [*librosa.core.convert.fft_frequencies(sr=RATE, n_fft=n_fft)]
    D = np.abs(librosa.stft(音, n_fft=n_fft)).mean(axis=1).tolist()
    assert len(map) == len(D)
    return {map[i]: D[i] for i in range(len(map))}


@冷却时间(15)
def 上报声音():
    try:
        音 = 录音()
        for k, v in 奸(音).items():
            save('audio_frequencies', v, {'frequency': str(int(k)).zfill(5)})    # grafana只支持按字符串排序
    except Exception as e:
        logging.exception(e)
    

while True:
    上报声音()
    time.sleep(0.1)
