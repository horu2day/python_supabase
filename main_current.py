import os
import io
import re  # 추가: 정규 표현식 모듈
import flet as ft

from flet.auth.providers import GoogleOAuthProvider
from youtube_transcript_api import YouTubeTranscriptApi
from supabase import create_client, Client
import google.generativeai as genai

from PIL import Image
import requests


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




# Gemini Pro Vision 모델 선택
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp",
    # model_name="gemini-2.0-flash-thinking-exp-01-21",
    generation_config=generation_config,
)

def extract_korean_text_from_image_url(image_url):
    """
    이미지 URL에서 한국어 문장을 추출합니다.

    Args:
        image_url: 이미지 URL

    Returns:
        추출된 한국어 문장 (문장이 없으면 빈 문자열)
    """
    try:
        # 이미지 다운로드
        response = requests.get(image_url, stream=True)
        response.raise_for_status()  # 오류 발생 시 예외 발생

        # 이미지 로드
        image = Image.open(io.BytesIO(response.content))

        # Gemini Pro Vision 모델에 이미지와 프롬프트 전달
        prompt_parts = [
            "이 이미지에서 한국어 문장을 추출해줘. 만약 한국어 문장이 없다면 아무것도 출력하지 마.",
            image
        ]
        response = model.generate_content(prompt_parts, stream=False)  # 추가

        # 결과 추출 및 반환
        text = response.text
        return text.strip()

    except requests.exceptions.RequestException as e:
        print(f"이미지 다운로드 오류: {e}")
        return ""
    except Exception as e:
        print(f"오류 발생: {e}")
        return ""

    except requests.exceptions.RequestException as e:
        print(f"이미지 다운로드 오류: {e}")
        return "", None
    except Exception as e:
        print(f"오류 발생: {e}")
        return "", None
    
def generate_question(extracted_text, transcript, question=None):
    """
    추출된 문장에서 질문을 만들고, transcript에서 답을 찾아 Concise하게 답변합니다.
    markdown 형식 으로 답변을 반환합니다.
    Args:
      extracted_text: 추출된 문장
      transcript: 답변을 찾을 transcript 내용
      question: 수정된 질문 (선택적)

    Returns:
      생성된 질문, 답, 또는 None (질문 생성 실패 시)
    """
    try:
        if question:  # 수정된 질문이 있으면 그대로 사용
            question_text = question
        else:
            # 질문 생성 프롬프트
            question_prompt = f"""
            주어진 문장: "{extracted_text}"

            위 문장에서 사람들이 가장 궁금해할 만한 핵심 질문을 하나 만들어줘.
            질문은 한국어로 작성하고, 간결하게 만들어줘.
            """
            
            question_response = model.generate_content(
                question_prompt, stream=False)  # 추가

            question_text = question_response.text.strip()

        return question_text
    except Exception as e:
        print(f"오류 발생: {e}")
        return None


