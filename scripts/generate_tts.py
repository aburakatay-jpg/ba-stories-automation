#!/usr/bin/env python3
"""
Edge TTS ile ses oluşturur, anlatici cinsiyetine göre ses seçer.
Kullanım: python generate_tts.py <metin_dosyası> <çıktı_mp3>
"""
import sys
import os
import json
import asyncio
import edge_tts

async def generate_audio(text, output_file, voice="tr-TR-SinanNeural"):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

def main():
    if len(sys.argv) < 3:
        print("Kullanım: generate_tts.py <metin_dosyası> <çıktı_mp3>")
        sys.exit(1)
    input_txt = sys.argv[1]
    output_mp3 = sys.argv[2]
    
    with open(input_txt, 'r', encoding='utf-8') as f:
        text = f.read().strip()
    if not text:
        print("Metin boş!")
        sys.exit(1)
    
    # Anlatici bilgisini tema.json'dan oku
    voice = "tr-TR-SinanNeural"  # varsayılan erkek
    if os.path.exists("output/tema.json"):
        with open("output/tema.json", "r", encoding="utf-8") as f:
            theme = json.load(f)
        anlatici = theme.get("anlatici", "").lower()
        if anlatici == "kadin":
            voice = "tr-TR-EmelNeural"
        elif anlatici == "erkek":
            voice = "tr-TR-SinanNeural"
        else:
            voice = "tr-TR-SinanNeural"  # fallback
    
    print(f"🗣️ Ses: {voice}")
    asyncio.run(generate_audio(text, output_mp3, voice))
    print(f"✅ Ses oluşturuldu: {output_mp3}")

if __name__ == "__main__":
    main()
