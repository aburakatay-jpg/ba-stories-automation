#!/usr/bin/env python3
import json
import os
import random
import time
import requests

os.makedirs("output", exist_ok=True)
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent"

def call_gemini(prompt, temperature=0.8, max_tokens=1500, max_retries=5):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY bulunamadı!")
        
    for attempt in range(max_retries):
        resp = requests.post(
            f"{API_URL}?key={api_key}",
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens
                }
            },
            timeout=120,
        )
        if resp.status_code in [429, 503]:
            print(f"⏳ API yoğun. 30 saniye bekleniyor... (Deneme {attempt+1}/{max_retries})")
            time.sleep(30)
            continue
        if not resp.ok:
            raise RuntimeError(f"Gemini API hatası: {resp.status_code} - {resp.text}")
        
        data = resp.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception:
            raise RuntimeError("API geçerli bir metin döndürmedi.")
            
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

def clean_script(raw_text):
    # Markdown, tırnak ve gereksiz etiketleri temizle ama hikayeyi ASLA kesme
    lines = raw_text.split("\n")
    valid_lines = []
    for line in lines:
        l = line.strip().replace("*", "").replace("#", "").replace('"', '')
        if not l:
            continue
        lower_l = l.lower()
        if any(lower_l.startswith(x) for x in ["senaryo:", "başlık:", "metin:", "işte", "tabii"]):
            continue
        valid_lines.append(l)
    return " ".join(valid_lines)

def clean_title(raw_title):
    t = raw_title.replace('"', '').replace('*', '').replace('#', '').strip()
    lines = [x.strip() for x in t.split('\n') if x.strip()]
    if lines:
        t = lines[0]
    if ":" in t:
        t = t.split(":", 1)[1].strip()
    for prefix in ["İşte başlık", "Başlık", "Shorts Başlığı"]:
        if t.lower().startswith(prefix.lower()):
            t = t[len(prefix):].strip(" :,-")
    return t if len(t) >= 5 else "Gecenin Karanlık Sırrı"

def main():
    context = generate_dynamic_context()
    
    # 1. SENARYO ÜRETİMİ (Uzunluk garantili)
    script_prompt = (
        f"Sen bir korku YouTube Shorts kanalı için seslendirme metni yazıyorsun.\n"
        f"KONU: {context['prompt_context']}\n\n"
        f"ZORUNLU KURALLAR:\n"
        f"1. Metin tam olarak 130 ile 160 kelime arasında olmalıdır (yaklaşık 45-50 saniye okunacak).\n"
        f"2. Giriş, gelişme ve korkunç bir sonu olmalı. Hikayeyi asla yarım bırakma.\n"
        f"3. Sadece okunacak hikaye metnini ver. Hiçbir başlık, açıklama, selamlama veya parantez içi efekt yazma."
    )
    raw_script = call_gemini(script_prompt, temperature=0.8, max_tokens=1500)
    final_script = clean_script(raw_script)
    
    time.sleep(10)
    
    # 2. BAŞLIK ÜRETİMİ
    title_prompt = (
        f"Aşağıdaki korku hikayesi için YouTube Shorts'ta tıklanma alacak 4-6 kelimelik çarpıcı bir Türkçe başlık yaz.\n"
        f"Hikaye: {final_script[:300]}...\n\n"
        f"KURAL: SADECE başlığı yaz. Tırnak, etiket veya açıklama ekleme."
    )
    raw_title = call_gemini(title_prompt, temperature=0.7, max_tokens=100)
    final_title = clean_title(raw_title)
    
    time.sleep(10)
    
    # 3. AÇIKLAMA ÜRETİMİ
    desc_prompt = (
        f"Başlık: {final_title}\n"
        f"Bu YouTube Shorts videosu için 2 cümlelik gizemli bir açıklama ve altına 5 adet korku etiketi (#shorts #korku vb.) yaz."
    )
    raw_desc = call_gemini(desc_prompt, temperature=0.7, max_tokens=300)
    final_desc = raw_desc.replace('"', '').strip()

    # Dosyaları diske yaz
    with open("output/senaryo.txt", "w", encoding="utf-8") as f:
        f.write(final_script)
        
    with open("output/baslik.txt", "w", encoding="utf-8") as f:
        f.write(final_title)
        
    with open("output/aciklama.txt", "w", encoding="utf-8") as f:
        f.write(final_desc)
        
    tema_ciktisi = {
        "tema": context["tema"],
        "mekan": context["mekan"],
        "anlatici": context["anlatici"]
    }
    with open("output/tema.json", "w", encoding="utf-8") as f:
        json.dump(tema_ciktisi, f, ensure_ascii=False)
        
    with open("output/playlist_id.txt", "w", encoding="utf-8") as f:
        f.write(context.get("playlist_id", ""))

    print(f"✅ Senaryo ({len(final_script.split())} kelime) ve Başlık ('{final_title}') hazırlandı.")

if __name__ == "__main__":
    main()
