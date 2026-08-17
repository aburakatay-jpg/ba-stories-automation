import sys
import asyncio
import edge_tts
import json
import os

async def generate_audio(text, output_file, voice):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

async def main_async(text, output_file, anlatici="erkek"):
    # Senaryodaki anlatıcıya göre öncelikli sesi belirle
    if anlatici == "kadin":
        voices = ["tr-TR-EmelNeural", "tr-TR-SinanNeural"]
    else:
        voices = ["tr-TR-SinanNeural", "tr-TR-EmelNeural"]
        
    for voice in voices:
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
    
    # tema.json dosyasından anlatıcı bilgisini çek
    anlatici = "erkek" # Herhangi bir hataya karşı varsayılan değer
    tema_path = "output/tema.json"
    if os.path.exists(tema_path):
        with open(tema_path, "r", encoding="utf-8") as f:
            try:
                tema_data = json.load(f)
                anlatici = tema_data.get("anlatici", "erkek")
                print(f"Okunan anlatıcı profili: {anlatici}")
            except json.JSONDecodeError:
                print("tema.json okunamadı, varsayılan erkek sesi kullanılacak.")
    
    with open(input_txt, 'r', encoding='utf-8') as f:
        text = f.read().strip()
        
    if not text:
        print("Metin boş, ses oluşturulamadı.")
        sys.exit(1)
        
    asyncio.run(main_async(text, output_mp3, anlatici))

if __name__ == "__main__":
    main()
