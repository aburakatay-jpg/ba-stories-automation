#!/usr/bin/env python3
import os
import requests

def add_row_to_sheet(title, video_id, video_type, theme, publish_date, initial_views):
    webhook_url = os.environ.get("SHEETS_WEBHOOK_URL")
    if not webhook_url:
        print("⚠️ SHEETS_WEBHOOK_URL bulunamadı, tabloya kayıt atlanıyor.")
        return

    # Görseldeki tablo sütunlarına birebir uyumlu payload (A'dan I'ya)
    payload = {
        "title": title,                # A Sütunu: BAŞLIK
        "videoId": video_id,          # B Sütunu: VIDEO ID
        "type": video_type,            # C Sütunu: TÜR
        "theme": theme,                # D Sütunu: TEMA/KONSEPT
        "publishDate": publish_date,   # E Sütunu: YAYIN TARİHİ
        "initialViews": initial_views, # F Sütunu: İLK İZLENME
        "currentViews": initial_views, # G Sütunu: GÜNCEL İZLENME
        "currentLikes": 0,             # H Sütunu: GÜNCEL BEĞENİ
        "currentComments": 0           # I Sütunu: GÜNCEL YORUM
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=30)
        if response.status_code == 200:
            print("✅ Video başarıyla Google Sheets tablosuna kaydedildi.")
        else:
            print(f"⚠️ Sheets kayıt hatası: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"⚠️ Webhook bağlantı hatası: {e}")

if __name__ == "__main__":
    print("Log script tablo düzenine göre güncellendi.")
