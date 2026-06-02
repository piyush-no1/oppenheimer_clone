import os
import sys
import torch
import re
import numpy as np
import soundfile as sf
import torchaudio

INIT_ERROR = None
CACHED_REF_TENSOR = None
CACHED_SAMPLE_RATE = None

def robust_torchaudio_load(filepath, *args, **kwargs):
    global CACHED_REF_TENSOR, CACHED_SAMPLE_RATE
    filepath_str = str(filepath)
    if CACHED_REF_TENSOR is not None and "oppenheimer_ref.wav" in os.path.basename(filepath_str):
        return CACHED_REF_TENSOR, CACHED_SAMPLE_RATE
    data, sr = sf.read(filepath_str)
    if data.ndim == 1:
        tensor = torch.from_numpy(data).float().unsqueeze(0)
    else:
        tensor = torch.from_numpy(data).float().t()
    return tensor, sr

def robust_torchaudio_save(filepath, src, sample_rate, *args, **kwargs):
    filepath_str = str(filepath)
    if torch.is_tensor(src):
        src = src.cpu().numpy()
    if src.ndim == 2:
        src = src.T
    sf.write(filepath_str, src, sample_rate)

torchaudio.load = robust_torchaudio_load
torchaudio.save = robust_torchaudio_save

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
REF_WAV_PATH = os.path.join(BASE_DIR, "assets", "oppenheimer_ref.wav")
OUTPUT_WAV_PATH = os.path.join(BASE_DIR, "assets", "oppenheimer_output.wav")

class OppenheimerNeuralVoice:
    def __init__(self):
        global CACHED_REF_TENSOR, CACHED_SAMPLE_RATE
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        if not os.path.exists(REF_WAV_PATH):
            raise FileNotFoundError(f"Reference voice asset missing at: {REF_WAV_PATH}")
            
        data, sr = sf.read(REF_WAV_PATH)
        if data.ndim == 1:
            CACHED_REF_TENSOR = torch.from_numpy(data).float().unsqueeze(0)
        else:
            CACHED_REF_TENSOR = torch.from_numpy(data).float().t()
        CACHED_SAMPLE_RATE = sr
        
        from f5_tts.api import F5TTS
        self.tts = F5TTS(device=self.device)
        
        self.ref_text = "We knew the world would not be the same."

    def generate_voice(self, text: str) -> str:
        """Synthesizes high-fidelity speech sentence-by-sentence to prevent alignment repetition loops."""
        clean_text = re.sub(r'[\$\*`#_\[\]\(\)\{\}\<\>\\\/+\-=~^]', '', text).strip()
        if not clean_text:
            return None
            
        sentences = re.split(r'(?<=[.!?])\s*', clean_text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 1]
        
        if not sentences:
            return None
            
        audio_chunks = []
        target_sample_rate = None
        
        for sentence in sentences:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
            wav, sr, _ = self.tts.infer(
                ref_file=REF_WAV_PATH,
                ref_text=self.ref_text,
                gen_text=sentence
            )
            
            if torch.is_tensor(wav):
                wav = wav.detach().cpu().numpy()
            
            wav = wav.squeeze()
            audio_chunks.append(wav)
            target_sample_rate = sr
            
        if audio_chunks and target_sample_rate:
            final_waveform = np.concatenate(audio_chunks)
            os.makedirs(os.path.dirname(OUTPUT_WAV_PATH), exist_ok=True)
            sf.write(OUTPUT_WAV_PATH, final_waveform, target_sample_rate)
            return OUTPUT_WAV_PATH
            
        return None

try:
    voice_cloner = OppenheimerNeuralVoice()
except Exception as e:
    INIT_ERROR = str(e)
    voice_cloner = None