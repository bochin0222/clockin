import time
import librosa
import numpy as np
from scipy import signal

from torch.utils import data


# 加载并预处理音频
def load_audio(audio_path, mode='train', win_length=400, sr=44100, hop_length=160, n_fft=512, spec_len=257):
    # 读取音频数据

    # 数据拼接
    if mode == 'train':
        wav, sr_ret = librosa.load(audio_path, sr=sr)
        extended_wav = np.append(wav, wav)
        if np.random.random() < 0.3:
            extended_wav = extended_wav[::-1]
    elif mode == 'load':
        wav, sr_ret = librosa.load(audio_path, sr=sr)
        print(type(wav[0]))
        extended_wav = np.append(wav, wav[::-1]) 
              
    else:
        wav = audio_path
        extended_wav = np.append(wav, wav[::-1])
        print(extended_wav.shape)
    # yf1 = f_high(extended_wav, sr)
    # 计算短时傅里叶变换
    # linear = librosa.stft(extended_wav, n_fft=n_fft, win_length=win_length, hop_length=hop_length)
    # linear_T = linear.T
    # mag, _ = librosa.magphase(linear_T)
    # mag_T = mag.T
    melspec = librosa.feature.melspectrogram(extended_wav, sr, n_fft=n_fft, hop_length=hop_length, n_mels=257)
    mag_T = librosa.power_to_db(melspec)  
    freq, freq_time = mag_T.shape
    assert freq_time >= spec_len, "非静音部分长度不能低于1.3s"
    if mode == 'train':
        # 随机裁剪
        rand_time = np.random.randint(0, freq_time - spec_len)
        spec_mag = mag_T[:, rand_time:rand_time + spec_len]
    else:
        spec_mag = mag_T[:, :spec_len]
    mean = np.mean(spec_mag, 0, keepdims=True)
    std = np.std(spec_mag, 0, keepdims=True)
    spec_mag = (spec_mag - mean) / (std + 1e-5)
    spec_mag = spec_mag[np.newaxis, :]
    return spec_mag

def f_high(y,sr):
    b,a = signal.butter(10, 2000/(sr/2), btype='highpass')
    yf = signal.lfilter(b,a,y)
    return yf

# 数据加载器
class CustomDataset(data.Dataset):
    def __init__(self, data_list_path, model='train', spec_len=257):
        super(CustomDataset, self).__init__()
        with open(data_list_path, 'r') as f:
            self.lines = f.readlines()
        self.model = model
        self.spec_len = spec_len

    def __getitem__(self, idx):
        audio_path, label = self.lines[idx].replace('\n', '').split('\t')
        spec_mag = load_audio(audio_path, mode=self.model, spec_len=self.spec_len)
        return spec_mag, np.array(int(label), dtype=np.int64)

    def __len__(self):
        return len(self.lines)
