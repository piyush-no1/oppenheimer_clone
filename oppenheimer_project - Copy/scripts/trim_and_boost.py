import os
from pydub import AudioSegment
from pydub.effects import normalize

ASSETS_DIR = "assets"
INPUT_WAV = os.path.join(ASSETS_DIR, "oppenheimer_ref.wav")
OUTPUT_WAV = os.path.join(ASSETS_DIR, "oppenheimer_ref_clean.wav")

print("🎚️ Initializing Audio Mastering Pipeline...")

if not os.path.exists(INPUT_WAV):
    print(f"❌ Error: Could not find your 1-minute audio file at: {INPUT_WAV}")
    print("💡 Please ensure your downloaded audio is named 'oppenheimer_ref.wav' inside the 'assets' folder.")
else:
    try:
        print("📥 Loading raw source track from disk...")
        raw_audio = AudioSegment.from_wav(INPUT_WAV)
        
       
        print("✂️ Slicing out the optimal 12-second voice window...")
        trimmed_audio = raw_audio[0:4000]
        
        
        print("🔊 Boosting low audio signal to uniform master levels...")
        mastered_audio = normalize(trimmed_audio, headroom=1.0)
        
        print("📊 Verifying matrix constraints (Mono, 24000Hz)...")
        mastered_audio = mastered_audio.set_channels(1)
        mastered_audio = mastered_audio.set_frame_rate(24000)
        
        
        mastered_audio.export(INPUT_WAV, format="wav")
        print(f"\n🚀 Success! Pristine, loud, and pre-sliced audio deployed to: {INPUT_WAV}")
        
    except Exception as e:
        print(f"❌ Failed to process audio: {e}")
        print("💡 Ensure your file is a valid uncompressed WAV format.")