#!/usr/bin/env python3
import os
import sys
import json
import time
import urllib.parse
import subprocess
import requests

def download_image(url, save_path, headers=None):
    try:
        h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        if headers:
            h.update(headers)
        resp = requests.get(url, timeout=30, headers=h)
        if resp.ok and len(resp.content) > 5000:
            with open(save_path, "wb") as f:
                f.write(resp.content)
            return True
    except Exception as e:
        print(f"İndirme hatası: {e}")
    return False

def generate_with_pexels(query, save_path, page=1):
    pexels_key = os.environ.get("PEXELS_API_KEY")
    if not pexels_key:
        return False
        
    print(f"🔍 Pexels ile görsel aranıyor: '{query}'")
    encoded_query = urllib.parse.quote(query)
    url = f"https://api.pexels.com/v1/search?query={encoded_query}&orientation=portrait&per_page=10&page={page}"
    headers = {"Authorization": pexels_key}
    
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.ok:
            data = resp.json()
            photos = data.get("photos", [])
            if photos:
                # İlgili sayfadan görsel al
                img_url = photos[min(page - 1, len(photos) - 1)]["src"]["large2x"]
                if download_image(img_url, save_path):
                    print(f"✅ Pexels görseli kaydedildi: {save_path}")
                    return True
    except Exception as e:
        print(f"Pexels API hatası: {e}")
    return False

def generate_with_pollinations(prompt, save_path):
    print("🔄 Pollinations AI ile üretiliyor...")
    # URL'yi sadeleştirilmiş kısa prompt ile çağırıyoruz
    short_prompt = prompt[:180]
    encoded = urllib.parse.quote(short_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&nologo=true"
    if download_image(url, save_path):
        print(f"✅ Pollinations görseli kaydedildi: {save_path}")
        return True
    return False

def create_fallback_image(save_path, text=""):
    """İnternet veya API kesilirse pipeline'ın durmaması için siyah/sisli atmosfer karesi üretir."""
    print("⚠️ Güvenlik görseli (Fallback) oluşturuluyor...")
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=0x0a0a0f:s=1080x1920:d=1",
        "-frames:v", "1",
        save_path
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"✅ Güvenlik görseli oluşturuldu: {save_path}")
        return True
    except Exception as e:
        print(f"Fallback hatası: {e}")
    return False

def main():
    if len(sys.argv) < 5:
        print("Kullanım: generate_scene_images.py <tema.json> <baslik.txt> <senaryo.txt> <output_dir>")
        sys.exit(1)

    output_dir = sys.argv[4]
    os.makedirs(output_dir, exist_ok=True)

    # Arama terimleri (Pexels için en verimli korku anahtar kelimeleri)
    search_queries = [
        "dark forest foggy night horror",
        "abandoned building dark creepy",
        "creepy mystery silhouette dark night"
    ]

    for i in range(1, 4):
        target_path = os.path.join(output_dir, f"scene_{i}.jpg")
        print(f"\n🎬 Sahne {i} hazırlanıyor...")
        
        # 1. Tercih: Pexels (Hızlı, temiz, dikey ve hatasız)
        query = search_queries[i - 1]
        success = generate_with_pexels(query, target_path, page=i)
        
        # 2. Tercih: Pollinations AI
        if not success:
            poll_prompt = f"dark cinematic horror scene, {query}, misty, eerie shadows, 9:16 vertical photorealistic"
            success = generate_with_pollinations(poll_prompt, target_path)

        # 3. Tercih: FFmpeg yerel karanlık arka plan (Pipeline ASLA durmaz)
        if not success:
            success = create_fallback_image(target_path)

        time.sleep(1)

    print("\n✅ Tüm 3 sahne görseli hazırlandı.")

if __name__ == "__main__":
    main()
