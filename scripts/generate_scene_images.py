import sys
import json
import os
import requests
from PIL import Image

def search_pexels(query, api_key, per_page=5):
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": api_key}
    # Shorts için dikey görseller (portrait) istiyoruz
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
        # Görsel daha geniş, yanlardan kırp
        new_width = int(target_ratio * img.height)
        offset = (img.width - new_width) / 2
        crop_box = (offset, 0, img.width - offset, img.height)
    else:
        # Görsel daha uzun, alt/üstten kırp
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
    baslik_txt = sys.argv[2] # Okunuyor ama görselde metin istenmediği için kullanılmıyor
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

    # Senaryoyu kelimelere böl ve tam 3 eşit parçaya ayır
    words = script.split()
    chunk_size = len(words) // 3
    if chunk_size == 0:
        chunk_size = 1 # Çok kısa metinler için güvenlik önlemi
        
    chunks = [
        words[:chunk_size],
        words[chunk_size:2*chunk_size],
        words[2*chunk_size:]
    ]

    # Tema anahtar kelimeleri (aramayı yönlendirmek için)
    # Pexels İngilizce aramada daha iyi sonuç verir, ancak tema metinleri Türkçe geliyor.
    # Yine de en iyi sonucu almak için genel temayı ve mekan bilgisini kullanıyoruz.
    base_keywords = f"{tema.get('tema', 'korku')} {tema.get('mekan', 'gece')}"

    for i in range(3):
        # Her parça için temanın yanına o parçanın ilk 2 kelimesini ekleyerek arama sorgusu oluştur
        chunk_words = " ".join(chunks[i][:2])
        query = f"{base_keywords} {chunk_words}"
        
        print(f"Sahne {i+1} için görsel aranıyor: {query}")
        images = search_pexels(query, pexels_api_key, per_page=3)
        
        # Eğer özel sorgu sonuç vermezse, sadece temel anahtar kelimelerle tekrar dene
        if not images:
            print("Özel sorgu sonuç vermedi, temel sorgu deneniyor...")
            images = search_pexels(base_keywords, pexels_api_key, per_page=5)
            
        # Hiçbir şey bulunamazsa fallback olarak "dark horror" ara
        if not images:
            images = search_pexels("dark horror night", pexels_api_key, per_page=5)

        if not images:
            print(f"Sahne {i+1} için hiçbir görsel bulunamadı, atlanıyor.")
            continue

        # İlk bulduğumuz görseli indir
        # Aynı görselin tekrar etmemesi için i indeksini kullanarak listeden farklı görseller alabiliriz
        img_url = images[i % len(images)] 
        
        resp = requests.get(img_url)
        img_path = os.path.join(output_dir, f"scene_{i+1}.jpg")
        with open(img_path, "wb") as f:
            f.write(resp.content)

        # Görseli kırp ve boyutlandır (Metin ÇİZİMİ TAMAMEN KALDIRILDI)
        img = Image.open(img_path).convert("RGB")
        img = crop_to_fill(img, 1080, 1920)
        img.save(img_path)
        print(f"Sahne {i+1} temiz bir şekilde kaydedildi: {img_path}")

if __name__ == "__main__":
    main()
