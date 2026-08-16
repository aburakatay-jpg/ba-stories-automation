import sys
import json
import os
import random
import requests
import base64

def generate_image_ai(prompt, api_key):
    enhanced_prompt = f"{prompt}. Dark spooky atmosphere, cinematic horror movie lighting, highly detailed, photorealistic, no text, empty background, 9:16 aspect ratio."
    print(f"Yapay zeka komutu: {enhanced_prompt}")

    # --- YÖNTEM 1: GEMINI IMAGEN 3 API ---
    if api_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:predict?key={api_key}"
            payload = {
                "instances": [{"prompt": enhanced_prompt}],
                "parameters": {
                    "sampleCount": 1,
                    "aspectRatio": "9:16",
                    "outputOptions": {"mimeType": "image/jpeg"}
                }
            }
            resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
            if resp.ok:
                data = resp.json()
                b64 = data["predictions"][0]["bytesBase64Encoded"]
                print("✅ Gemini Imagen 3 ile görsel başarıyla üretildi.")
                return base64.b64decode(b64)
            else:
                print(f"⚠️ Gemini API görseli reddetti. Hata: {resp.text}")
        except Exception as e:
             print(f"⚠️ Gemini API hatası: {e}.")

    # --- YÖNTEM 2: ÜCRETSİZ YEDEK YAPAY ZEKA (Pollinations AI) ---
    print("🔄 Yedek AI görsel aracına başvuruluyor...")
    safe_prompt = requests.utils.quote(enhanced_prompt)
    
    # SEED EKLENDİ: Her API çağrısında farklı görsel üretilmesi garanti altına alındı
    seed_value = random.randint(1, 9999999) 
    fallback_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1080&height=1920&nologo=true&seed={seed_value}"
    
    resp = requests.get(fallback_url)
    if resp.ok:
        print("✅ Yedek AI ile görsel üretildi.")
        return resp.content
    else:
        print("❌ Hiçbir yöntemle görsel üretilemedi!")
        return None

def main():
    if len(sys.argv) < 5:
        print("Kullanım: generate_scene_images.py <tema_json> <baslik_txt> <senaryo_txt> <cikti_klasoru>")
        sys.exit(1)
        
    tema_json = sys.argv[1]
    baslik_txt = sys.argv[2]
    senaryo_txt = sys.argv[3]
    output_dir = sys.argv[4]
    os.makedirs(output_dir, exist_ok=True)

    gemini_api_key = os.environ.get("GEMINI_API_KEY", "")

    with open(tema_json, "r", encoding="utf-8") as f:
        tema = json.load(f)
    
    tema_konusu = tema.get("tema", "korku")
    tema_mekani = tema.get("mekan", "karanlık mekan")

    kamera_acilari = [
        "Wide angle shot, mysterious shadow lurking in the distance",
        "Close up macro shot, eerie details, feeling of being watched",
        "Low angle shot, towering creepy environment, thick fog"
    ]

    for i in range(3):
        sahne_promptu = f"Concept: {tema_konusu} at {tema_mekani}. {kamera_acilari[i]}"
        
        image_bytes = generate_image_ai(sahne_promptu, gemini_api_key)
        
        if image_bytes:
            img_path = os.path.join(output_dir, f"scene_{i+1}.jpg")
            with open(img_path, "wb") as f:
                f.write(image_bytes)
            print(f"Sahne {i+1} klasöre kaydedildi: {img_path}")
        else:
            print(f"Sahne {i+1} atlandı!")

if __name__ == "__main__":
    main()
