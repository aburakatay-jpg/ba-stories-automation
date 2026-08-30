#!/usr/bin/env python3
import json
import os
import random
import time
import requests

os.makedirs("output", exist_ok=True)
# KESİN VE HATASIZ URL - Parantezler temizlendi, en stabil 'pro' modele geçildi.
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent"

def clean_ai_text(text):
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        line = line.strip()
        lower_line = line.lower()
        if lower_line.startswith(("işte", "tabii", "senaryo:", "başlık:", "tamam", "elbette", "uzun senaryo")):
            continue
        if line.startswith("```"):
            continue
        if line:
            cleaned.append(line.replace('*', '').replace('"', '').replace('#', ''))
    return "\n".join(cleaned).strip()

def call_gemini(prompt, temperature=0.9, max_tokens=4000, max_retries=5):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY bulunamadı!")
        
    for attempt in range(max_retries):
        resp = requests.post(
            f"{API_URL}?key={api_key}",
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
                # Güvenlik filtrelerini en geniş ayara alıyoruz ki korku hikayesini engellemesin
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
            time.sleep(60)
            continue
        if not resp.ok:
            raise RuntimeError(f"Gemini API hatası: {resp.status_code} - {resp.text}")
        
        data = resp.json()
        # Hata ayıklama için cevabı yazdır
        if "candidates" not in data or not data["candidates"]:
            print(f"DEBUG: Gelen cevapta candidate yok: {data}")
            raise RuntimeError("API cevabında candidate bulunamadı.")
            
        candidate = data["candidates"][0]
        if "content" not in candidate or "parts" not in candidate["content"]:
            print(f"DEBUG: İçerik yapısı hatalı: {candidate}")
            raise RuntimeError("API cevabında content veya parts bulunamadı.")

        raw_text = candidate["content"]["parts"][0].get("text", "")
        return clean_ai_text(raw_text)
    raise RuntimeError("Gemini API'ye ulaşılamadı")

def get_series_info():
    seri_path = os.path.join(os.path.dirname(__file__), "seri_bilgisi.json")
    if not os.path.exists(seri_path):
        default_series = {
            "karanlik_arsivler": {"ad": "Karanlık Arşivler", "mekan": "Terk Edilmiş Devlet Arşivi", "sayac": 0},
            "deniz_feneri": {"ad": "Yalnız Fener", "mekan": "Okyanus Ortasında Bir Deniz Feneri", "sayac": 0},
            "kayip_kasetler": {"
