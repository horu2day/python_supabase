import os

import flet as ft
from flet.auth.providers import GoogleOAuthProvider

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
assert GOOGLE_CLIENT_ID, "set GOOGLE_CLIENT_ID environment variable"
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
assert GOOGLE_CLIENT_SECRET, "set GOOGLE_CLIENT_SECRET environment variable"

def main(page: ft.Page):
    provider = GoogleOAuthProvider(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        redirect_url="http://localhost:8550/oauth_callback",
    )

    def login_click(e):
        page.login(provider)

    def on_login(e):
        print("Login error:", e.error)
        print("Access token:", page.auth.token.access_token)
        print("User ID:", page.auth.user.id)

    page.on_login = on_login
    page.add(ft.ElevatedButton("Google로 로그인", on_click=login_click))

ft.app(main, port=8550, view=ft.WEB_BROWSER)