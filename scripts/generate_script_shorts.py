#!/usr/bin/env python3
import json
import os
import random
import time
import requests

os.makedirs("output", exist_ok=True)
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent"

def clean_ai_text(text):
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        line = line.strip()
        lower_line = line.lower()
        if lower_line.startswith(("işte", "tabii", "senaryo:", "başlık:", "tamam", "elbette", "shorts")):
            continue
        if line.startswith("```"):
            continue
        if line:
            cleaned.append(line.replace('*', '').replace('"', '').replace('#', ''))
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
                "safetySettings": [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
            },
            timeout=120,
        )
        if resp.status_code in [429, 503]:
            print(f"⏳ API yoğun. 60 saniye bekleniyor... (Deneme {attempt+1}/{max_retries})")
            time.sleep(60)
            continue
        if not resp.ok:
            raise RuntimeError(f"Gemini API hatası: {resp.status_code} - {resp.text}")
        
        data = resp.json()
        if "candidates" not in data or not data["candidates"]:
            raise RuntimeError("API cevabında candidate bulunamadı.")
            
        candidate = data["candidates"][0]
        if "content" not in candidate or "parts" not in candidate["content"]:
            raise RuntimeError("API cevabında content veya parts bulunamadı.")

        raw_text = candidate["content"]["parts"][0].get("text", "")
        return clean_ai_text(raw_text)
    raise RuntimeError("Gemini API'ye ulaşılamadı.")

def generate_dynamic_context():
    mekanlar = ["ıssız bir asansör", "gece yarısı boş bir metro vagonu", "eski bir akıl hastanesi kalıntısı", "orman yolunda tek başına bir araba", "terk edilmiş bir lunapark"]
    nesneler = ["isimsiz bir kaset", "gece yarısı çalan eski model bir telefon", "duvardaki tuhaf çizimler", "kendiliğinden açılan güvenlik kameraları", "aynadaki farklı yansıma"]
    kavramlar = ["doğaüstü varlıklar", "zaman döngüsü", "klostrofobik gerilim", "paralel gerçeklik", "psikolojik dehşet"]
    
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
        f"Sen Türkçe bir YouTube kanalı için YOUTUBE SHORTS (Kısa Video) korku senaryosu yazarısın. "
        f"Lütfen en fazla 130-150 kelime uzunluğunda, hızlı okunduğunda 45-55 saniye sürecek, "
        f"birinci ağızdan ('ben') anlatılan vurucu bir kısa hikaye yaz.\n\n"
        f"BAĞLAM: {context['prompt_context']}\n\n"
        f"YAPI VE KURALLAR:\n"
        f"1. Asla 'Merhaba', 'Kanalıma abone olun' gibi girişler yapma. Direkt olayın ortasından, şok edici bir cümleyle başla.\n"
        f"2. Kelime israfı yapma, gerilimi çok hızlı tırmandır.\n"
        f"3. Finali çok ani ve ürkütücü bir sonla (plot twist) bitir.\n"
        f"4. Sadece senaryo metnini ver."
    )
    return call_gemini(prompt, temperature=0.9, max_tokens=1000)

def write_title(context):
    prompt = (
        f"Aşağıdaki konsepte uygun, YouTube Shorts için 4-6 kelimelik, çok merak uyandıran Türkçe bir korku videosu başlığı yaz.\n"
        f"Konsept: {context['prompt_context']}\n"
    )
    title = call_gemini(prompt, temperature=0.8, max_tokens=150)
    clean_title = title.replace('"', '').replace('*', '').replace("'", "").strip()
    
    # Yapay zekanın başlığa sızdırdığı kelimeleri temizleme filtresi
    for prefix in ["Başlık:", "Sadece başlığı ver", "Sadece başlığı ver,", "İşte başlık:", "Sadece başlık:"]:
        if clean_title.lower().startswith(prefix.lower()):
            clean_title = clean_title[len(prefix):].strip()
            
    if not clean_title or len(clean_title) < 3:
         clean_title = "Karanlık Sırlar"
         
    return clean_title

def write_description(context, title):
    prompt = (
        f"YouTube Shorts korku videosu için 2-3 cümlelik SEO uyumlu, izleyiciyi içine çekecek kısa bir açıklama yaz. "
        f"Altına #shorts ve ilgili Türkçe hashtag'ler (5-6 tane) ekle. "
        f"Sadece açıklamayı döndür.\nBaşlık: {title}\nBağlam: {context['prompt_context']}"
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
