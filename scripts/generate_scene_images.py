import sys
import json
import os
import random
import requests
from PIL import Image

def search_pexels(query, api_key, per_page=15):
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": api_key}
    params = {"query": query, "per_page": per_page, "orientation": "portrait"}
    resp = requests.get(url, headers=headers, params=params)
    if not resp.ok:
        print(f"Pexels hatası: {resp.text}")
        return []
    data = resp.json()
    return [photo["src"]["original"] for photo in data.get("photos", [])]

def crop_to_fill(img, target_width, target_height):
    """Görseli sündürmeden (aspect ratio bozmadan) hedef boyuta göre merkezden kırpar."""
    img_ratio = img.width / img.height
    target_ratio = target_width / target_height

    if img_ratio > target_ratio:
        new_width = int(target_ratio * img.height)
        offset = (img.width - new_width) / 2
        crop_box = (offset, 0, img.width - offset, img.height)
    else:
        new_height = int(img.width / target_ratio)
        offset = (img.height - new_height) / 2
        crop_box = (0, offset, img.width, img.height - offset)
    
    img = img.crop(crop_box)
    return img.resize((target_width, target_height), Image.Resampling.LANCZOS)

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

    # KORKU KANALI İÇİN ÖZEL PEXELS ARAMA ŞABLONLARI
    # Tamamen karanlık, gerilimli ve atmosferik İngilizce kelimeler
    creepy_templates = [
        "dark creepy room",
        "scary shadows night",
        "abandoned spooky house",
        "dark empty corridor",
        "creepy window night",
        "dark misty forest",
        "spooky fog night",
        "dark eerie street",
        "creepy cinematic lighting",
        "horror background dark",
        "mysterious dark silhouette"
    ]

    # Şablonlardan rastgele ve birbirinden GÜVENLİ ŞEKİLDE FARKLI 3 tanesini seç
    selected_queries = random.sample(creepy_templates, 3)

    for i in range(3):
        query = selected_queries[i]
        print(f"Sahne {i+1} için aranıyor: {query}")
        
        images = search_pexels(query, pexels_api_key)
        
        if not images:
            print("Özel sorgu sonuç vermedi, varsayılan karanlık tema deneniyor...")
            images = search_pexels("pitch black dark night", pexels_api_key)
            
        if not images:
            print(f"Sahne {i+1} için hiçbir görsel bulunamadı, atlanıyor.")
            continue

        # Gelen 15 sonuç arasından rastgele birini seç ki çeşitlilik artsın
        img_url = random.choice(images[:10])
        
        resp = requests.get(img_url)
        img_path = os.path.join(output_dir, f"scene_{i+1}.jpg")
        with open(img_path, "wb") as f:
            f.write(resp.content)

        # Görseli kırp ve boyutlandır
        img = Image.open(img_path).convert("RGB")
        img = crop_to_fill(img, 1080, 1920)
        img.save(img_path)
        print(f"Sahne {i+1} temiz bir şekilde kaydedildi: {img_path}")

if __name__ == "__main__":
    main()
