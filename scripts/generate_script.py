#!/usr/bin/env python3
"""
temalar.json'dan rastgele bir tema seçer, Groq API ile Türkçe forum-itirafı
tonunda ORİJİNAL bir senaryo yazdırır. Çıktı: output/senaryo.txt, output/baslik.txt

Not: Önceki sürüm Reddit'ten hikaye çekiyordu, ancak GitHub Actions'ın
sunucu IP'leri Reddit tarafından bot olarak engelleniyor (403 Blocked).
Bu yüzden dış kaynağa bağımlı olmayan, tema havuzundan üreten bir yaklaşıma
geçildi — hem daha güvenilir hem de Türk izleyiciye daha uygun.

Gerekli ortam değişkeni: GROQ_API_KEY
"""
import json
import os
import random
import time

import requests

os.makedirs("output", exist_ok=True)

API_URL = "https://api.groq.com/openai/v1/chat/completions"


def call_groq(messages, temperature, max_tokens, timeout=120, max_retries=5):
    """Groq API'ye istek atar, 429 (rate limit) durumunda otomatik bekleyip tekrar dener."""
    api_key = os.environ["GROQ_API_KEY"]
    for attempt in range(max_retries):
        resp = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        if resp.status_code == 429:
            wait = float(resp.headers.get("retry-after", 15))
            wait = max(wait, 10) * (attempt + 1)
            print(f"Rate limit'e takıldık, {wait:.0f} saniye bekleniyor (deneme {attempt + 1}/{max_retries})...")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()

    raise RuntimeError("Groq API'ye çok denemeden sonra bile ulaşılamadı (rate limit)")


def pick_theme():
    with open(os.path.join(os.path.dirname(__file__), "temalar.json"), "r", encoding="utf-8") as f:
        temalar = json.load(f)
    return random.choice(temalar)


def write_script(theme):
    system_prompt = (
        "Sen Türkçe bir korku/paranormal YouTube kanalı için senaryo "
        "yazarısın. Sanki bir forum/itiraf sitesinde birinci ağızdan "
        "gerçek yaşanmış gibi anlatılan, doğal ve akıcı bir Türkçe korku "
        "hikayesi yaz. UZUNLUK ZORUNLU: 1800-2200 kelime — bu, 10-11 "
        "dakikalık bir seslendirmeye denk gelir, kısa kesme. Bu uzunluğa "
        "doğal ulaşmak için hikayeyi şu yapıda kur: (1) güçlü bir kanca "
        "ile açılış, (2) sıradan bir başlangıç ve karakterlerin/ortamın "
        "tanıtımı, (3) ilk tuhaflıklar ve artan şüphe, (4) olayların "
        "yoğunlaşması — en az 2-3 ayrı gerilim anı/sahne, her biri bir "
        "öncekinden daha rahatsız edici, (5) doruk noktası, (6) esrarını "
        "koruyan bir kapanış (net açıklama yapma). Betimlemelerde cömert "
        "ol (ortam, sesler, fiziksel tepkiler, iç ses), ama tekrar veya "
        "doldurma hissi verme — her paragraf hikayeyi ileri taşısın. "
        "Klişe  jump-scare yerine yavaş yavaş büyüyengerilim kullan. Anlatıcı ASLA kendi adını söylemesin veya kendine isimle hitap etmesin, sadece birinci ağızdan ('ben') anlatsın — sadece hikayedeki diğer kişilere isim verilebilir."
        "Sadece senaryo metnini döndür, başlık veya başka açıklama ekleme."
    )
    user_prompt = (
        f"Tema: {theme['tema']}\nMekan: {theme['mekan']}\n\n"
        "Bu tema ve mekana göre, 1800-2200 kelimelik özgün ve sürükleyici "
        "bir hikaye yaz."
    )

    script = call_groq(
        [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        temperature=0.9,
        max_tokens=6000,
    )

    attempts = 0
    while len(script.split()) < 1600 and attempts < 3:
        time.sleep(8)
        cont = call_groq(
            [
                {
                    "role": "system",
                    "content": (
                        "Aşağıdaki Türkçe korku hikayesinin devamını yaz. "
                        "Aynı üslupta, kaldığı yerden akıcı şekilde devam "
                        "et, tekrar etme, gerilimi bir üst seviyeye taşı. "
                        "En az 600 kelime ekle. Sadece devam eden metni "
                        "döndür, önceki kısmı tekrar yazma."
                    ),
                },
                {"role": "user", "content": script},
            ],
            temperature=0.9,
            max_tokens=4000,
        )
        script += "\n\n" + cont
        attempts += 1

    return script


def write_title(theme):
    return call_groq(
        [
            {
                "role": "system",
                "content": (
                    "YouTube korku kanalı için merak uyandıran, kısa (en "
                    "fazla 12 kelime) bir Türkçe başlık yaz. Soru formatı "
                    "veya gizem vurgusu iyi çalışır. Sadece başlığı "
                    "döndür, tırnak işareti kullanma."
                ),
            },
            {"role": "user", "content": f"Tema: {theme['tema']}, Mekan: {theme['mekan']}"},
        ],
        temperature=0.8,
        max_tokens=60,
        timeout=30,
    ).strip('"')


def main():
    theme = pick_theme()
    script = write_script(theme)
    time.sleep(8)
    title = write_title(theme)

    with open("output/senaryo.txt", "w", encoding="utf-8") as f:
        f.write(script)
    with open("output/baslik.txt", "w", encoding="utf-8") as f:
        f.write(title)

    print(f"OK: {len(script)} karakterlik senaryo üretildi — '{title}'")


if __name__ == "__main__":
    main()