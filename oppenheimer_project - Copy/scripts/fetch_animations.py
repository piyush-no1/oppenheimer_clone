import os
import urllib.request

ASSETS_DIR = "assets"
os.makedirs(ASSETS_DIR, exist_ok=True)

ANIMATION_URLS = {
    "anim_general.json": "https://raw.githubusercontent.com/LottieFiles/lottie-player/master/demo/loading.json",
    "anim_physics.json": "https://raw.githubusercontent.com/samuelosborn/lottie-animation-library/master/math.json",
    "anim_history.json": "https://raw.githubusercontent.com/samuelosborn/lottie-animation-library/master/book.json"
}

print("🎨 Initializing Updated Frontend Animation Asset Pipeline...")
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

for file_name, url in ANIMATION_URLS.items():
    destination_path = os.path.join(ASSETS_DIR, file_name)
    print(f"📡 Querying asset stream for: {file_name}...")
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response, open(destination_path, 'wb') as out_file:
            out_file.write(response.read())
        print(f"📥 Successfully deployed local vector asset to: {destination_path}")
    except Exception as e:
        print(f"❌ Failed to automate download for {file_name}: {e}")

print("\n🚀 Core animation asset layer sync complete!")