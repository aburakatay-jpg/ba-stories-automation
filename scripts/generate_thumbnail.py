import sys
import json
import os
from PIL import Image, ImageDraw, ImageFont
import textwrap

def create_thumbnail(text, output_path, bg_color=(0,0,0)):
    img = Image.new('RGB', (1080, 1920), color=bg_color)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
    except:
        font = ImageFont.load_default()
    wrapped = textwrap.fill(text, width=20)
    bbox = draw.textbbox((0,0), wrapped, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.text(((1080-w)//2, (1920-h)//2), wrapped, fill='white', font=font)
    img.save(output_path)
    print(f"Thumbnail oluşturuldu: {output_path}")

def main():
    if len(sys.argv) < 4:
        print("Kullanım: generate_thumbnail.py <tema_json> <baslik_txt> <çıktı_prefix> [adet]")
        sys.exit(1)
    tema_json = sys.argv[1]
    baslik_txt = sys.argv[2]
    output_prefix = sys.argv[3]  # örn: "output/thumbnail"
    count = int(sys.argv[4]) if len(sys.argv) > 4 else 1

    with open(baslik_txt, 'r', encoding='utf-8') as f:
        text = f.read().strip()
    if not text:
        print("Başlık boş")
        sys.exit(1)

    # Farklı renk tonları veya efektler için varyasyonlar
    colors = [(0,0,0), (10,5,20), (5,10,20), (20,5,5), (0,10,15)]
    for i in range(count):
        bg = colors[i % len(colors)]
        output_path = f"{output_prefix}_{i+1}.jpg"
        create_thumbnail(text, output_path, bg)

if __name__ == "__main__":
    main()
