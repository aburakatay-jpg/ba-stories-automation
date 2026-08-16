import sys
import json
import os
import requests
from PIL import Image, ImageDraw, ImageFont
import textwrap

def search_pexels(query, api_key, per_page=5):
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": api_key}
    params = {"query": query, "per_page": per_page, "orientation": "portrait"}
    resp = requests.get(url, headers=headers, params=params)
    if not resp.ok:
        raise Exception(f"Pexels hatası: {resp.text}")
    data = resp.json()
    return [photo["src"]["original"] for photo in data.get("photos", [])]

def main():
    if len(sys.argv) < 5:
        print("Kullanım: generate_scene_images.py <tema_json> <baslik_txt> <senaryo_txt> <cikti_klasoru>")
        sys.exit(1)
    tema_json = sys.argv[1]
    baslik_txt = sys.argv[2]
    senaryo_txt = sys.argv[3]
    output_dir = sys.argv[4]
    os.makedirs(output_dir, exist_ok=True)

    pexels_api_key = os.environ.get("PEXELS_API_KEY")
    if not pexels_api_key:
        print("PEXELS_API_KEY ortam değişkeni tanımlı değil!")
        sys.exit(1)

    with open(tema_json, "r", encoding="utf-8") as f:
        tema = json.load(f)
    with open(senaryo_txt, "r", encoding="utf-8") as f:
        script = f.read()
    with open(baslik_txt, "r", encoding="utf-8") as f:
        baslik = f.read().strip()

    # Senaryoyu sahnelere böl (basitçe nokta)
    sentences = [s.strip() for s in script.split(".") if len(s.strip()) > 10]
    scenes = sentences[:5]  # en fazla 5 sahne

    # Tema anahtar kelimeleri
    keywords = [tema["tema"], tema["mekan"], "korku", "gece", "gerilim"]

    for i, scene in enumerate(scenes):
        query = " ".join(keywords[:3]) + " " + " ".join(scene.split()[:5])
        print(f"Sahne {i+1} için görsel aranıyor: {query}")
        images = search_pexels(query, pexels_api_key, per_page=3)
        if not images:
            print(f"Görsel bulunamadı, atlanıyor: {i+1}")
            continue
        img_url = images[0]
        # Görseli indir
        resp = requests.get(img_url)
        img_path = os.path.join(output_dir, f"scene_{i+1}.jpg")
        with open(img_path, "wb") as f:
            f.write(resp.content)

        # Görsel üzerine metin ekle (isteğe bağlı)
        img = Image.open(img_path).convert("RGB")
        img = img.resize((1080, 1920), Image.Resampling.LANCZOS)
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        except:
            font = ImageFont.load_default()
        # Metin kutusu (yarı saydam siyah)
        wrapped = textwrap.fill(scene, width=25)
        bbox = draw.textbbox((0,0), wrapped, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        box_x1 = (1080 - w)//2 - 40
        box_y1 = (1920 - h)//2 - 40
        box_x2 = (1080 + w)//2 + 40
        box_y2 = (1920 + h)//2 + 40
        draw.rectangle([box_x1, box_y1, box_x2, box_y2], fill=(0,0,0,180))
        draw.text(((1080-w)//2, (1920-h)//2), wrapped, fill='white', font=font)
        img.save(img_path)
        print(f"Sahne {i+1} kaydedildi: {img_path}")

if __name__ == "__main__":
    main()
