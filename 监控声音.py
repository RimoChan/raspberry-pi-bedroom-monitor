import json
import time
import random
import logging

import pyaudio
import numpy as np
import librosa.core.convert

from 打点 import start_http_server, save
from utils import 冷却时间


n_fft = 256
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


def 奸(音) -> dict:
    map = [*librosa.core.convert.fft_frequencies(sr=RATE, n_fft=n_fft)]
    D = np.abs(librosa.stft(音, n_fft=n_fft)).mean(axis=1).tolist()
    assert len(map) == len(D)
    return {map[i]: D[i] for i in range(len(map))}


try:
    with open('声音记录.json') as f:
        _记录 = json.load(f)
except Exception as e:
    logging.exception('加载记录出错了！')
    _记录 = []


def 记录(d: dict):
    global _记录
    _记录.append(d)
    _记录 = _记录[-200:]
    with open('声音记录.json', 'w') as f:
        f.write(json.dumps(_记录))


def 修正(新d) -> dict:
    小d = {}
    for d in _记录 + [新d]:
        for k, v in d.items():
            小d[k] = min(v, 小d.get(k, 999))
    return {k: v - 小d[k] for k, v in 新d.items()}


@冷却时间(15)
def 上报声音():
    try:
        音 = 录音()
        d = 奸(音)
        d = {str(int(k)).zfill(5): v for k, v in d.items()}           # grafana只支持按字符串排序
        if len(_记录) < 10 or random.random() < 0.01:
            记录(d)
        d = 修正(d)
        for k, v in d.items():
            save('audio_frequencies', v, {'frequency': k})
    except Exception as e:
        logging.exception(e)
    

while True:
    上报声音()
    time.sleep(0.1)
