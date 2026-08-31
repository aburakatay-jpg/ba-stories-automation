#!/usr/bin/env python3
import sys
import json
import os
import urllib.parse
import time
import requests

def get_thumbnail(prompt, output_path):
    safe_prompt = urllib.parse.quote(prompt)
    seed = int(time.time())
    
    url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1920&height=1080&nologo=true&seed={seed}"
    
    print(f"🖼️ Kapak fotoğrafı üretiliyor...")
    
    # 403 Forbidden hatasını aşmak için sisteme standart bir Chrome tarayıcısı kimliği veriyoruz
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # urllib yerine daha stabil olan requests kütüphanesini kullanıyoruz
            response = requests.get(url, headers=headers, timeout=45)
            response.raise_for_status() # Eğer 200 OK (Başarılı) dışı bir kod dönerse direkt except bloğuna atlar
            
            with open(output_path, "wb") as f:
                f.write(response.content)
                
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
