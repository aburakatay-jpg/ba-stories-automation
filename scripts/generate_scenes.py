#!/usr/bin/env python3
import sys
import json
import os
import random
import requests
import base64
import time

def generate_image_ai(prompt, api_key):
    # Yatay (16:9) video için özel sinematik korku promptu
    enhanced_prompt = f"{prompt}. Dark spooky atmosphere, cinematic horror movie lighting, highly detailed, photorealistic, no text, empty background, 16:9 aspect ratio, wide landscape shot."
    
    if api_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:predict?key={api_key}"
            payload = {
                "instances": [{"prompt": enhanced_prompt}],
                "parameters": {
                    "sampleCount": 1,
                    "aspectRatio": "16:9",
                    "outputOptions": {"mimeType": "image/jpeg"}
                }
            }
            resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
            if resp.ok:
                b64 = resp.json()["predictions"][0]["bytesBase64Encoded"]
                return base64.b64decode(b64)
            else:
                print(f"⚠️ Gemini API hatası: {resp.text}")
        except Exception as e:
             print(f"⚠️ API İletişim Hatası: {e}")

    # Yedek Sistem (Pollinations AI - Yatay Format 1920x1080)
    print("🔄 Yedek AI'a geçiliyor...")
    safe_prompt = requests.utils.quote(enhanced_prompt)
    seed_value = random.randint(1, 9999999) 
    fallback_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1920&height=1080&nologo=true&seed={seed_value}"
    
    resp = requests.get(fallback_url)
    if resp.ok:
        return resp.content
    return None

def main():
    if len(sys.argv) < 4:
        print("Kullanım: generate_scenes.py <tema_json> <senaryo_txt> <cikti_klasoru>")
        sys.exit(1)
        
    tema_json = sys.argv[1]
    senaryo_txt = sys.argv[2]
    output_dir = sys.argv[3]
    os.makedirs(output_dir, exist_ok=True)

    gemini_api_key = os.environ.get("GEMINI_API_KEY", "")

    with open(tema_json, "r", encoding="utf-8") as f:
        tema = json.load(f)
    
    tema_konusu = tema.get("tema", "korku")
    tema_mekani = tema.get("mekan", "karanlık mekan")

    with open(senaryo_txt, "r", encoding="utf-8") as f:
        script = f.read()

    # Senaryoyu kelimelere böl ve 18 eşit sahneye ayır (11 dakikalık video için ideal görsel değişimi)
    words = script.split()
    toplam_sahne = 18
    chunk_size = len(words) // toplam_sahne
    if chunk_size == 0:
        chunk_size = 1
        
    kamera_acilari = [
        "Wide tracking shot", "Extreme wide establishing shot", 
        "Low angle ominous perspective", "Cinematic drone shot", 
        "Eye-level mysterious view", "Over the shoulder eerie shot"
    ]

    for i in range(toplam_sahne):
        # O sahnenin anahtar kelimelerini yakala
        chunk_words = " ".join(words[i*chunk_size : (i+1)*chunk_size][:5])
        sahne_promptu = f"Concept: {tema_konusu} at {tema_mekani}. Element: {chunk_words}. {random.choice(kamera_acilari)}"
        
        print(f"Sahne {i+1}/{toplam_sahne} üretiliyor...")
        image_bytes = generate_image_ai(sahne_promptu, gemini_api_key)
        
        if image_bytes:
            img_path = os.path.join(output_dir, f"scene_{i+1:03d}.jpg")
            with open(img_path, "wb") as f:
                f.write(image_bytes)
            print(f"✅ Kaydedildi: {img_path}")
        
        # API limitine takılmamak için 5 saniye bekle
        time.sleep(5)

if __name__ == "__main__":
    main()
