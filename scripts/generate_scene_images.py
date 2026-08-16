#!/usr/bin/env python3
import sys
import json
import os
import random
import textwrap
from PIL import Image, ImageDraw, ImageFont

def main():
    if len(sys.argv) != 4:
        print("Kullanım: generate_scene_images.py <tema_json> <baslik_txt> <senaryo_txt>")
        sys.exit(1)

    tema_json = sys.argv[1]
    baslik_txt = sys.argv[2]
    senaryo_txt = sys.argv[3]
    output_dir = "output/scenes"
    os.makedirs(output_dir, exist_ok=True)

    # Başlık ve tema bilgisi
    with open(baslik_txt, 'r', encoding='utf-8') as f:
        baslik = f.read().strip()
    with open(tema_json, 'r', encoding='utf-8') as f:
        tema = json.load(f)

    # Senaryoyu oku ve cümlelere ayır (nokta, soru, ünlem ile)
    with open(senaryo_txt, 'r', encoding='utf-8') as f:
        text = f.read().strip()
    # Basit sahne bölme: noktalı işaretlerden sonra böl, boşları temizle
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    # En fazla 6 sahne (Shorts için ideal)
    if len(sentences) > 6:
        # Her bir sahneye eşit sayıda cümle düşecek şekilde grupla
        chunk_size = len(sentences) // 6
        scenes = [' '.join(sentences[i:i+chunk_size]) for i in range(0, len(sentences), chunk_size)]
        scenes = scenes[:6]  # max 6
    else:
        scenes = sentences

    # Arkaplan görsellerini bul
    bg_dir = "backgrounds"
    bg_files = []
    if os.path.exists(bg_dir):
        bg_files = [f for f in os.listdir(bg_dir) if f.lower().endswith(('.jpg','.png','.jpeg'))]
    if not bg_files:
        print("Uyarı: backgrounds klasörü boş veya yok, varsayılan siyah arkaplan kullanılacak.")

    # Font
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
    except:
        font = ImageFont.load_default()

    # Her sahne için görsel oluştur
    for idx, scene_text in enumerate(scenes):
        # Arkaplan seç
        if bg_files:
            bg_path = os.path.join(bg_dir, random.choice(bg_files))
            img = Image.open(bg_path).convert('RGB')
            img = img.resize((1080, 1920), Image.Resampling.LANCZOS)
        else:
            img = Image.new('RGB', (1080, 1920), color='#1a1a2e')

        draw = ImageDraw.Draw(img)

        # Metni sar
        wrapped = textwrap.fill(scene_text, width=25)  # 25 karakter genişlik
        # Boyutlandırma
        bbox = draw.textbbox((0,0), wrapped, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]

        # Yarı saydam siyah zemin
        box_x1 = (1080 - w)//2 - 40
        box_y1 = (1920 - h)//2 - 40
        box_x2 = (1080 + w)//2 + 40
        box_y2 = (1920 + h)//2 + 40
        draw.rectangle([box_x1, box_y1, box_x2, box_y2], fill=(0,0,0,200))
        draw.text(((1080-w)//2, (1920-h)//2), wrapped, fill='white', font=font)

        # Kaydet
        out_path = os.path.join(output_dir, f"scene_{idx+1:02d}.jpg")
        img.save(out_path)
        print(f"Sahne {idx+1} görseli oluşturuldu: {out_path}")

    # Sahne sayısını JSON olarak kaydet (assemble_short_scenes.py kullanacak)
    with open(os.path.join(output_dir, "scene_count.json"), "w") as f:
        json.dump({"count": len(scenes)}, f)

    print(f"Toplam {len(scenes)} sahne görseli oluşturuldu.")

if __name__ == "__main__":
    main()
