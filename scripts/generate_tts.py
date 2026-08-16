import sys
import os
from gtts import gTTS

def main():
    if len(sys.argv) < 3:
        print("Kullanım: python generate_tts.py <metin_dosyası> <çıktı_mp3>")
        sys.exit(1)

    input_txt = sys.argv[1]
    output_mp3 = sys.argv[2]

    # Metni oku
    with open(input_txt, 'r', encoding='utf-8') as f:
        text = f.read().strip()

    if not text:
        print("Hata: Metin dosyası boş!")
        sys.exit(1)

    # Türkçe ses sentezi (gTTS)
    tts = gTTS(text=text, lang='tr', slow=False)
    tts.save(output_mp3)
    print(f"Ses başarıyla oluşturuldu: {output_mp3}")

if __name__ == "__main__":
    main()
