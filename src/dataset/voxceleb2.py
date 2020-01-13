import os
from torch.utils.data import Dataset
import errno
import shutil
import random

import pathlib
AUDIO_EXTENSIONS = [
    '.wav', '.mp3', '.flac', '.sph', '.ogg', '.opus', '.m4a',
    '.WAV', '.MP3', '.FLAC', '.SPH', '.OGG', '.OPUS', '.M4A'
]

def is_audio_file(filename):
    return any(filename.endswith(extension) for extension in AUDIO_EXTENSIONS)


def make_manifest(dir):
    audios = []
    dir = os.path.expanduser(dir)
    for target in sorted(os.listdir(dir)):
        d = os.path.join(dir, target)
        if not os.path.isdir(d):
            continue

        for root, _, fnames in sorted(os.walk(d)):
            for fname in fnames:
                if is_audio_file(fname):
                    path = os.path.join(root, fname)
                    item = path
                    audios.append(item)
    return audios

def load_txts(dir):
    assert "not implemented"

class Voxceleb2(Dataset):
    dset_path = 'voxceleb2'

    def make_speaker_dic(self, root):
        speakers = [
            str(speaker.name) for speaker in pathlib.Path(root).glob('dev/aac/*/')]
        print(speakers)
        speakers = sorted([speaker for speaker in speakers])
        speaker_dic = {speaker: i for i, speaker in enumerate(speakers)}
        return 
    def __init__(self, root, downsample=False, transform=None, target_transform=None, download=True, dev_mode=False, ratio=0.8):
        super(Voxceleb2, self).__init__()

        self.root = os.path.expanduser(root)
        self.raw_folder = '../data/voxceleb2/raw'
        #if os.path.isdir('..' + os.sep + self.raw_folder):
        #    self.raw_folder = '..' + os.sep + self.raw_folder
        self.downsample = downsample
        self.transform = transform
        self.target_transform = target_transform
        self.dev_mode = dev_mode
        self.data = []
        self.labels = []
        self.chunk_size = 1000
        self.num_samples = 0
        self.max_len = 0
        self.cached_pt = 0

        if download:
            self.download()

        dset_abs_path = os.path.join(
            self.root, self.raw_folder, self.dset_path)

        self.audios = make_manifest(dset_abs_path)
        self.utterences = load_txts(dset_abs_path)
        self.speaker_dic = self.make_speaker_dic(dset_abs_path)

        random.shuffle(self.audios)
        split = int(len(self.audios)*ratio)

        self.audios_train = self.audios[:split]
        self.audios_val = self.audios[split:]

    def download(self):
        assert "not implemented"
