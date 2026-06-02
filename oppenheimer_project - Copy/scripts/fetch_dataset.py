import os
import urllib.request
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data_source")
os.makedirs(DATA_DIR, exist_ok=True)
OUTPUT_PATH = os.path.join(DATA_DIR, "oppenheimer_corpus.txt")

print("⚡ Starting Corrected Pure-Text Dataset Pipeline...")

BIO_URL = "https://archive.org/download/j.-robert-oppenheimer-archive/Robert%20Oppenheimer/Oppenheimer%2C%20Robert%20-%20Letters%20and%20Recollections%20%5Bed.%20Smith%20%26%20Weiner%5D%20%28Harvard%2C%201980%29_djvu.txt"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

try:
    print("📡 Pulling from direct archival data streams...")
    req = urllib.request.Request(BIO_URL, headers=headers)
    
    with urllib.request.urlopen(req, timeout=45) as response:
        raw_text = response.read().decode('utf-8')
    print(f"📥 Successfully downloaded raw text ({len(raw_text):,} characters).")

    print("🧹 Scrubbing OCR noise, broken lines, and system layout artifacts...")
    
    clean_text = re.sub(r'(?i)page\s+\d+(\s+of\s+\d+)?', '', raw_text)
    
    clean_text = clean_text.replace('\n', ' ')
    
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    clean_text = re.sub(r'\s+([,\.!;\?\)])', r'\1', clean_text)
    
    clean_text = re.sub(r'(LETTERS\s+\d+|CHAPTER\s+\d+)', r'\n\n\1', clean_text)
    
    clean_text = clean_text.strip()
    
    manual_append_header = (
        f"{clean_text}\n\n"
        f"================================================================================\n"
        f"MANUAL ACADEMIC SECTOR: RESEARCH PAPERS & QUANTUM FIELD EQUATIONS\n"
        f"================================================================================\n\n"
        f"/* PASTE YOUR COPIED PAPER TEXTS AND MATH MATRICES DIRECTLY BELOW THIS LINE */\n\n"
    )

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(manual_append_header)
        
    print(f"\n🚀 Success! Millions of characters of real biography deployed to: {OUTPUT_PATH}")
    print("💡 Open the file now—it will be pure, clean paragraphs!")

except Exception as e:
    print(f"\n❌ Script failed to execute: {e}")