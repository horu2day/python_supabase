import os
import flet as ft
from flet.auth.providers import GoogleOAuthProvider
from supabase import create_client, Client

# Google OAuth 환경 변수
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
assert GOOGLE_CLIENT_ID, "set GOOGLE_CLIENT_ID environment variable"
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
assert GOOGLE_CLIENT_SECRET, "set GOOGLE_CLIENT_SECRET environment variable"

# Supabase 환경 변수
SUPABASE_URL = os.getenv("SUPABASE_URL")
assert SUPABASE_URL, "set SUPABASE_URL environment variable"
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
assert SUPABASE_KEY, "set SUPABASE_KEY environment variable"

# Supabase 클라이언트 초기화
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def main(page: ft.Page):
    # 페이지 속성 설정
    page.title = "사용자 관리 시스템"
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Google OAuth 제공자 설정
    provider = GoogleOAuthProvider(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        redirect_url="https://auth4flet.fly.dev/oauth_callback", 
    )
    
    # 사용자 정보 표시를 위한 UI 컴포넌트
    login_button = ft.ElevatedButton("Google로 로그인", on_click=lambda e: page.login(provider))
    logout_button = ft.ElevatedButton("로그아웃", on_click=lambda e: handle_logout(e))
    user_info = ft.Column(visible=False)
    
    # 로그인 처리 함수
    def on_login(e):
        if e.error:
            show_message(f"로그인 오류: {e.error}")
            return
        
        # Google 로그인 성공, Supabase와 연동
        try:
            # 사용자 정보 가져오기
            user_id = page.auth.user.id
            user_email = page.auth.user['email']
            user_name = page.auth.user['name']
            
            # Supabase에서 사용자 검색
            result = supabase.table("users").select("*").eq("user_id", user_id).execute()
            
            if not result.data:
                # 신규 사용자 - Supabase에 추가
                user_data = {
                    "user_id": user_id,
                    "email": user_email,
                    "name": user_name,
                    "subscription_type": "free",  # 기본값: 무료 사용자
                    "created_at": "now()"
                }
                supabase.table("users").insert(user_data).execute()
                show_message(f"환영합니다! {user_name}님의 계정이 생성되었습니다.")
            else:
                # 기존 사용자
                show_message(f"{user_name}님, 다시 오신 것을 환영합니다!")
            
            # 로그인 UI 업데이트
            update_user_info()
            
        except Exception as e:
            show_message(f"사용자 데이터 처리 중 오류 발생: {str(e)}")
    
    # 로그아웃 처리 함수
    def handle_logout(e):
        # 로컬 인증 상태 초기화
        try:
            page.logout()
        except Exception as e:
            show_message(f"사용자 데이터 처리 중 오류 발생: {str(e)}")

            # 로그아웃 UI 업데이트
        login_button.visible = True
        logout_button.visible = False
        user_info.visible = False
        
        show_message("로그아웃되었습니다.")
        page.update()
    
    # 사용자 정보 표시 업데이트 함수
    def update_user_info():
        if page.auth and page.auth.user:
            # Supabase에서 사용자 정보 가져오기
            user_id = page.auth.user.id
            result = supabase.table("users").select("*").eq("user_id", user_id).execute()
            
            if result.data:
                user_data = result.data[0]
                
                # 사용자 정보 표시 업데이트
                user_info.controls = [
                    ft.Text(f"이름: {user_data.get('name', '알 수 없음')}", size=18),
                    ft.Text(f"이메일: {user_data.get('email', '알 수 없음')}"),
                    ft.Text(f"구독 유형: {user_data.get('subscription_type', 'free')}"),
                    ft.Container(height=20),
                    ft.Text("계정 정보", weight=ft.FontWeight.BOLD),
                    ft.Text(f"계정 생성일: {user_data.get('created_at', '알 수 없음')}")
                ]
                
                # 버튼 표시 상태 업데이트
                login_button.visible = False
                logout_button.visible = True
                user_info.visible = True
                page.update()
    
    # 메시지 표시 헬퍼 함수
    def show_message(message):
        page.snack_bar = ft.SnackBar(content=ft.Text(message))
        page.snack_bar.open = True
        page.update()
    
    # 페이지 이벤트 핸들러 설정
    page.on_login = on_login
    
    # 앱 레이아웃 생성
    title = ft.Text("사용자 관리 시스템", size=30, weight=ft.FontWeight.BOLD)
    
    # 모든 컨트롤을 페이지에 추가
    page.add(
        ft.Column([
            title,
            ft.Container(height=20),
            login_button,
            logout_button,
            ft.Container(height=30),
            user_info
        ], alignment=ft.MainAxisAlignment.START)
    )
    
    # UI 초기 상태 설정 (로그아웃 버튼 숨김)
    logout_button.visible = False

# 앱 실행
port = int(os.getenv("PORT", "8000"))
ft.app(main, port=port, view=ft.WEB_BROWSER)