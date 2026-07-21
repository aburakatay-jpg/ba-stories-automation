#!/usr/bin/env python3
"""
Refresh token kullanarak YouTube'a video yükler, thumbnail set eder,
ve tema bir seriye aitse videoyu ilgili playlist'e ekler.

Gerekli ortam değişkenleri:
  YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
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
    if len(sys.argv) != 6:
        print(
            "Kullanım: upload_youtube.py <video.mp4> <baslik.txt> <aciklama.txt> <thumbnail.jpg> <playlist_id.txt>",
            file=sys.stderr,
        )
        sys.exit(1)

    video_path, title_path, description_path, thumbnail_path, playlist_path = sys.argv[1:6]

    with open(title_path, "r", encoding="utf-8") as f:
        title = f.read().strip()
    with open(description_path, "r", encoding="utf-8") as f:
        description = f.read().strip()
    with open(playlist_path, "r", encoding="utf-8") as f:
        playlist_id = f.read().strip()

    creds = get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": ["korku", "paranormal", "gerçek hikaye", "şehir efsanesi"],
            "categoryId": "24",
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

    video_id = response["id"]

    youtube.thumbnails().set(
        videoId=video_id,
        media_body=MediaFileUpload(thumbnail_path, mimetype="image/jpeg"),
    ).execute()

    if playlist_id:
        youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {"kind": "youtube#video", "videoId": video_id},
                }
            },
        ).execute()
        print(f"Playlist'e eklendi: {playlist_id}")

    print(f"OK: https://youtube.com/watch?v={video_id} (thumbnail set edildi)")


if __name__ == "__main__":
    main()