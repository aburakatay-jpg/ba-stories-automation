import sys
import asyncio
import edge_tts

async def generate_audio(text, output_file, voice):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

async def main_async(text, output_file):
    # Önce Sinan dene, olmazsa Emel
    for voice in ["tr-TR-SinanNeural", "tr-TR-EmelNeural"]:
        try:
            print(f"🗣️ Ses deneniyor: {voice}")
            await generate_audio(text, output_file, voice)
            print(f"✅ Ses kaydedildi: {output_file} (ses: {voice})")
            return
        except Exception as e:
            print(f"⚠️ {voice} ile ses oluşturulamadı: {e}")
    raise RuntimeError("Hiçbir ses çalışmadı.")

def main():
    if len(sys.argv) < 3:
        print("Kullanım: generate_tts.py <metin_dosyası> <çıktı_mp3>")
        sys.exit(1)
    input_txt = sys.argv[1]
    output_mp3 = sys.argv[2]
    with open(input_txt, 'r', encoding='utf-8') as f:
        text = f.read().strip()
    if not text:
        print("Metin boş, ses oluşturulamadı.")
        sys.exit(1)
    asyncio.run(main_async(text, output_mp3))

if __name__ == "__main__":
    main()