def main(page: ft.Page):
    # 페이지 속성 설정
    page.title = "유튜브 중독자 로그인"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    

    extracted_text_data = ""
    transcript_data = ""

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

    # # 테스트용 자동 로그인 기능
    # def auto_login_for_testing():
    #     # 테스트용 사용자 데이터
    #     user_data = {
    #         "user_id": "test123",
    #         "name": "테스트 사용자",
    #         "email": "test@example.com",
    #         "picture": None,
    #         "subscription_type": "Free"
    #     }
        
    #     # 직접 메인 화면으로 전환
    #     page.clean()
    #     page.add(create_youtube_analyzer_view(user_data))
    #     page.update()
    
    # 테스트/디버그 모드 - 자동 로그인을 원하면 아래 주석을 해제
    #page.add(ft.ElevatedButton("테스트 모드: 자동 로그인", on_click=lambda _: auto_login_for_testing()))
    


    # Google OAuth 제공자 설정
    provider = GoogleOAuthProvider(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        #redirect_url="http://localhost:8000/api/oauth/redirect", 
        redirect_url="https://auth4flet.fly.dev/oauth_callback", 
        
    )
    ########### 여기부터 로직 추가###################
    # def extract_info(e):
    #     nonlocal url_field, extracted_text_data, transcript_data, thumbnail_display
    #     progress_bar.visible = True  # Hide progress bar
    #     url = url_field.value

    #     video_id = url.split('v=')[1]
    #     question_text = question_field.value 
    #     if '&' in video_id:
    #         video_id = video_id.split('&')[0]

    #     try:
    #         progress_bar.value=0.3
    #         answer_text.value = "30 : 유튜브 내용을 추출하였습니다. "
    #         page.update()  # UI 업데이트

    #         markdown_result, answer = generate_answer(
    #             question_text, transcript_data)
    #         progress_bar.value=0.5
    #         answer_text.value = "70: 답변을 생성하였습니다."
    #         page.update()  # UI 업데이트

    #         # 수정: markdown 결과 받기
    #         if markdown_result:
    #             # 추가로 구현해야 함.
    #             # filename = save_markdown_file(
    #             #     markdown_result, url, "question_answer")  # 추가: 마크다운 파일 저장
    #             # progress_bar.value=0.8
    #             # answer_text.value = "80: 답변을 저장하였습니다."
    #             # page.update()  # UI 업데이트

    #             answer_text.value = markdown_result  # 수정: 마크다운 결과 출력
    #             page.overlay.append(
    #                 ft.SnackBar(
    #                     ft.Text("답변 완료."), open=True))
    #         else:
    #             answer_text.value = "질문/답변 생성 실패"

    #         progress_bar.value=1.0
    #         answer_text.value = f"{answer}"
    #         page.update()  # UI 업데이트
    #     except Exception as e:
    #         answer_text.value =f"오류: {e}"
    #         page.update()
    
    
    # def generate_answer(question_text, transcript, question=None):
    #     """
    #     transcript에서 답을 찾아 Concise하게 답변합니다.
    #     markdown 형식 으로 답변을 반환합니다.
    #     Args:
    #     extracted_text: 추출된 문장
    #     transcript: 답변을 찾을 transcript 내용
    #     question: 수정된 질문 (선택적)

    #     Returns:
    #     생성된 질문, 답, 또는 None (질문 생성 실패 시)
    #     """
    #     try:
    #         # 답변 찾기 프롬프트
    #         answer_prompt = f"""
    #         질문: "{question_text}"
    #         Transcript: "{transcript}"

    #         위 질문에 대한 답을 Transcript에서 찾아서 한국어로 알려줘.
    #         답변은 Concise하게 작성하고, 만약 답을 찾을 수 없다면 "답변을 찾을 수 없습니다." 라고 출력해줘.
    #         """
    #         answer_response = model.generate_content(
    #             answer_prompt, stream=False)  # 추가
    #         answer = answer_response.text.strip()

    #         # Markdown 형식으로 결과 반환
    #         markdown_result = f"## 질문\n{question_text}\n\n## 답변\n{answer}"
    #         return markdown_result, answer

    #     except Exception as e:
    #         print(f"오류 발생: {e}")
    #         return None, None
    def on_change(e):
        # 정규 표현식을 사용하여 유튜브 URL 패턴 감지
        youtube_regex = (
            r'(https?://)?(www\.)?'
            r'(youtube|youtu)\.(com|be)/'
            r'(watch\?v=|embed/|shorts/|v/)?([\w-]+)(&.*)?'
        )
        match = re.search(youtube_regex, url_field.value)
        if match:
            print("유튜브 URL 감지!")
            # 여기에 유튜브 URL 처리 함수 호출 (예: youtube_url_handler(match.group(6)))
            youtube_url_handler(match.group(6)) # 비디오 ID 추출하여 함수에 전달
        else:
            print("유튜브 URL 아님")

    def youtube_url_handler(video_id):
        nonlocal extracted_text_data, transcript_data, thumbnail_display
        progress_bar.visible = True  # Hide progress bar

        if '&' in video_id:
            video_id = video_id.split('&')[0]

        # 썸네일 URL 생성
        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
        extracted_text = extract_korean_text_from_image_url(thumbnail_url)
        extracted_text_data = extracted_text
        if extracted_text:
            print(f"추출된 한국어 문장:\n{extracted_text}")
        else:
            print("이미지에서 한국어 문장을 찾을 수 없습니다.")
        thumbnail_display.content.src = thumbnail_url
        
        thumbnail_display.update()  # 이미지 업데이트
        try:

            transcript = YouTubeTranscriptApi.get_transcript(
                video_id, languages=['ko', 'en'])
            transcript_data = transcript
            progress_bar.value=0.3
            answer_text.value = "30 : 유튜브 내용을 추출하였습니다. "
            page.update()  # UI 업데이트

            question = generate_question(
                extracted_text, transcript)
            progress_bar.value=0.5
            answer_text.value = "50: 질문을 생성하고 답변을 가져옵니다."
            question_field.value = question
            page.update()  # UI 업데이트
        except Exception as e:
            question_field.value = f"오류: {e}"            
    ##################################################
    # URL 입력 필드
    url_field = ft.TextField(
        label="YouTube URL",
        hint_text="유튜브 주소를 복사해 넣으세요",
        prefix_icon=ft.icons.LINK,
        border_radius=10,
        expand=True,
        on_change=on_change ,
    )
    # 질문 입력 필드
    question_field = ft.TextField(
        label="궁금한 내용을 질문하세요",
        hint_text="영상 내용에 대한 질문",
        prefix_icon=ft.icons.QUESTION_ANSWER,
        border_radius=10,
        expand=True,
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
                # on_click=extract_info
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
    

    #scrollable_answer = None
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




# if __name__ == "__main__":
#     port = int(os.getenv("PORT", "8000"))
#     ft.app(main, port=port, view=ft.WEB_BROWSER,assets_dir="assets")
# 앱 실행
port = int(os.getenv("PORT", "8000"))
ft.app(main, port=port, view=ft.WEB_BROWSER)