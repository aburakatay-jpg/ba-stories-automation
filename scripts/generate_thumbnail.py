#!/usr/bin/env python3
import sys
import json
import os
import urllib.request
import urllib.parse
import time

def get_thumbnail(prompt, output_path):
    # Boşlukları ve özel karakterleri URL formatına uygun hale getiriyoruz
    safe_prompt = urllib.parse.quote(prompt)
    seed = int(time.time())
    
    # Pollinations AI - Hızlı, ücretsiz ve API Key gerektirmez
    url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1920&height=1080&nologo=true&seed={seed}"
    
    print(f"🖼️ Kapak fotoğrafı üretiliyor...")
    
    # API hata verirse diye 3 kez tekrar deneme mantığı
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 30 saniye zaman aşımı sınırı
            urllib.request.urlretrieve(url, output_path)
            print("✅ Kapak fotoğrafı başarıyla üretildi!")
            return True
        except Exception as e:
            print(f"⚠️ Hata (Deneme {attempt+1}): {e}")
            time.sleep(5)
            
    print("❌ Kapak fotoğrafı üretilemedi!")
    sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Kullanım: python generate_thumbnail.py <tema.json> <baslik.txt> <output.jpg>")
        sys.exit(1)
        
    tema_file = sys.argv[1]
    baslik_file = sys.argv[2]
    output_file = sys.argv[3]
    
    try:
        with open(tema_file, "r", encoding="utf-8") as f:
            tema_data = json.load(f)
            konsept = tema_data.get("tema", "Korku hikayesi")
            mekan = tema_data.get("mekan", "Karanlık bir yer")
    except:
        konsept = "Korku hikayesi"
        mekan = "Karanlık bir yer"
        
    prompt = f"Concept: {konsept} at {mekan}. YouTube thumbnail, highly detailed, extreme contrast, mysterious, terrifying, cinematic lighting, dark spooky atmosphere, focal point on a creeping silhouette or creepy object, vivid colors in shadows, photorealistic, no text, 16:9 aspect ratio."
    
    get_thumbnail(prompt, output_file)
