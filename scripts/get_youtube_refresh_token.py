#!/usr/bin/env python3
"""
BU SCRIPT SADECE BİR KEZ, KENDİ PC'NDE ÇALIŞTIRILIR.
GitHub Actions içinde ÇALIŞTIRILMAZ.

Amaç: YouTube hesabını yetkilendirip kalıcı bir "refresh token" almak.
Bu token'ı bir kez alıp GitHub Secrets'a kaydedeceğiz, sonra GitHub Actions
her hafta bu token'ı kullanarak senin adına video yükleyecek.

Kurulum:
  pip install google-auth-oauthlib google-api-python-client --break-system-packages

Önce Google Cloud Console'dan bir OAuth2 "Desktop app" client_secret.json
indirip bu script ile aynı klasöre koymalısın (KURULUM_GITHUB.md adım 3).

Kullanım:
  python3 get_youtube_refresh_token.py
"""
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def main():
    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
    creds = flow.run_local_server(port=0)

    print("\n" + "=" * 60)
    print("Aşağıdaki bilgileri GitHub Secrets'a kaydet:")
    print("=" * 60)
    print(f"YT_CLIENT_ID     = {creds.client_id}")
    print(f"YT_CLIENT_SECRET = {creds.client_secret}")
    print(f"YT_REFRESH_TOKEN = {creds.refresh_token}")
    print("=" * 60)


if __name__ == "__main__":
    main()
