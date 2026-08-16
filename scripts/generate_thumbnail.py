# scripts/create_thumbnail.py
from PIL import Image, ImageDraw, ImageFont
import textwrap

def create_thumbnail(text, output_path="output/thumbnail.jpg"):
    # Siyah arkaplan
    img = Image.new('RGB', (1080, 1920), color='black')
    draw = ImageDraw.Draw(img)
    
    # Font (Actions ortamında varsayılan bir font kullan, ya da indir)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
    except:
        font = ImageFont.load_default()
    
    # Metni sar ve ortala
    wrapped = textwrap.fill(text, width=20)
    w, h = draw.textsize(wrapped, font=font)
    draw.text(((1080-w)//2, (1920-h)//2), wrapped, fill='white', font=font)
    
    img.save(output_path)
    print(f"Thumbnail oluşturuldu: {output_path}")
