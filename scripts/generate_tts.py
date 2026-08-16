import sys
import asyncio
import edge_tts

async def generate_audio(text, output_file, voice="tr-TR-SinanNeural"):
    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_file)
        print(f"✅ Ses kaydedildi: {output_file}")
    except Exception as e:
        print(f"❌ Ses oluşturulamadı: {e}")
        # Alternatif ses dene
        print("🔄 Alternatif ses deneniyor (Emel)...")
        try:
            communicate = edge_tts.Communicate(text, "tr-TR-EmelNeural")
            await communicate.save(output_file)
            print(f"✅ Ses kaydedildi (Emel): {output_file}")
        except Exception as e2:
            print(f"❌ Alternatif ses de başarısız: {e2}")
            raise

def main():
    if len(sys.argv) < 3:
        print("Kullanım: python generate_tts.py <metin_dosyası> <çıktı_mp3>")
        sys.exit(1)
    input_txt = sys.argv[1]
    output_mp3 = sys.argv[2]

    with open(input_txt, 'r', encoding='utf-8') as f:
        text = f.read().strip()
    if not text:
        print("❌ Metin boş, ses oluşturulamadı.")
        sys.exit(1)

    # Metni kısalt (Edge TTS 1000 karakter sınırı var mı bilmiyorum ama güvenli ol)
    if len(text) > 1500:
        text = text[:1500]
        print("⚠️ Metin 1500 karaktere kısaltıldı.")

    # Ses tercihi: tema.json'daki 'anlatici' alanına göre seçim yapabiliriz, ama şimdilik sabit
    voice = "tr-TR-SinanNeural"  # veya "tr-TR-EmelNeural"
    print(f"🗣️ Ses: {voice}")
    asyncio.run(generate_audio(text, output_mp3, voice))

if __name__ == "__main__":
    main()
