import sys
import json
from PIL import Image, ImageDraw, ImageFont
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

    # Siyah arkaplan
    img = Image.new('RGB', (1080, 1920), color='black')
    draw = ImageDraw.Draw(img)

    # Font (Actions ortamında varsayılan fontu dene)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
    except:
        font = ImageFont.load_default()

    # Metni sar ve ortala
    wrapped = textwrap.fill(text, width=20)
    bbox = draw.textbbox((0,0), wrapped, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.text(((1080-w)//2, (1920-h)//2), wrapped, fill='white', font=font)

    img.save(output_jpg)
    print(f"Thumbnail oluşturuldu: {output_jpg}")

if __name__ == "__main__":
    main()
