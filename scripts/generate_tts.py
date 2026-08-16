import sys
import asyncio
import edge_tts

async def generate_audio(text, output_file):
    # Türkçe doğal ses (Sinan - erkek)
    voice = "tr-TR-SinanNeural"
    # İstersen "tr-TR-EmelNeural" (kadın) da kullanabilirsin
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

def main():
    if len(sys.argv) < 3:
        print("Kullanım: python generate_tts.py <metin_dosyası> <çıktı_mp3>")
        sys.exit(1)
    input_txt = sys.argv[1]
    output_mp3 = sys.argv[2]
    with open(input_txt, 'r', encoding='utf-8') as f:
        text = f.read().strip()
    if not text:
        print("Metin boş, ses oluşturulamadı.")
        sys.exit(1)
    # Asenkron çalıştır
    asyncio.run(generate_audio(text, output_mp3))
    print(f"Ses oluşturuldu: {output_mp3}")

if __name__ == "__main__":
    main()
