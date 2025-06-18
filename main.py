import os       # - os: 파일 경로 등 시스템 관련 작업
import re       # - re: 정규표현식(채팅 필터링 등)
import json     # - json: OpenAI 응답 파싱용
from datetime import datetime       # - datetime: 오늘 날짜 포맷용
from fastapi import FastAPI, UploadFile, File, HTTPException        # - FastAPI: 웹 프레임워크 - UploadFile, File: 파일 업로드 처리 - HTTPException: 에러 응답 반환 시 사용
from pydantic import BaseModel      # Pydantic 모델 선언용 (입력 데이터 구조 정의에 필요)
from dotenv import load_dotenv      # .env 환경 변수 파일 로드를 위한 라이브러리
from openai import OpenAI       # OpenAI API를 사용하기 위한 클라이언트
# -- CORS 허용 (크로스 도메인 통신 허용) -- #
from fastapi.middleware.cors import CORSMiddleware


# .env 파일의 경로를 절대 경로로 명시
# - uvicorn처럼 별도 프로세스에서 실행할 때 상대경로 문제 방지 안했을때 집에서 됐던게 학교에선 안됐음..
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)        # 위에서 지정한 경로의 .env 파일을 로드 (환경 변수 설정)
print("✅ API 키 확인:", os.getenv("OPENAI_API_KEY"))   # 환경 변수가 제대로 로드되었는지 확인용 (디버깅) - .env 에 api 키 있는데 안불러와져서 확인차 작성

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))    # - 인증 실패 시 에러 발생 가능하므로 os.getenv()가 None이면 예외 처리 필요

# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI()  # - 이후 라우터(@app.get, @app.post 등)에서 사용함

# 기존 코드
# load_dotenv()
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# app = FastAPI()


#  요청 모델 정의
# FastAPI에서 사용자의 요청 데이터를 구조화하기 위해 Pydantic 모델을 사용
class DiaryRequest(BaseModel):
    kakao_text: str                         # 사용자로부터 전달받은 카카오톡 텍스트 데이터
    search_log: str | None = "없음"         # 선택적인 검색 기록 (기본값: "없음")
    user_prompt: str | None = None          # 사용자 정의 프롬프트 (선택적)
    use_prompt: bool = True                 # 프롬프트 사용 여부 (기본값: True)


#  오늘 날짜를 카카오톡 날짜 포맷에 맞게(예: 2025년 6월 17일) 반환하는 함수
def get_today_str_kakao():
    today = datetime.now()                                      # 현재 날짜 및 시간 객체 생성
    return f"{today.year}년 {today.month}월 {today.day}일"      # 카카오톡 형식에 맞춰 문자열로 반환

#  카카오톡 txt 파일에서 대화 내용만 추출하는 함수
# - 날짜 기준이 아닌 전체 텍스트 중 유효한 대화 메시지를 필터링함
def extract_today_chat(text: str, _: str = "") -> str:          
    lines = text.splitlines()         # 텍스트를 줄 단위로 나눔
    chat = []                         # 유효한 메시지를 저장할 리스트

    #  [이름] [오후 3:36] 메시지
    #  정규 표현식 정의: '[이름] [오전/오후 시:분] 메시지' 패턴 추출용
    msg = re.compile(r"^\[(.*?)\]\s*\[(오전|오후)\s*\d{1,2}:\d{2}\]\s*(.*)")

    for ln in lines:
        ln = ln.strip()     # 각 줄의 앞뒤 공백 제거
        matching = msg.match(ln)       # 정규표현식과 매칭 시도
        if matching:        
            msg_txt = matching.group(3).strip()     # 대화 내용만 추출 (이름/시간 제외)
            # 시스템 메시지나 불필요한 항목 필터링
            # 예: [사진], 이모티콘, 입장/퇴장 알림 등은 제외
            if not any(k in msg_txt for k in ["[사진]", "이모티콘", "님이 입장", "님이 나갔"]):
                chat.append(msg_txt)    # 유효한 메시지만 리스트에 추가하기

    return "\n".join(chat[-30:]) # 최근 메시지 30개만 추출하여 반환하기 (추후 변동 예정)


