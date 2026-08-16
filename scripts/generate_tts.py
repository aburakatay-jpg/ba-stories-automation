import sys
import asyncio
import json
import edge_tts

async def generate_audio(text, output_file, voice="tr-TR-SinanNeural"):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

def main():
    if len(sys.argv) < 4:
        print("Kullanım: generate_tts.py <senaryo_txt> <tema_json> <cikti_mp3>")
        sys.exit(1)
    script_file = sys.argv[1]
    theme_file = sys.argv[2]
    output_file = sys.argv[3]

    with open(script_file, 'r', encoding='utf-8') as f:
        text = f.read().strip()
    with open(theme_file, 'r', encoding='utf-8') as f:
        theme = json.load(f)
        anlatici = theme.get('anlatici', 'erkek')

    # Edge TTS ses seçimi
    if anlatici == 'kadin':
        voice = "tr-TR-EmelNeural"
    else:
        voice = "tr-TR-SinanNeural"

    asyncio.run(generate_audio(text, output_file, voice))
    print(f"Ses oluşturuldu: {output_file} ({anlatici})")

if __name__ == "__main__":
    main()
