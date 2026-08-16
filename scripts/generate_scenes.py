#!/usr/bin/env python3
"""
Senaryoyu sahnelere böler, her sahne için arkaplan + metin içeren bir görsel oluşturur.
Kullanım: python generate_scenes.py
"""
import os
import json
import random
import textwrap
from PIL import Image, ImageDraw, ImageFont

os.makedirs("output", exist_ok=True)

def split_into_scenes(text, max_words=25):
    """Metni cümlelere böler, her cümle bir sahne."""
    sentences = text.replace('\n', ' ').split('. ')
    scenes = []
    for s in sentences:
        s = s.strip()
        if s:
            # Cümlenin sonuna nokta ekle (eğer yoksa)
            if not s.endswith('.'):
                s += '.'
            scenes.append(s)
    # Eğer çok az sahne varsa, her 25 kelimede bir bölelim
    if len(scenes) < 3:
        words = text.split()
        scenes = []
        for i in range(0, len(words), max_words):
            chunk = ' '.join(words[i:i+max_words])
            if chunk:
                scenes.append(chunk + '.')
    return scenes

def pick_background(theme, bg_dir="backgrounds"):
    """Temaya uygun arkaplan resmi seç (alt klasör veya rastgele)."""
    # Basitçe backgrounds klasöründen rastgele bir resim seç
    if not os.path.exists(bg_dir):
        return None
    files = [f for f in os.listdir(bg_dir) if f.lower().endswith(('.jpg','.png','.jpeg'))]
    if not files:
        return None
    return os.path.join(bg_dir, random.choice(files))

def create_scene_image(text, output_path, bg_path=None):
    """Bir sahne görseli oluştur."""
    # Arkaplan
    if bg_path and os.path.exists(bg_path):
        img = Image.open(bg_path).convert('RGB')
        img = img.resize((1080, 1920), Image.Resampling.LANCZOS)
    else:
        img = Image.new('RGB', (1080, 1920), color='#1a1a2e')
    
    draw = ImageDraw.Draw(img)
    
    # Font
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
    except:
        font = ImageFont.load_default()
    
    # Metni sar ve ortala
    wrapped = textwrap.fill(text, width=25)
    bbox = draw.textbbox((0,0), wrapped, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    
    # Yarı saydam siyah kutu
    box_x1 = (1080 - w)//2 - 40
    box_y1 = (1920 - h)//2 - 40
    box_x2 = (1080 + w)//2 + 40
    box_y2 = (1920 + h)//2 + 40
    draw.rectangle([box_x1, box_y1, box_x2, box_y2], fill=(0,0,0,180))
    draw.text(((1080-w)//2, (1920-h)//2), wrapped, fill='white', font=font)
    
    img.save(output_path)
    print(f"✅ Sahne görseli oluşturuldu: {output_path}")

def main():
    # Senaryoyu oku
    with open("output/senaryo.txt", "r", encoding="utf-8") as f:
        script = f.read().strip()
    if not script:
        print("❌ Senaryo boş!")
        return
    
    # Temayı oku (arkaplan seçimi için)
    theme = {}
    if os.path.exists("output/tema.json"):
        with open("output/tema.json", "r", encoding="utf-8") as f:
            theme = json.load(f)
    
    scenes = split_into_scenes(script)
    print(f"📝 {len(scenes)} sahne oluşturuldu.")
    
    # Her sahne için görsel üret
    for i, scene_text in enumerate(scenes, start=1):
        bg = pick_background(theme.get("tema", ""))
        out_path = f"output/scene_{i:03d}.jpg"
        create_scene_image(scene_text, out_path, bg)
    
    # Sahne sayısını bir dosyaya yaz (montaj scripti kullanacak)
    with open("output/scene_count.txt", "w") as f:
        f.write(str(len(scenes)))

if __name__ == "__main__":
    main()
