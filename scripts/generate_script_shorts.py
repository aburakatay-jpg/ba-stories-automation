#!/usr/bin/env python3
import json
import os
import random
import time
import requests

os.makedirs("output", exist_ok=True)
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

def clean_ai_text(text):
    text = text.replace('"', '').replace('*', '').replace('#', '').strip()
    lines = text.split('\n')
    cleaned = []
    
    for line in lines:
        line = line.strip()
        if not line: continue
        lower_line = line.lower()
        
        # Yapay zekanın saçma giriş cümlelerini atla
        if lower_line.startswith(("işte", "tabii", "tamam", "elbette", "aşağıda")):
            continue
            
        # Eğer yapay zeka "Başlık: X" formatında verdiyse sadece X'i al
        if ":" in line:
            prefix = line.split(":")[0].lower()
            if any(word in prefix for word in ["başlık", "senaryo", "işte", "shorts", "youtube"]):
                line = line.split(":", 1)[1].strip()
                
        cleaned.append(line)
        
    return "\n".join(cleaned).strip()

def call_gemini(prompt, temperature=0.9, max_tokens=1000, max_retries=6):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY bulunamadı!")
        
    for attempt in range(max_retries):
        resp = requests.post(
            f"{API_URL}?key={api_key}",
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
            },
            timeout=120,
        )
        if resp.status_code in [429, 503]:
            print(f"⏳ API yoğun. 60 saniye bekleniyor... (Deneme {attempt+1}/{max_retries})")
            time.sleep(60)
            continue
        if not resp.ok:
            raise RuntimeError(f"Gemini API hatası: {resp.status_code}")
        
        data = resp.json()
        raw_text = data["candidates"][0]["content"]["parts"][0].get("text", "")
        return clean_ai_text(raw_text)
        
    raise RuntimeError("Gemini API'ye ulaşılamadı.")

def generate_dynamic_context():
    mekanlar = ["ıssız bir asansör", "gece yarısı boş bir metro vagonu", "eski bir akıl hastanesi kalıntısı", "orman yolunda tek başına bir araba", "terk edilmiş lunapark"]
    nesneler = ["isimsiz bir kaset", "eski model telefon", "tuhaf çizimler", "güvenlik kameraları", "aynadaki yansıma"]
    kavramlar = ["doğaüstü varlıklar", "zaman döngüsü", "klostrofobi", "paralel gerçeklik", "psikolojik dehşet"]
    
    mekan = random.choice(mekanlar)
    nesne = random.choice(nesneler)
    kavram = random.choice(kavramlar)
    
    return {
        "is_series": False,
        "tema": f"{kavram}, Odak: {nesne}",
        "mekan": mekan,
        "playlist_id": "",
        "anlatici": random.choice(["erkek", "kadin"]),
        "prompt_context": f"Mekan: {mekan}. Odak Nesne: {nesne}. Tema: {kavram}."
    }

def write_script(context):
    prompt = (
        f"Sen Türkçe YouTube Shorts korku senaryosu yazarısın.\n"
        f"Bağlam: {context['prompt_context']}\n"
        f"KURAL: 130-150 kelime arası olsun. Şok edici başla, ürkütücü bitir. "
        f"ASLA 'Merhaba', 'İşte senaryo' gibi kelimeler kullanma, direkt hikayeyi ver."
    )
    return call_gemini(prompt, temperature=0.9, max_tokens=1000)

def write_title(context):
    prompt = (
        f"Aşağıdaki konsepte uygun, YouTube Shorts için 4-5 kelimelik çok korkunç bir başlık yaz.\n"
        f"Bağlam: {context['prompt_context']}\n"
        f"KURAL: SADECE başlık metnini yaz. 'İşte', 'Başlık' gibi kelimeler KULLANMA."
    )
    title = call_gemini(prompt, temperature=0.8, max_tokens=100)
    
    # Tüm filtrelere rağmen yapay zeka 8 kelimeden uzun saçma sapan bir cümle kurarsa acil durum başlığı kullan
    if len(title.split()) > 8 or not title:
        return "Karanlık Sırlar ve Gizem"
        
    return title

def write_description(context, title):
    prompt = (
        f"YouTube Shorts korku videosu için 2 cümlelik SEO uyumlu açıklama yaz.\n"
        f"Bağlam: {context['prompt_context']}\n"
        f"Sonuna #shorts ve 3 tane daha korku etiketi ekle."
    )
    return call_gemini(prompt, temperature=0.7, max_tokens=300)

def main():
    context = generate_dynamic_context()
    script = write_script(context)
    time.sleep(15)
    title = write_title(context)
    time.sleep(10)
    description = write_description(context, title)

    with open("output/senaryo.txt", "w", encoding="utf-8") as f:
        f.write(script)
    with open("output/baslik.txt", "w", encoding="utf-8") as f:
        f.write(title)
    with open("output/aciklama.txt", "w", encoding="utf-8") as f:
        f.write(description)
        
    tema_ciktisi = {"tema": context["tema"], "mekan": context["mekan"], "anlatici": context["anlatici"]}
    with open("output/tema.json", "w", encoding="utf-8") as f:
        json.dump(tema_ciktisi, f, ensure_ascii=False)
    with open("output/playlist_id.txt", "w", encoding="utf-8") as f:
        f.write(context.get("playlist_id", ""))

if __name__ == "__main__":
    main()
