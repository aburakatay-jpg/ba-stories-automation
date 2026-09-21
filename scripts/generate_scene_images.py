#!/usr/bin/env python3
import os
import sys
import json
import time
import urllib.parse
import requests

def download_image(url, save_path):
    try:
        resp = requests.get(url, timeout=45, headers={"User-Agent": "Mozilla/5.0"})
        if resp.ok and len(resp.content) > 5000:
            with open(save_path, "wb") as f:
                f.write(resp.content)
            return True
    except Exception as e:
        print(f"İndirme hatası ({url[:40]}...): {e}")
    return False

def generate_with_gemini_imagen(prompt, save_path):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return False
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key={api_key}"
    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": "9:16",
            "outputMimeType": "image/jpeg"
        }
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=60)
        if resp.ok:
            data = resp.json()
            import base64
            b64_data = data["predictions"][0]["bytesBase64Encoded"]
            with open(save_path, "wb") as f:
                f.write(base64.b64decode(b64_data))
            print(f"✅ Gemini Imagen ile görsel üretildi: {save_path}")
            return True
        else:
            print(f"⚠️ Gemini Imagen yanıtı: {resp.status_code}")
    except Exception as e:
        print(f"Gemini Imagen hatası: {e}")
    return False

def generate_with_pollinations(prompt, save_path):
    print("🔄 Yedek AI motoru (Pollinations) ile görsel üretiliyor...")
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&model=flux&nologo=true&seed={int(time.time())}"
    if download_image(url, save_path):
        print(f"✅ Yedek görsel başarıyla üretildi: {save_path}")
        return True
    return False

def generate_with_pexels(query, save_path):
    pexels_key = os.environ.get("PEXELS_API_KEY")
    if not pexels_key:
        return False
        
    print("🔄 Pexels ile stok görsel aranıyor...")
    url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(query)}&orientation=portrait&per_page=5"
    headers = {"Authorization": pexels_key}
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.ok:
            data = resp.json()
            photos = data.get("photos", [])
            if photos:
                img_url = photos[0]["src"]["portrait"]
                if download_image(img_url, save_path):
                    print(f"✅ Pexels görseli indirildi: {save_path}")
                    return True
    except Exception as e:
        print(f"Pexels hatası: {e}")
    return False

def main():
    if len(sys.argv) < 5:
        print("Kullanım: generate_scene_images.py <tema.json> <baslik.txt> <senaryo.txt> <output_dir>")
        sys.exit(1)

    tema_file = sys.argv[1]
    baslik_file = sys.argv[2]
    senaryo_file = sys.argv[3]
    output_dir = sys.argv[4]
    os.makedirs(output_dir, exist_ok=True)

    tema_info = {}
    if os.path.exists(tema_file):
        try:
            with open(tema_file, "r", encoding="utf-8") as f:
                tema_info = json.load(f)
        except Exception:
            pass

    mekan = tema_info.get("mekan", "dark foggy abandoned place")
    tema = tema_info.get("tema", "horror eerie mystery")

    # 3 farklı sahne açısı ve atmosferi
    prompts = [
        f"Cinematic horror wide angle shot of {mekan}, {tema}, dark misty night, eerie lighting, photorealistic, 8k, highly detailed, vertical 9:16",
        f"Creepy close up mysterious view inside {mekan}, shadowy figure in background, cinematic darkness, horrifying atmosphere, vertical 9:16",
        f"Terrifying low angle view of {mekan}, thick fog, abandoned place, cold moonlight, chilling horror movie scene, vertical 9:16"
    ]

    for i, prompt in enumerate(prompts, start=1):
        target_path = os.path.join(output_dir, f"scene_{i}.jpg")
        print(f"\n🎬 Sahne {i} hazırlanıyor...")
        
        # 1. Deneme: Imagen 3 (002)
        success = generate_with_gemini_imagen(prompt, target_path)
        
        # 2. Deneme: Pollinations AI (Kesin sonuç verir)
        if not success:
            success = generate_with_pollinations(prompt, target_path)
            
        # 3. Deneme: Pexels API
        if not success:
            success = generate_with_pexels(f"{mekan} dark night", target_path)

        if not success:
            print(f"❌ Sahne {i} oluşturulamadı!")
            sys.exit(1)
            
        time.sleep(2)

    print("\n✅ Tüm sahne görselleri başarıyla hazırlandı.")

if __name__ == "__main__":
    main()
