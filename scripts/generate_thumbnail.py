import sys
import json
import random
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap

def main():
    if len(sys.argv) < 4:
        print("Kullanım: generate_thumbnail.py <tema_json> <baslik_txt> <çıktı_jpg>")
        sys.exit(1)

    tema_json = sys.argv[1]
    baslik_txt = sys.argv[2]
    output_jpg = sys.argv[3]

    # Başlık metnini oku
    with open(baslik_txt, 'r', encoding='utf-8') as f:
        text = f.read().strip()
    if not text:
        print("Başlık boş, thumbnail oluşturulamadı.")
        sys.exit(1)

    # Arkaplan resmi seç (backgrounds klasöründen rastgele)
    bg_dir = "backgrounds"
    if os.path.exists(bg_dir):
        bg_files = [f for f in os.listdir(bg_dir) if f.lower().endswith(('.jpg','.png','.jpeg'))]
        if bg_files:
            bg_path = os.path.join(bg_dir, random.choice(bg_files))
            img = Image.open(bg_path).convert('RGB')
            # Resmi 1080x1920 boyutuna kırp/ölçekle (cover)
            img = img.resize((1080, 1920), Image.Resampling.LANCZOS)
        else:
            img = Image.new('RGB', (1080, 1920), color='#1a1a2e')
    else:
        img = Image.new('RGB', (1080, 1920), color='#1a1a2e')

    draw = ImageDraw.Draw(img)

    # Font ayarları
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
    except:
        font = ImageFont.load_default()

    # Metni sar ve ortala
    wrapped = textwrap.fill(text, width=20)
    bbox = draw.textbbox((0,0), wrapped, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]

    # Yarı saydam arkaplan kutusu
    padding = 40
    box_x1 = (1080 - w)//2 - padding
    box_y1 = (1920 - h)//2 - padding
    box_x2 = (1080 + w)//2 + padding
    box_y2 = (1920 + h)//2 + padding
    draw.rectangle([box_x1, box_y1, box_x2, box_y2], fill=(0,0,0,180))
    draw.text(((1080-w)//2, (1920-h)//2), wrapped, fill='white', font=font)

    img.save(output_jpg)
    print(f"Thumbnail oluşturuldu: {output_jpg}")

if __name__ == "__main__":
    main()
