import os
import flet as ft
from flet.auth.providers import GoogleOAuthProvider
from supabase import create_client

# Google OAuth 환경 변수
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "your-client-id")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "your-client-secret")

# Supabase 환경 변수
SUPABASE_URL = os.getenv("SUPABASE_URL", "your-supabase-url")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "your-supabase-key")

# Supabase 클라이언트 초기화
supabase = None
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Supabase 초기화 오류: {e}")

def main(page: ft.Page):
    # 페이지 속성 설정
    page.title = "유튜브 중독자 로그인"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    
    # 테스트용 자동 로그인 기능
    def auto_login_for_testing():
        # 테스트용 사용자 데이터
        user_data = {
            "user_id": "test123",
            "name": "테스트 사용자",
            "email": "test@example.com",
            "picture": None,
            "subscription_type": "Free"
        }
        
        # 직접 메인 화면으로 전환
        page.clean()
        page.add(create_youtube_analyzer_view(user_data))
        page.update()
    
    # 테스트/디버그 모드 - 자동 로그인을 원하면 아래 주석을 해제
    page.add(ft.ElevatedButton("테스트 모드: 자동 로그인", on_click=lambda _: auto_login_for_testing()))
    


    # Google OAuth 제공자 설정
    provider = GoogleOAuthProvider(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        redirect_url="http://localhost:8000/api/oauth/redirect", 
        # redirect_url="https://auth4flet.fly.dev/oauth_callback", 
        
    )
    
    # 로그인 화면 컴포넌트
    def create_login_view():
        return ft.Column(
            [
                ft.Container(
                    content=ft.Image(
                        src="assets/video-player.png",
                        width=200,
                        height=200,
                        fit=ft.ImageFit.CONTAIN,
                    ),
                    margin=ft.margin.only(bottom=25),
                ),
                ft.Text(
                    "유튜브 중독자",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.RED_600,
                ),
                ft.Text(
                    "YouTube 영상 분석 및 지식화 도구",
                    size=16,
                    color=ft.colors.GREY_700,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(
                    content=ft.ElevatedButton(
                        content=ft.Row(
                            [
                                ft.Image(
                                    src="assets/google.png",
                                    width=24,
                                    height=24,
                                ),
                                ft.Text("Google로 로그인"),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=10,
                        ),
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10),
                            padding=ft.padding.all(15),
                        ),
                        width=280,
                        on_click=lambda e: page.login(provider),
                    ),
                    margin=ft.margin.only(top=30),
                ),
                ft.Container(
                    content=ft.Text(
                        "로그인하면 모든 기능을 사용할 수 있습니다",
                        size=12,
                        color=ft.colors.GREY_500,
                    ),
                    margin=ft.margin.only(top=10),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )

    # YouTube 분석 화면 컴포넌트
    def create_youtube_analyzer_view(user_data):
        # 헤더 섹션 (사용자 정보 및 로그아웃)
        header = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(
                        ft.icons.PLAY_CIRCLE_FILL_ROUNDED,
                        color=ft.colors.RED_600,
                        size=30,
                    ),
                    ft.Text(
                        "유튜브 중독자",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.RED_600,
                    ),
                    ft.Container(expand=True),
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(
                                            user_data.get("name", "사용자"),
                                            size=14,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        ft.Text(
                                            f"구독: {user_data.get('subscription_type', 'Free')}",
                                            size=12,
                                            color=ft.colors.GREY_700,
                                        ),
                                    ],
                                    spacing=2,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                                ft.CircleAvatar(
                                    foreground_image_url=user_data.get("picture", None),
                                    content=ft.Text(user_data.get("name", "")[:1]) if not user_data.get("picture") else None,
                                    radius=20,
                                ),
                                ft.IconButton(
                                    icon=ft.icons.LOGOUT,
                                    tooltip="로그아웃",
                                    on_click=handle_logout,
                                ),
                            ],
                            spacing=10,
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        padding=ft.padding.only(left=10),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.all(20),
            border_radius=ft.border_radius.only(
                bottom_left=10, bottom_right=10
            ),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_center,
                end=ft.alignment.bottom_center,
                colors=[ft.colors.GREY_50, ft.colors.WHITE],
            ),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=ft.colors.with_opacity(0.2, ft.colors.GREY_300),
                offset=ft.Offset(0, 5),
            ),
        )
        
        # URL 입력 필드
        url_field = ft.TextField(
            label="YouTube URL",
            hint_text="유튜브 주소를 복사해 넣으세요",
            prefix_icon=ft.icons.LINK,
            border_radius=10,
            expand=True,
            on_focus=lambda e: paste_from_clipboard(e, url_field),
        )

        # 질문 입력 필드
        question_field = ft.TextField(
            label="궁금한 내용을 질문하세요",
            hint_text="영상 내용에 대한 질문",
            prefix_icon=ft.icons.QUESTION_ANSWER,
            border_radius=10,
            expand=True,
        )
        
        # 썸네일 표시 영역
        thumbnail_display = ft.Container(
            content=ft.Image(
                src="https://picsum.photos/200/200?5",
                width=320,
                height=180,
                fit=ft.ImageFit.COVER,
                border_radius=ft.border_radius.all(10),
            ),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.colors.with_opacity(0.2, ft.colors.GREY_300),
                offset=ft.Offset(0, 2),
            ),
            border_radius=ft.border_radius.all(10),
            margin=ft.margin.only(top=10, bottom=10),
        )
        
        # 진행 표시줄
        progress_bar = ft.ProgressBar(width=320, visible=False, color=ft.colors.RED_500)
        
        # 답변 텍스트 영역
        answer_text = ft.Text("영상에서 추출한 내용이 여기에 표시됩니다", selectable=True,expand=True)
        
        scrollable_answer = ft.Container(
            content=ft.Column(
                [answer_text],
                scroll=ft.ScrollMode.ALWAYS,
                spacing=10,
                height=300,
                expand=True,
            ),
            border=ft.border.all(1, ft.colors.RED_300),
            border_radius=10,
            padding=10,
            expand=True,
            margin=ft.margin.only(top=15),
        )
        
        # 기능 버튼들
        action_buttons = ft.Row(
            [
                ft.ElevatedButton(
                    "썸네일 못참아!",
                    icon=ft.icons.IMAGE,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=10),
                        color=ft.colors.WHITE,
                        bgcolor=ft.colors.INDIGO_500,
                    ),
                ),
                ft.ElevatedButton(
                    "요약 아니고 정리",
                    icon=ft.icons.SUMMARIZE,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=10),
                        color=ft.colors.WHITE,
                        bgcolor=ft.colors.TEAL_500,
                    ),
                ),
                ft.ElevatedButton(
                    "지식백과[옵시디언 연동]",
                    icon=ft.icons.BOOK,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=10),
                        color=ft.colors.WHITE,
                        bgcolor=ft.colors.DEEP_PURPLE_500,
                    ),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        )
        
        # 전체 레이아웃
        return ft.Column(
            [
                header,
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Container(
                                content=ft.Column(
                                    [
                                        url_field,
                                        question_field,
                                        ft.Row(
                                            [thumbnail_display],
                                            alignment=ft.MainAxisAlignment.CENTER,
                                        ),
                                        progress_bar,
                                        action_buttons,
                                        scrollable_answer,
                                    ],
                                    spacing=15,
                                ),
                                padding=ft.padding.all(20),
                                border_radius=10,
                                bgcolor=ft.colors.WHITE,
                                shadow=ft.BoxShadow(
                                    spread_radius=1,
                                    blur_radius=15,
                                    color=ft.colors.with_opacity(0.1, ft.colors.BLACK),
                                    offset=ft.Offset(0, 5),
                                ),
                            ),
                        ],
                        spacing=20,
                    ),
                    padding=ft.padding.all(20),
                    expand=True,
                ),
            ],
            spacing=0,
            height=page.height,
        )

    # 클립보드 내용 붙여넣기
    async def paste_from_clipboard(e, field):
        clipboard_content = await page.get_clipboard()
        if clipboard_content and "youtube.com" in clipboard_content:
            field.value = clipboard_content
            page.update()

    # 로그인 처리 함수
    def on_login(e):
        if e.error:
            show_message(f"로그인 오류: {e.error}")
            return
        
        # Google 로그인 성공, Supabase와 연동
        try:
            # 사용자 정보 가져오기
            user_id = page.auth.user.id
            user_email = page.auth.user.get('email', '')
            user_name = page.auth.user.get('name', '')
            user_picture = page.auth.user.get('picture', '')
            
            user_data = {
                "user_id": user_id,
                "email": user_email,
                "name": user_name,
                "picture": user_picture,
                "subscription_type": "Free"  # 기본값
            }
            
            # Supabase에서 사용자 검색 (supabase가 초기화된 경우만)
            if supabase:
                try:
                    result = supabase.table("users").select("*").eq("user_id", user_id).execute()
                    
                    if not result.data:
                        # 신규 사용자 - Supabase에 추가
                        user_data_for_db = {
                            "user_id": user_id,
                            "email": user_email,
                            "name": user_name,
                            "picture": user_picture,
                            "subscription_type": "free",  # 기본값: 무료 사용자
                            "created_at": "now()"
                        }
                        supabase.table("users").insert(user_data_for_db).execute()
                        show_message(f"환영합니다! {user_name}님의 계정이 생성되었습니다.")
                    else:
                        # 기존 사용자
                        user_data = result.data[0]
                        show_message(f"{user_name}님, 다시 오신 것을 환영합니다!")
                except Exception as e:
                    print(f"Supabase 연동 오류: {e}")
                    show_message("사용자 데이터 처리 중 오류가 발생했습니다.")
            
            # 로그인 후 화면 전환
            page.clean()
            page.add(create_youtube_analyzer_view(user_data))
            
        except Exception as e:
            show_message(f"사용자 데이터 처리 중 오류 발생: {str(e)}")
    
    # 로그아웃 처리 함수
    def handle_logout(e):
        # 로컬 인증 상태 초기화
        try:
            page.logout()
            # 로그아웃 후 로그인 화면으로 전환
            page.clean()
            page.add(create_login_view())
            show_message("로그아웃되었습니다.")
        except Exception as e:
            show_message(f"로그아웃 중 오류 발생: {str(e)}")
    
    # 메시지 표시 헬퍼 함수
    def show_message(message):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            action="확인",
        )
        page.snack_bar.open = True
        page.update()
    
    # 페이지 이벤트 핸들러 설정
    page.on_login = on_login
    
    # 초기 화면 설정 (로그인 화면)
    page.add(create_login_view())

# 앱 실행
port = int(os.getenv("PORT", "8000"))
ft.app(main, port=port, view=ft.WEB_BROWSER,assets_dir="assets")
