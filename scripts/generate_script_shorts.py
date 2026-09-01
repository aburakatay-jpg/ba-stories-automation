#!/usr/bin/env python3
import json
import os
import random
import time
import requests

os.makedirs("output", exist_ok=True)
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent"

def call_gemini_json(prompt, max_retries=5):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY bulunamadı!")
        
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.8,
            "maxOutputTokens": 2048,
            "responseMimeType": "application/json"
        }
    }

    for attempt in range(max_retries):
        resp = requests.post(f"{API_URL}?key={api_key}", json=payload, timeout=120)
        if resp.status_code in [429, 503]:
            time.sleep(30)
            continue
        if not resp.ok:
            raise RuntimeError(f"Gemini API hatası: {resp.status_code} - {resp.text}")
        
        data = resp.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        try:
            return json.loads(raw_text)
        except Exception:
            raise RuntimeError(f"JSON parse edilemedi: {raw_text}")
            
    raise RuntimeError("Gemini API'ye ulaşılamadı.")

def generate_dynamic_context():
    mekanlar = [
        "terk edilmiş eski bir lunapark",
        "gece yarısı duran ıssız bir metro vagonu",
        "kapısı kilitli eski bir çatı katı",
        "orman yolunda terkedilmiş bir araba",
        "gece yarısı sinyal veren boş bir radyo kulesi"
    ]
    nesneler = ["eski bir kasetçalar", "üzeri çizilmiş bir ayna", "çalan ankesörlü telefon", "eski bir oyuncak bebek"]
    kavramlar = ["zaman kayması", "paralel evren gerilimi", "görünmeyen varlıklar", "psikolojik kabus"]
    
    mekan = random.choice(mekanlar)
    nesne = random.choice(nesneler)
    kavram = random.choice(kavramlar)
    
    return {
        "tema": f"{kavram}, Odak: {nesne}",
        "mekan": mekan,
        "playlist_id": "",
        "anlatici": "erkek",
        "prompt_context": f"Mekan: {mekan}. Odak Nesne: {nesne}. Olay: {kavram}."
    }

def main():
    context = generate_dynamic_context()
    
    prompt = (
        f"Sen Türkçe YouTube Shorts korku kanalı için içerik üreten profesyonel bir yazarsın.\n"
        f"KONU: {context['prompt_context']}\n\n"
        f"Şu JSON formatında çıktı ver:\n"
        f"{{\n"
        f'  "baslik": "YouTube Shorts için 3-5 kelimelik çok merak uyandırıcı Türkçe başlık",\n'
        f'  "senaryo": "Giriş, gelişme ve çarpıcı bir final içeren, birinci ağızdan anlatılan tam 140-160 kelimelik korku hikayesi. Asla selamlama veya parantez içi efekt yazma.",\n'
        f'  "aciklama": "2 cümlelik video açıklaması ve ardından #shorts #korku #hikaye etiketleri"\n'
        f"}}"
    )

    result = call_gemini_json(prompt)
    
    baslik = result.get("baslik", "Gece Yarısı Gelen Ses").strip().replace('"', '')
    senaryo = result.get("senaryo", "").strip().replace('"', '')
    aciklama = result.get("aciklama", "").strip()

    # Kelime kontrolü: Eğer model kısa kestiyse acil durum uzatması
    if len(senaryo.split()) < 100:
        senaryo += " Adımlarım beni o karanlığın en derin yerine çekerken artık geri dönüşün olmadığını çok iyi biliyordum. Arkama baktığımda gördüğüm şey ise sadece sonsuz bir boşluktan ibaretti."

    with open("output/senaryo.txt", "w", encoding="utf-8") as f:
        f.write(senaryo)
        
    with open("output/baslik.txt", "w", encoding="utf-8") as f:
        f.write(baslik)
        
    with open("output/aciklama.txt", "w", encoding="utf-8") as f:
        f.write(aciklama)
        
    tema_ciktisi = {
        "tema": context["tema"],
        "mekan": context["mekan"],
        "anlatici": context["anlatici"]
    }
    with open("output/tema.json", "w", encoding="utf-8") as f:
        json.dump(tema_ciktisi, f, ensure_ascii=False)
        
    with open("output/playlist_id.txt", "w", encoding="utf-8") as f:
        f.write(context.get("playlist_id", ""))

    print(f"✅ Üretim Tamamlandı -> Başlık: {baslik} | Senaryo: {len(senaryo.split())} kelime")

if __name__ == "__main__":
    main()