# ✅ 1. 카카오톡 txt 업로드 및 오늘 대화 미리보기.... Auto_diary로 대체
@app.post("/upload-kakao")
async def upload_kakao(file: UploadFile = File(...)):
    try:
        content = (await file.read()).decode("utf-8", errors="ignore")

        today_chat = extract_today_chat(content)

        print("총 메시지 줄 수:", len(content.splitlines()))
        print("추출된 대화 줄 수:", len(today_chat.splitlines()))
        print("미리보기 내용:\n", today_chat)

        return {
            "today_chat": today_chat,
            "length": len(today_chat)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ✅ 2. 요약 + 감정 분석 포함된 감성 일기 생성
@app.post("/generate-diary")
def generate_diary(data: DiaryRequest):
    """
    개선된 프롬프트 처리 로직을 사용하는 감성 일기 생성 엔드포인트
    """
    return generate_diary_with_prompt_handling(data)
    
@app.post("/auto-diary")
async def auto_diary(
    file: UploadFile = File(...), 
    search_log: str = "없음",
    user_prompt: str | None = None,
    use_prompt: bool = True
):
    """
    카카오톡 파일 업로드와 프롬프트 처리를 통합한 자동 일기 생성 엔드포인트
    """
    try:
        content = (await file.read()).decode("utf-8", errors="ignore")

        # 1단계: 카카오톡 대화 추출
        kakao_text = extract_today_chat(content)

        if not kakao_text.strip():
            raise HTTPException(status_code=400, detail="카카오톡 대화가 감지되지 않았습니다.")

        # 2단계: DiaryRequest 객체 생성하여 통합 처리
        diary_request = DiaryRequest(
            kakao_text=kakao_text,
            search_log=search_log,
            user_prompt=user_prompt,
            use_prompt=use_prompt
        )

        # 3단계: 개선된 프롬프트 처리 로직으로 일기 생성
        diary = generate_diary_with_prompt_handling(diary_request)
        diary["kakao_text"] = kakao_text

        return diary

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 프롬프트 충돌 감지 전용 엔드포인트
@app.post("/detect-conflict")
async def detect_conflict_endpoint(data: DiaryRequest):
    """
    사용자 프롬프트와 카카오톡 대화 내용 간의 충돌을 감지하는 엔드포인트
    """
    try:
        if not data.user_prompt:
            return {
                "has_conflict": False,
                "conflict_type": "none",
                "confidence": 0.0,
                "suggestion": "사용자 프롬프트가 없습니다."
            }
        
        conflict_info = detect_prompt_conflict(data.user_prompt, data.kakao_text)
        return conflict_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 프롬프트 기능 테스트용 엔드포인트
@app.get("/test-prompt-features")
async def test_prompt_features():
    """
    프롬프트 기능 테스트를 위한 샘플 데이터와 사용법을 제공하는 엔드포인트
    """
    return {
        "message": "프롬프트 기능이 성공적으로 구현되었습니다!",
        "features": {
            "user_prompt": "사용자 정의 프롬프트 입력 가능",
            "use_prompt": "프롬프트 사용 여부 선택 가능",
            "conflict_detection": "프롬프트와 대화 내용 충돌 감지",
            "endpoints": {
                "/generate-diary": "프롬프트 포함 일기 생성",
                "/auto-diary": "파일 업로드 + 프롬프트 처리",
                "/detect-conflict": "충돌 감지 전용"
            }
        },
        "sample_request": {
            "kakao_text": "오늘 친구와 좋은 대화를 나눴어요",
            "search_log": "없음",
            "user_prompt": "오늘은 정말 힘든 하루였어요",
            "use_prompt": True
        }
    }

## 아래는 아직 적용 안된코드들 ##


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 또는 Flutter 앱 도메인만 제한적으로
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 프롬프트와 대화 내용의 충돌을 감지하는 함수
def detect_prompt_conflict(user_prompt: str, kakao_text: str) -> dict:
    """
    사용자 프롬프트와 카카오톡 대화 내용 간의 충돌을 감지합니다.
    
    Returns:
        dict: {
            "has_conflict": bool,
            "conflict_type": str,
            "confidence": float,
            "suggestion": str
        }
    """
    if not user_prompt or not kakao_text:
        return {
            "has_conflict": False,
            "conflict_type": "none",
            "confidence": 0.0,
            "suggestion": "충돌 감지 불가"
        }
    
    # 충돌 감지를 위한 프롬프트
    conflict_detection_prompt = f"""
    사용자가 작성한 프롬프트와 카카오톡 대화 내용을 비교하여 충돌 여부를 분석해주세요.
    
    ### 사용자 프롬프트:
    {user_prompt}
    
    ### 카카오톡 대화 내용:
    {kakao_text}
    
    다음 JSON 형식으로만 응답하세요:
    {{
        "has_conflict": true/false,
        "conflict_type": "감정_충돌" | "상황_충돌" | "의도_충돌" | "none",
        "confidence": 0.0-1.0,
        "suggestion": "충돌 해결 방안 또는 설명"
    }}
    
    충돌 유형 설명:
    - 감정_충돌: 프롬프트의 감정과 대화의 감정이 반대
    - 상황_충돌: 프롬프트의 상황과 대화의 상황이 다름
    - 의도_충돌: 프롬프트의 의도와 대화의 맥락이 맞지 않음
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": conflict_detection_prompt}]
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        print(f"충돌 감지 중 오류: {e}")
        return {
            "has_conflict": False,
            "conflict_type": "error",
            "confidence": 0.0,
            "suggestion": "충돌 감지 실패"
        }

# 프롬프트 처리 로직을 개선한 일기 생성 함수
def generate_diary_with_prompt_handling(data: DiaryRequest) -> dict:
    """
    프롬프트 처리 로직이 포함된 개선된 일기 생성 함수
    """
    try:
        # 1단계: 요약 생성
        summary_prompt = f"""
        아래는 카카오톡 대화 내용입니다:
        ---
        {data.kakao_text}
        ---

        위 대화를 요약해줘. 감정 표현 없이 무슨 일이 있었는지 2~3문장으로 설명해줘.
        출력은 반드시 다음 JSON 형식을 따르세요:
        {{
          "summary": "..."
        }}
        """

        summary_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": summary_prompt}]
        )
        summary = json.loads(summary_response.choices[0].message.content)["summary"]

        # 2단계: 프롬프트 충돌 감지 (프롬프트가 있는 경우)
        conflict_info = None
        if data.user_prompt and data.use_prompt:
            conflict_info = detect_prompt_conflict(data.user_prompt, data.kakao_text)
            print(f"🔍 충돌 감지 결과: {conflict_info}")

        # 3단계: 감성 일기 생성 (프롬프트 처리 로직 포함)
        if data.use_prompt and data.user_prompt:
            # 사용자 프롬프트를 사용하는 경우
            diary_prompt = f"""
            ### 입력 정보
            - 검색기록: {data.search_log}
            - 카카오톡 대화: {data.kakao_text}
            - 요약: {summary}
            - 사용자 프롬프트: {data.user_prompt}
            {f"- 충돌 감지: {conflict_info['conflict_type']} (신뢰도: {conflict_info['confidence']:.2f})" if conflict_info and conflict_info['has_conflict'] else ""}

            ### 지시사항
            1) 사용자 프롬프트를 우선적으로 고려하되, 카카오톡 대화 내용과의 일관성을 유지하세요.
            2) 충돌이 감지된 경우, 대화 내용을 기반으로 하되 사용자 의도를 최대한 반영하세요.
            3) 아래 JSON **구조** 그대로 채워서 출력하세요(필드명 변경 금지).
            4) 각 항목은 2~3문장 이상, 따뜻하고 진심 어린 말로 작성하세요.

            {{
              "상황설명": "...",
              "감정표현": "...",
              "공감과인정": "...",
              "따뜻한위로": "...",
              "실용적제안": "..."
            }}
            """
        else:
            # 프롬프트 없이 대화만으로 일기 생성
            diary_prompt = f"""
            ### 입력 정보
            - 검색기록: {data.search_log}
            - 카카오톡 대화: {data.kakao_text}
            - 요약: {summary}

            ### 지시사항
            1) 사용자 대화에는 감정이 숨겨져 있을 수 있으므로, 상황의 흐름과 말투에서 감정을 섬세하게 추론하세요.
            2) 아래 JSON **구조** 그대로 채워서 출력하세요(필드명 변경 금지).
            3) 각 항목은 2~3문장 이상, 따뜻하고 진심 어린 말로 작성하세요.
            4) 외국어, 욕설이 있어도 무시하지 말고 감정을 정확히 해석하세요.

            {{
              "상황설명": "...",
              "감정표현": "...",
              "공감과인정": "...",
              "따뜻한위로": "...",
              "실용적제안": "..."
            }}
            """

        diary_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 감성적인 작가이자 상담가입니다. 주어진 정보로 감정 분석과 위로의 말을 작성해주세요. 반드시 JSON으로 응답하세요."},
                {"role": "user", "content": diary_prompt}
            ]
        )

        diary = json.loads(diary_response.choices[0].message.content)
        diary["summary"] = summary
        
        # 충돌 정보 추가
        if conflict_info:
            diary["conflict_info"] = conflict_info

        return diary

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))