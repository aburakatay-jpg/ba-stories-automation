#!/usr/bin/env python3
import json
import os
import random
import time
import requests

os.makedirs("output", exist_ok=True)
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent"

def clean_ai_text(text):
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        line = line.strip()
        lower_line = line.lower()
        if lower_line.startswith(("işte", "tabii", "senaryo:", "başlık:", "tamam", "elbette", "kısa senaryo")):
            continue
        if line.startswith("```"):
            continue
        if line:
            cleaned.append(line.replace('*', '').replace('"', '').replace('#', ''))
    return "\n".join(cleaned).strip()

def call_gemini(prompt, temperature=0.95, max_tokens=500, max_retries=5):
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
            timeout=60,
        )
        if resp.status_code in [429, 503]:
            time.sleep(30)
            continue
        if not resp.ok:
            raise RuntimeError(f"Gemini API hatası: {resp.status_code}")
        
        data = resp.json()
        raw_text = data["candidates"][0]["content"]["parts"][0].get("text", "")
        return clean_ai_text(raw_text)
    raise RuntimeError("Gemini API'ye ulaşılamadı")

def generate_dynamic_theme():
    """Gemini'ye tamamen özgün, modern ve klişe olmayan bir Shorts konsepti ürettirir."""
    prompt = (
        "YouTube Shorts için benzersiz, modern ve ürkütücü bir mikro korku hikayesi konsepti üret. "
        "Sıradan cin/perili ev klişelerinden kaçın. Dijital paranoya, modern teknoloji, nesnelerin hafızası, "
        "şehir efsaneleri, zaman sapmaları veya kural ihlali temalarından birini seç.\n"
        "Çıktıyı YALNIZCA şu JSON formatında ver:\n"
        '{"tema": "konsept başlığı", "mekan": "spesifik mekan", "odak": "dikkat çeken nesne/durum"}'
    )
    try:
        raw_json = call_gemini(prompt, temperature=1.0, max_tokens=150)
        start = raw_json.find('{')
        end = raw_json.rfind('}') + 1
        data = json.loads(raw_json[start:end])
        return data
    except Exception:
        return {
            "tema": "Akıllı Ev Protokolü",
            "mekan": "Yalnız kalınan akıllı bir daire",
            "odak": "Kendi kendine kilitlenen dijital kapı kilidi"
        }

def write_script(concept):
    prompt = (
        f"Sen bir YouTube Shorts korku yazarıdır. "
        f"Konu: {concept['tema']}, Mekan: {concept['mekan']}, Odak: {concept['odak']}.\n"
        f"ZORUNLU KURALLAR:\n"
        f"1. Uzunluk KESİNLİKLE 85 - 110 kelime arasında olacak (yaklaşık 45 saniyelik okuma süresi).\n"
        f"2. İlk cümle anında merak uyandırmalı (kanca).\n"
        f"3. Birinci tekil şahıs ('ben') ağzından, yaşanmış gibi anlat.\n"
        f"4. Asla 'abone ol', 'beğen' veya 'sen ne düşünüyorsun' gibi kapanış cümleleri EKLEME. Hikaye en tekinsiz anda aniden bitsin.\n"
        f"5. Sadece senaryo metnini döndür."
    )
    return call_gemini(prompt, temperature=0.9, max_tokens=300)

def write_title(concept):
    prompt = (
        f"Şu korku Shorts hikayesi için 5-8 kelimelik, aşırı merak uyandıran, tıklama oranı yüksek bir Türkçe başlık yaz:\n"
        f"Konu: {concept['tema']} - {concept['odak']}\n"
        f"Başlığın sonuna sadece #shorts ekle. Başka açıklama yapma."
    )
    return call_gemini(prompt, temperature=0.8, max_tokens=40)

def write_description(title, concept):
    prompt = (
        f"Başlık: {title}\nKonsept: {concept['tema']} ({concept['mekan']}).\n"
        f"Bu Shorts için 2 cümlelik merak uyandıran özet ve 8 adet popüler Türkçe korku hashtag'i yaz."
    )
    return call_gemini(prompt, temperature=0.7, max_tokens=200)

def main():
    concept = generate_dynamic_theme()
    print(f"Yeni Dinamik Tema: {concept['tema']} ({concept['mekan']})")
    
    script = write_script(concept)
    time.sleep(2)
    title = write_title(concept)
    time.sleep(2)
    description = write_description(title, concept)

    with open("output/senaryo.txt", "w", encoding="utf-8") as f:
        f.write(script)
    with open("output/baslik.txt", "w", encoding="utf-8") as f:
        f.write(title)
    with open("output/aciklama.txt", "w", encoding="utf-8") as f:
        f.write(description)
        
    with open("output/tema.json", "w", encoding="utf-8") as f:
        json.dump(concept, f, ensure_ascii=False)
        
    with open("output/playlist_id.txt", "w", encoding="utf-8") as f:
        f.write("")

    print(f"✅ Shorts Hazır (Kelime Sayısı: {len(script.split())}) — Başlık: {title}")

if __name__ == "__main__":
    main()
