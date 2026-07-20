#!/usr/bin/env python3
"""
Refresh token kullanarak YouTube'a video yükler (insansız/unattended çalışır).

Gerekli ortam değişkenleri:
  YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN

Bu üçünü almak için önce get_youtube_refresh_token.py'yi kendi PC'nde
BİR KERE çalıştırman gerekiyor (bkz. KURULUM_GITHUB.md).
"""
import os
import sys

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


def get_credentials():
    return Credentials(
        token=None,
        refresh_token=os.environ["YT_REFRESH_TOKEN"],
        client_id=os.environ["YT_CLIENT_ID"],
        client_secret=os.environ["YT_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
    )


def main():
    if len(sys.argv) != 4:
        print("Kullanım: upload_youtube.py <video.mp4> <baslik.txt> <aciklama.txt>", file=sys.stderr)
        sys.exit(1)

    video_path, title_path, description_path = sys.argv[1], sys.argv[2], sys.argv[3]

    with open(title_path, "r", encoding="utf-8") as f:
        title = f.read().strip()
    with open(description_path, "r", encoding="utf-8") as f:
        description = f.read().strip()

    creds = get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": ["korku", "paranormal", "gerçek hikaye", "şehir efsanesi"],
            "categoryId": "24",  # Entertainment
        },
        "status": {"privacyStatus": "public"},
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Yükleniyor: %{int(status.progress() * 100)}")

    print(f"OK: https://youtube.com/watch?v={response['id']}")


if __name__ == "__main__":
    main()
