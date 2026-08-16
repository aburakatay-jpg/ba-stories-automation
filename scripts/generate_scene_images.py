import sys
import json
import os
import base64
import requests

def generate_image(prompt, api_key):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=" + api_key
    payload = {
        "contents": [
            {"parts": [{"text": f"Üret: {prompt}"}]}
        ],
        "generationConfig": {
            "responseModalities": ["IMAGE"]
        }
    }
    resp = requests.post(url, json=payload)
    if not resp.ok:
        raise Exception(f"Görsel üretilemedi: {resp.text}")
    data = resp.json()
    # İlk görseli al
    image_data = data["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
    return base64.b64decode(image_data)

def main():
    tema_json = sys.argv[1]
    senaryo_txt = sys.argv[2]
    output_dir = sys.argv[3]
    api_key = os.environ["GEMINI_API_KEY"]

    with open(tema_json, "r") as f:
        tema = json.load(f)
    with open(senaryo_txt, "r", encoding="utf-8") as f:
        script = f.read()

    # Senaryoyu 4-5 sahneye böl (basitçe nokta ile)
    sentences = [s.strip() for s in script.split(".") if len(s.strip()) > 10]
    scenes = sentences[:5]  # en fazla 5 sahne

    for i, scene in enumerate(scenes):
        prompt = f"{tema['tema']}, {tema['mekan']}, korku atmosferi, gece, gerilim, fotoğraf gerçekçi: {scene}"
        print(f"Sahne {i+1} görseli üretiliyor...")
        image_bytes = generate_image(prompt, api_key)
        out_path = os.path.join(output_dir, f"scene_{i+1}.jpg")
        with open(out_path, "wb") as f:
            f.write(image_bytes)
        print(f"Kaydedildi: {out_path}")

if __name__ == "__main__":
    main()
