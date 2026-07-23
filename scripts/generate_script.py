#!/usr/bin/env python3
"""
temalar.json'dan, SON KULLANILAN TEMALARI HARİÇ TUTARAK rastgele bir tema
seçer, Groq API ile Türkçe forum-itirafı tonunda ORİJİNAL bir senaryo
yazdırır, sonra bir "düzelti" geçişiyle imla/yabancı kelime hatalarını
otomatik temizler. Çıktı: output/senaryo.txt, output/baslik.txt, output/aciklama.txt

Gerekli ortam değişkeni: GROQ_API_KEY
"""
import json
import os
import random
import time

import requests

os.makedirs("output", exist_ok=True)

API_URL = "https://api.groq.com/openai/v1/chat/completions"
GECMIS_UZUNLUK = 8


def call_groq(messages, temperature, max_tokens, timeout=120, max_retries=5):
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
    base_dir = os.path.dirname(__file__)
    temalar_path = os.path.join(base_dir, "temalar.json")
    gecmis_path = os.path.join(base_dir, "tema_gecmisi.json")

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
        "Klişe jump-scare yerine yavaş yavaş büyüyen gerilim kullan. "
        "Anlatıcı ASLA kendi adını söylemesin veya kendine isimle hitap "
        "etmesin, sadece birinci ağızdan ('ben') anlatsın — sadece "
        "hikayedeki diğer kişilere isim verilebilir. DİL KURALI: metin "
        "SADECE düzgün, standart yazım kurallarına uygun Türkçe olacak. "
        "Tek bir İngilizce kelime, marka adı ya da yabancı sözcük bile "
        "kullanma. Uydurma, hatalı çekimlenmiş veya var olmayan kelime "
        "kullanma - her kelime gerçek, doğru yazılmış bir Türkçe kelime "
        "olmalı. Sadece senaryo metnini döndür, başlık veya başka "
        "açıklama ekleme."
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
                        "En az 600 kelime ekle. SADECE düzgün, standart "
                        "yazım kurallarına uygun Türkçe kullan, İngilizce "
                        "kelime veya uydurma/hatalı kelime kullanma. "
                        "Sadece devam eden metni döndür, önceki kısmı "
                        "tekrar yazma."
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


def proofread_script(script):
    """Metni bir kez daha okutup imla hatalarını ve yabancı kelimeleri temizler."""
    return call_groq(
        [
            {
                "role": "system",
                "content": (
                    "Sen bir Türkçe dil editörüsün. Sana verilen metni "
                    "dikkatlice gözden geçir ve SADECE şu hataları "
                    "düzelt: (1) yazım/imla hataları, (2) var olmayan "
                    "veya hatalı çekimlenmiş kelimeler, (3) İngilizce "
                    "veya yabancı kelimeleri doğru Türkçe karşılığıyla "
                    "değiştir. Metnin anlamını, uzunluğunu, üslubunu ve "
                    "cümle yapısını DEĞİŞTİRME - sadece hataları düzelt. "
                    "Sadece düzeltilmiş metni döndür, açıklama ekleme."
                ),
            },
            {"role": "user", "content": script},
        ],
        temperature=0.3,
        max_tokens=6000,
    )


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


def write_description(theme, title):
    return call_groq(
        [
            {
                "role": "system",
                "content": (
                    "YouTube korku videosu için SEO uyumlu bir açıklama "
                    "yaz. 2-3 cümlelik merak uyandıran bir özet + "
                    "aşağıya ilgili Türkçe hashtag'ler (en az 8 tane, "
                    "örn. #korku #paranormal #gerçekhikaye #gizem gibi) "
                    "ekle. Hikayenin sonunu ifşa etme. Sadece açıklama "
                    "metnini döndür."
                ),
            },
            {
                "role": "user",
                "content": f"Başlık: {title}\nTema: {theme['tema']}, Mekan: {theme['mekan']}",
            },
        ],
        temperature=0.7,
        max_tokens=300,
        timeout=30,
    )
def write_cta():
    return call_groq(
        [
            {
                "role": "system",
                "content": (
                    "Türkçe bir korku/paranormal YouTube kanalı için, "
                    "videonun sonuna eklenecek kısa (2-3 cümle) ve doğal "
                    "bir kapanış metni yaz. Sanki anlatıcı hikayeyi "
                    "bitirdikten sonra izleyiciye dönüyormuş gibi, sohbet "
                    "tarzında olsun. Şu unsurları içersin: (1) hikayenin "
                    "gerçek mi kurgu mu olduğu sorusu, (2) yorumlara "
                    "davet, (3) abone ol çağrısı. Klişe ve yapay "
                    "gelmesin, samimi ve kısa olsun. Sadece metni "
                    "döndür."
                ),
            },
            {
                "role": "user",
                "content": "Kanalımız için bir kapanış metni yaz.",
            },
        ],
        temperature=0.8,
        max_tokens=150,
        timeout=30,
    )



def apply_series(theme, title):
    seri_path = os.path.join(os.path.dirname(__file__), "seri_bilgisi.json")
    with open(seri_path, "r", encoding="utf-8") as f:
        seriler = json.load(f)

    seri_key = theme.get("seri")
    if not seri_key or seri_key not in seriler:
        return title, ""

    seriler[seri_key]["sayac"] += 1
    with open(seri_path, "w", encoding="utf-8") as f:
        json.dump(seriler, f, ensure_ascii=False, indent=2)

    yeni_baslik = f"{seriler[seri_key]['ad']} #{seriler[seri_key]['sayac']}: {title}"
    return yeni_baslik, seriler[seri_key]["playlist_id"]


def main():
    theme = pick_theme()
    script = write_script(theme)

    time.sleep(8)
    script = proofread_script(script)

    time.sleep(5)
    cta = write_cta()
    script = script + "\n\n" + cta

    time.sleep(8)
    title = write_title(theme)
    title, playlist_id = apply_series(theme, title)

    time.sleep(5)
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
        f.write(playlist_id)

    print(f"OK: {len(script)} karakterlik senaryo üretildi — '{title}'")


if __name__ == "__main__":
    main()