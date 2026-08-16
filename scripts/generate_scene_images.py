import sys
import json
import os
import base64
import requests
import textwrap

def generate_image(prompt, api_key):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=" + api_key
    payload = {
        "contents": [
            {"parts": [{"text": f"Görsel oluştur: {prompt}. Korku atmosferi, gerilim, karanlık, fotoğraf gerçekçi."}]}
        ],
        "generationConfig": {
            "responseModalities": ["IMAGE"]
        }
    }
    resp = requests.post(url, json=payload, timeout=60)
    if not resp.ok:
        print(f"Hata {resp.status_code}: {resp.text}")
        raise Exception("Görsel üretilemedi")
    data = resp.json()
    # inlineData içinde base64 resim var
    try:
        image_data = data["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
    except (KeyError, IndexError):
        print("Yanıt beklenen formatta değil:", json.dumps(data, indent=2))
        raise
    return base64.b64decode(image_data)

def main():
    if len(sys.argv) < 5:
        print("Kullanım: generate_scene_images.py <tema_json> <baslik_txt> <senaryo_txt> <cikti_klasoru>")
        sys.exit(1)
    tema_json = sys.argv[1]
    baslik_txt = sys.argv[2]
    senaryo_txt = sys.argv[3]
    output_dir = sys.argv[4]

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY ortam değişkeni tanımlı değil!")

    with open(tema_json, 'r', encoding='utf-8') as f:
        tema = json.load(f)
    with open(baslik_txt, 'r', encoding='utf-8') as f:
        baslik = f.read().strip()
    with open(senaryo_txt, 'r', encoding='utf-8') as f:
        script = f.read().strip()

    # Senaryoyu cümlelere böl, çok uzun olanları birleştir
    raw_sentences = [s.strip() for s in script.replace("\n", " ").split(".") if len(s.strip()) > 10]
    # En fazla 5 sahne, her biri 2-3 cümle
    scenes = []
    for i in range(0, min(len(raw_sentences), 10), 2):
        chunk = ". ".join(raw_sentences[i:i+2])
        if chunk:
            scenes.append(chunk)
        if len(scenes) >= 5:
            break

    if not scenes:
        print("Yeterli cümle bulunamadı, senaryoyu parçalayalım...")
        # Yedek: kelime sayısına göre böl
        words = script.split()
        chunk_size = len(words) // 5
        for i in range(5):
            chunk = " ".join(words[i*chunk_size:(i+1)*chunk_size])
            if chunk:
                scenes.append(chunk)

    os.makedirs(output_dir, exist_ok=True)

    for idx, scene_text in enumerate(scenes):
        prompt = f"{tema['tema']}, {tema['mekan']}, korku, gerilim, gece, tek başına, karanlık, fotoğraf gerçekçi: {scene_text[:150]}"
        print(f"🎨 Sahne {idx+1} görseli üretiliyor...")
        try:
            img_bytes = generate_image(prompt, api_key)
            out_path = os.path.join(output_dir, f"scene_{idx+1:02d}.jpg")
            with open(out_path, "wb") as f:
                f.write(img_bytes)
            print(f"✅ Kaydedildi: {out_path}")
        except Exception as e:
            print(f"❌ Sahne {idx+1} başarısız: {e}")

if __name__ == "__main__":
    main()
