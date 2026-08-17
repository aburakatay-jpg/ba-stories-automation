#!/usr/bin/env python3
import json
import os
import random
import time
import requests

os.makedirs("output", exist_ok=True)

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent"
GECMIS_UZUNLUK = 6

def clean_ai_text(text):
    """Yapay zekanın üretebileceği 'İşte senaryonuz:' gibi kalıpları ve markdown karakterlerini temizler."""
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        line = line.strip()
        lower_line = line.lower()
        # AI giriş kalıplarını atla
        if lower_line.startswith(("işte", "tabii", "senaryo:", "başlık:", "tamam", "elbette", "kısa senaryo")):
            continue
        if line.startswith("```"):
            continue
        if line:
            # Okumayı bozan markdown işaretlerini temizle
            cleaned.append(line.replace('*', '').replace('"', '').replace('#', ''))
    return "\n".join(cleaned).strip()

def call_gemini(prompt, temperature=0.9, max_tokens=500, max_retries=5):
    api_key = os.environ["GEMINI_API_KEY"]
    for attempt in range(max_retries):
        resp = requests.post(
            f"{API_URL}?key={api_key}",
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                },
            },
            timeout=60,
        )
        if resp.status_code == 429:
            wait = 30
            time.sleep(wait)
            continue
        if not resp.ok:
            raise RuntimeError(f"Gemini API hatası: {resp.status_code}")
        
        raw_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        return clean_ai_text(raw_text) # Filtreden geçirerek döndür
        
    raise RuntimeError("Gemini API'ye ulaşılamadı")

def pick_theme():
    base_dir = os.path.dirname(__file__)
    temalar_path = os.path.join(base_dir, "temalar_shorts.json")
    gecmis_path = os.path.join(base_dir, "tema_gecmisi_shorts.json")

    with open(temalar_path, "r", encoding="utf-8") as f:
        temalar = json.load(f)

    gecmis = []
    if os.path.exists(gecmis_path):
        with open(gecmis_path, "r", encoding="utf-8") as f:
            gecmis = json.load(f)

    uygun = [t for t in temalar if t["tema"] not in gecmis]
    if not uygun:
        uygun = temalar

    secilen = random.choice(uygun)

    gecmis.append(secilen["tema"])
    gecmis = gecmis[-GECMIS_UZUNLUK:]
    with open(gecmis_path, "w", encoding="utf-8") as f:
        json.dump(gecmis, f, ensure_ascii=False, indent=2)

    return secilen

def write_script(theme):
    prompt = (
        f"Sen Türkçe bir korku YouTube Shorts kanalı için senaryo yazarısın. "
        f"Sanki forumda birinci ağızdan gerçek yaşanmış gibi anlatılan, çok kısa "
        f"ve çarpıcı bir korku anısı yaz. UZUNLUK ZORUNLU: 150-200 kelime. "
        f"İlk cümle anında kanca atmalı. KESİNLİKLE 'İşte senaryo', 'Tabii ki' gibi cümlelerle başlama. "
        f"Direkt hikayeye gir. Anlatıcı ASLA kendi adını söylemesin, birinci ağızdan ('ben') anlatsın. "
        f"DİL KURALI: SADECE düzgün Türkçe olacak. Sadece senaryo metnini döndür.\n\n"
        f"Tema: {theme['tema']}\nMekan: {theme['mekan']}"
    )
    return call_gemini(prompt, temperature=0.95, max_tokens=600)

def write_title(theme):
    prompt = (
        f"YouTube Shorts korku videosu için en fazla 8 kelimelik, merak uyandıran "
        f"bir Türkçe başlık yaz. KESİNLİKLE 'İşte başlık', 'Başlık:' gibi kelimeler kullanma. "
        f"Sadece başlığı döndür.\nTema: {theme['tema']}, Mekan: {theme['mekan']}"
    )
    return call_gemini(prompt, temperature=0.8, max_tokens=40)

def write_description(theme, title):
    prompt = (
        f"YouTube korku videosu için SEO uyumlu bir açıklama yaz. 2-3 cümlelik "
        f"merak uyandıran bir özet ve aşağıya ilgili Türkçe hashtag'ler (en az 8 tane) ekle. "
        f"Sadece açıklamayı döndür.\nBaşlık: {title}\nTema: {theme['tema']}, Mekan: {theme['mekan']}"
    )
    return call_gemini(prompt, temperature=0.7, max_tokens=300)

def write_cta():
    prompt = (
        f"Türkçe korku Shorts videosu için 2 cümlelik, yoruma ve abone olmaya davet eden "
        f"doğal bir kapanış metni yaz. Sadece kapanış metnini döndür, açıklama yapma."
    )
    return call_gemini(prompt, temperature=0.8, max_tokens=150)

def main():
    theme = pick_theme()
    script = write_script(theme)

    time.sleep(2)
    cta = write_cta()
    script = script + "\n\n" + cta

    time.sleep(2)
    title = write_title(theme)
    # Tırnak işaretlerini başlık için ekstra temizle
    title = title.replace('"', '').replace("'", "")

    time.sleep(2)
    description = write_description(theme, title)

    with open("output/senaryo.txt", "w", encoding="utf-8") as f:
        f.write(script)
    with open("output/baslik.txt", "w", encoding="utf-8") as f:
        f.write(title)
    with open("output/aciklama.txt", "w", encoding="utf-8") as f:
        f.write(description)
    with open("output/tema.json", "w", encoding="utf-8") as f:
        json.dump(theme, f, ensure_ascii=False)
    with open("output/playlist_id.txt", "w", encoding="utf-8") as f:
        f.write("")

    print(f"OK: {len(script)} karakterlik short senaryosu temizlendi ve üretildi — '{title}'")

if __name__ == "__main__":
    main()
