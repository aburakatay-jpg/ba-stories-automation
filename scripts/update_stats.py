#!/usr/bin/env python3
import os
import requests

def get_channel_videos(api_key, channel_id):
    # Kanalın "Yüklemeler" oynatma listesini bul (UC ile başlayan kanal ID'sini UU ile değiştirerek bulunur)
    uploads_playlist_id = channel_id.replace("UC", "UU", 1)
    
    url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={uploads_playlist_id}&maxResults=50&key={api_key}"
    response = requests.get(url)
    if response.status_code != 200:
        print("⚠️ YouTube API Hatası (Playlist):", response.text)
        return []
    
    items = response.json().get("items", [])
    return [item["snippet"]["resourceId"]["videoId"] for item in items]

def get_video_stats(api_key, video_ids):
    if not video_ids: return []
    ids_str = ",".join(video_ids)
    url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics&id={ids_str}&key={api_key}"
    response = requests.get(url)
    if response.status_code != 200:
        print("⚠️ YouTube API Hatası (Stats):", response.text)
        return []
    
    return response.json().get("items", [])

def update_sheet(webhook_url, video_id, views, likes, comments):
    # Tabloya 'update' aksiyonu ile gönderiyoruz
    payload = {
        "action": "update",
        "videoId": video_id,
        "currentViews": views,
        "currentLikes": likes,
        "currentComments": comments
    }
    try:
        requests.post(webhook_url, json=payload, timeout=10)
        print(f"✅ {video_id} güncellendi: {views} İzlenme, {likes} Beğeni")
    except Exception as e:
        print(f"⚠️ Hata: {video_id} - {e}")

def main():
    api_key = os.environ.get("YOUTUBE_API_KEY")
    webhook_url = os.environ.get("SHEETS_WEBHOOK_URL")
    channel_id = os.environ.get("YOUTUBE_CHANNEL_ID") 

    if not all([api_key, webhook_url, channel_id]):
        print("⚠️ Eksik API anahtarları! YOUTUBE_API_KEY, SHEETS_WEBHOOK_URL ve YOUTUBE_CHANNEL_ID Github Secrets'ta olmalı.")
        return

    print("🔄 YouTube'dan son videolar çekiliyor...")
    video_ids = get_channel_videos(api_key, channel_id)
    
    if not video_ids:
        print("Video bulunamadı.")
        return

    print("📊 İstatistikler alınıyor...")
    stats = get_video_stats(api_key, video_ids)

    print("📈 Tablo güncelleniyor...")
    for item in stats:
        vid = item["id"]
        stat = item["statistics"]
        views = stat.get("viewCount", 0)
        likes = stat.get("likeCount", 0)
        comments = stat.get("commentCount", 0)
        
        update_sheet(webhook_url, vid, views, likes, comments)

    print("🚀 Günlük tablo güncellemesi tamamlandı!")

if __name__ == "__main__":
    main()
