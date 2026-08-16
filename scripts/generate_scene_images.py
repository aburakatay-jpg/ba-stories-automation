#!/usr/bin/env python3
import sys
import json
import os
import base64
import requests

def generate_image(prompt, api_key):
    url = "https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:predict?key=" + api_key
    payload = {
        "contents": [
            {"parts": [{"text": f"Üret: {prompt}"}]}
        ],
        "generationConfig": {
            "responseModalities": ["IMAGE"]
        }
    }
    resp = requests.post(url, json=payload, timeout=60)
    if not resp.ok:
        raise Exception(f"Görsel üretilemedi: {resp.text}")
    data = resp.json()
    # İlk görseli al
    image_data = data["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
    return base64.b64decode(image_data)

def main():
    if len(sys.argv) != 5:
        print("Kullanım: generate_scene_images.py <tema_json> <baslik_txt> <senaryo_txt> <cikti_klasoru>")
        sys.exit(1)
    tema_json = sys.argv[1]
    baslik_txt = sys.argv[2]
    senaryo_txt = sys.argv[3]
    output_dir = sys.argv[4]
    os.makedirs(output_dir, exist_ok=True)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY ortam değişkeni ayarlanmamış")

    with open(tema_json, "r", encoding="utf-8") as f:
        tema = json.load(f)
    with open(baslik_txt, "r", encoding="utf-8") as f:
        baslik = f.read().strip()
    with open(senaryo_txt, "r", encoding="utf-8") as f:
        script = f.read().strip()

    # Senaryoyu cümlelere böl (nokta, ünlem, soru işareti)
    import re
    sentences = re.split(r'(?<=[.!?])\s+', script)
    # Boşları temizle ve en fazla 5 sahne al
    scenes = [s.strip() for s in sentences if len(s.strip()) > 10][:5]
    if not scenes:
        # Eğer hiç cümle yoksa, baslığı kullan
        scenes = [baslik]

    for i, scene in enumerate(scenes):
        prompt = f"{tema['tema']}, {tema['mekan']}, korku atmosferi, gece, gerilim, fotoğraf gerçekçi: {scene}"
        print(f"Sahne {i+1}/{len(scenes)} görseli üretiliyor...")
        image_bytes = generate_image(prompt, api_key)
        out_path = os.path.join(output_dir, f"scene_{i+1}.jpg")
        with open(out_path, "wb") as f:
            f.write(image_bytes)
        print(f"Kaydedildi: {out_path}")

if __name__ == "__main__":
    main()
