import os
import subprocess

ASSETS_DIR = "assets"
os.makedirs(ASSETS_DIR, exist_ok=True)

FINAL_WAV = os.path.join(ASSETS_DIR, "oppenheimer_ref.wav")

TARGET_URL = "https://www.youtube.com/watch?v=eCWBAX9Ihw0"

print("📡 Initiating Direct Public Stream Extraction Pipeline...")

try:
    cmd = [
        "python", "-m", "yt_dlp",
        "-x", "--audio-format", "wav",
        "--audio-quality", "0",
        "--postprocessor-args", "-ac 1 -ar 24000",
        "-o", FINAL_WAV,
        TARGET_URL
    ]
    
    print("📥 Stream caching and data processing active...")
    subprocess.run(cmd, check=True)
    
    print(f"\n🚀 Success! Pristine reference audio deployed cleanly to: {FINAL_WAV}")

except Exception as e:
    print(f"\n❌ Pipeline failed: {e}")
    print("\n💡 Speed-Run Alternative:")
    print("If your system missing an internal path variable, just head to a web tool,")
    print(f"convert the link '{TARGET_URL}' to a WAV file,")
    print("and drop it directly into your folder as 'assets/oppenheimer_ref.wav'!")