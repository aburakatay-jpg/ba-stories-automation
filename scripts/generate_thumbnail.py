#!/usr/bin/env python3
import sys
import json
import os
import random
import requests
import base64

def generate_thumbnail_ai(tema_konusu, tema_mekani, api_key):
    # Kapak fotoğrafı için özel olarak tasarlanmış yüksek CTR getirecek prompt
    # Merak uyandıran, yüksek kontrastlı ve odak noktası belli bir komut kullanıyoruz.
    prompt = (
        f"Concept: {tema_konusu} at {tema_mekani}. "
        "YouTube thumbnail, highly detailed, extreme contrast, mysterious, terrifying, "
        "cinematic lighting, dark spooky atmosphere, focal point on a creeping silhouette or creepy object, "
        "vivid colors in shadows, photorealistic, no text, 16:9 aspect ratio."
    )
    print(f"Thumbnail Komutu: {prompt}")

    # --- YÖNTEM 1: GEMINI IMAGEN 3 API ---
    if api_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:predict?key={api_key}"
            payload = {
                "instances": [{"prompt": prompt}],
                "parameters": {
                    "sampleCount": 1,
                    "aspectRatio": "16:9",
                    "outputOptions": {"mimeType": "image/jpeg"}
                }
            }
            resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
            if resp.ok:
                b64 = resp.json()["predictions"][0]["bytesBase64Encoded"]
                print("✅ Gemini Imagen 3 ile kapak fotoğrafı üretildi.")
                return base64.b64decode(b64)
            else:
                print(f"⚠️ Gemini API hatası: {resp.text}")
        except Exception as e:
             print(f"⚠️ API İletişim Hatası: {e}")

    # --- YÖNTEM 2: ÜCRETSİZ YEDEK YAPAY ZEKA (Pollinations AI) ---
    print("🔄 Yedek AI'a geçiliyor...")
    safe_prompt = requests.utils.quote(prompt)
    seed_value = random.randint(1, 9999999) 
    fallback_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1920&height=1080&nologo=true&seed={seed_value}"
    
    resp = requests.get(fallback_url)
    if resp.ok:
        print("✅ Yedek AI ile kapak fotoğrafı üretildi.")
        return resp.content
    return None

def main():
    if len(sys.argv) < 4:
        print("Kullanım: generate_thumbnail.py <tema_json> <baslik_txt> <çıktı_jpg>")
        sys.exit(1)

    tema_json = sys.argv[1]
    baslik_txt = sys.argv[2] # Workflow kırılmasın diye okuyoruz ama görselde metin kullanmıyoruz
    output_jpg = sys.argv[3]

    gemini_api_key = os.environ.get("GEMINI_API_KEY", "")

    with open(tema_json, "r", encoding="utf-8") as f:
        tema = json.load(f)
    
    tema_konusu = tema.get("tema", "korkunç bir olay")
    tema_mekani = tema.get("mekan", "karanlık mekan")

    image_bytes = generate_thumbnail_ai(tema_konusu, tema_mekani, gemini_api_key)
    
    if image_bytes:
        with open(output_jpg, "wb") as f:
            f.write(image_bytes)
        print(f"Kapak fotoğrafı (Thumbnail) başarıyla kaydedildi: {output_jpg}")
    else:
        print("❌ Kapak fotoğrafı üretilemedi!")
        sys.exit(1)

if __name__ == "__main__":
    main()
