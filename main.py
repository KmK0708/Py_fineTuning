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

# 카카오톡 대화를 날짜별로 구분하여 추출하는 함수
def extract_chat_by_date(text: str, target_date: str | None = None) -> dict:
    """
    카카오톡 대화를 날짜별로 구분하여 추출합니다.
    
    Args:
        text: 카카오톡 txt 파일 내용
        target_date: 특정 날짜 (예: "20일", "19일"). None이면 모든 날짜 반환
    
    Returns:
        dict: {
            "20일": ["메시지1", "메시지2", ...],
            "19일": ["메시지1", "메시지2", ...],
            ...
        }
    """
    lines = text.splitlines()
    chat_by_date = {}  # 날짜별 대화 저장
    current_date = None
    
    # 날짜 패턴: "2025년 1월 20일" 또는 "1월 20일" 형식
    date_pattern = re.compile(r"(\d{4}년\s*)?(\d{1,2}월\s*\d{1,2}일)")
    # 메시지 패턴: [이름] [오전/오후 시:분] 메시지
    msg_pattern = re.compile(r"^\[(.*?)\]\s*\[(오전|오후)\s*\d{1,2}:\d{2}\]\s*(.*)")
    
    for line in lines:
        line = line.strip()
        
        # 날짜 라인인지 확인
        date_match = date_pattern.search(line)
        if date_match:
            # 날짜 추출 (예: "20일" 형태로 변환)
            date_str = date_match.group(2)  # "1월 20일"
            day_match = re.search(r"(\d{1,2})일", date_str)
            if day_match:
                current_date = day_match.group(1) + "일"
                if current_date not in chat_by_date:
                    chat_by_date[current_date] = []
            continue
        
        # 메시지 라인인지 확인
        msg_match = msg_pattern.match(line)
        if msg_match and current_date:
            msg_txt = msg_match.group(3).strip()
            # 시스템 메시지 필터링
            if not any(k in msg_txt for k in ["[사진]", "이모티콘", "님이 입장", "님이 나갔"]):
                chat_by_date[current_date].append(msg_txt)
    
    # 특정 날짜만 요청한 경우
    if target_date:
        return {target_date: chat_by_date.get(target_date, [])}
    
    return chat_by_date

# 특정 날짜의 대화를 문자열로 변환하는 함수
def get_chat_for_date(chat_by_date: dict, target_date: str) -> str:
    """
    특정 날짜의 대화를 문자열로 변환합니다.
    
    Args:
        chat_by_date: 날짜별 대화 딕셔너리
        target_date: 원하는 날짜 (예: "20일")
    
    Returns:
        str: 해당 날짜의 대화 내용
    """
    if target_date in chat_by_date:
        return "\n".join(chat_by_date[target_date])
    return ""

# 날짜별 이벤트 분석 함수
def analyze_events_by_date(chat_by_date: dict) -> dict:
    """
    각 날짜별로 이벤트를 분석합니다.
    
    Args:
        chat_by_date: 날짜별 대화 딕셔너리
    
    Returns:
        dict: 날짜별 이벤트 분석 결과
    """
    events_by_date = {}
    
    for date, messages in chat_by_date.items():
        if not messages:  # 메시지가 없으면 건너뛰기
            continue
            
        chat_text = "\n".join(messages)
        
        # 이벤트 분석 프롬프트
        event_analysis_prompt = f"""
        아래는 {date}의 카카오톡 대화 내용입니다:
        ---
        {chat_text}
        ---
        
        이 대화에서 어떤 주요 이벤트나 일이 있었는지 분석해주세요.
        다음 JSON 형식으로만 응답하세요:
        {{
            "date": "{date}",
            "events": ["이벤트1", "이벤트2", "이벤트3"],
            "summary": "해당 날짜의 주요 일정 요약 (2-3문장)",
            "emotion": "전체적인 감정 분위기 (긍정/부정/중립)"
        }}
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": event_analysis_prompt}]
            )
            
            content = response.choices[0].message.content
            if content is None:
                raise ValueError("API 응답이 비어있습니다")
                
            result = json.loads(content)
            events_by_date[date] = result
            
        except Exception as e:
            print(f"📅 {date} 이벤트 분석 중 오류: {e}")
            events_by_date[date] = {
                "date": date,
                "events": [],
                "summary": "분석 실패",
                "emotion": "알 수 없음"
            }
    
    return events_by_date

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
        
        content = response.choices[0].message.content
        if content is None:
            raise ValueError("API 응답이 비어있습니다")
            
        result = json.loads(content)
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
        
        summary_content = summary_response.choices[0].message.content
        if summary_content is None:
            raise ValueError("요약 API 응답이 비어있습니다")
            
        summary = json.loads(summary_content)["summary"]

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

        diary_content = diary_response.choices[0].message.content
        if diary_content is None:
            raise ValueError("일기 생성 API 응답이 비어있습니다")
            
        diary = json.loads(diary_content)
        diary["summary"] = summary
        
        # 충돌 정보 추가
        if conflict_info:
            diary["conflict_info"] = conflict_info

        return diary

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    use_prompt: bool = True,
    use_date_analysis: bool = False,  # 날짜별 분석 사용 여부
    target_date: str | None = None    # 특정 날짜 (use_date_analysis가 True일 때)
):
    """
    카카오톡 파일 업로드와 프롬프트 처리를 통합한 자동 일기 생성 엔드포인트
    날짜별 분석 옵션 추가
    """
    try:
        content = (await file.read()).decode("utf-8", errors="ignore")

        if use_date_analysis:
            # 날짜별 분석 모드
            chat_by_date = extract_chat_by_date(content, target_date)
            
            if not chat_by_date:
                raise HTTPException(status_code=400, detail="날짜별 대화가 감지되지 않았습니다.")
            
            # 특정 날짜가 지정되지 않았으면 가장 최근 날짜 사용
            if target_date is None:
                available_dates = list(chat_by_date.keys())
                if available_dates:
                    target_date = available_dates[-1]  # 가장 최근 날짜
                else:
                    raise HTTPException(status_code=400, detail="유효한 날짜가 없습니다.")
            
            # 해당 날짜의 대화 내용
            if target_date is not None:
                kakao_text = get_chat_for_date(chat_by_date, target_date)
            else:
                raise HTTPException(status_code=400, detail="유효한 날짜가 없습니다.")
            
            if not kakao_text.strip():
                raise HTTPException(status_code=400, detail=f"{target_date}에 유효한 대화가 없습니다.")
                
        else:
            # 기존 방식 (최근 30줄)
            kakao_text = extract_today_chat(content)
            target_date = None

        if not kakao_text.strip():
            raise HTTPException(status_code=400, detail="카카오톡 대화가 감지되지 않았습니다.")

        # DiaryRequest 객체 생성하여 통합 처리
        diary_request = DiaryRequest(
            kakao_text=kakao_text,
            search_log=search_log,
            user_prompt=user_prompt,
            use_prompt=use_prompt
        )

        # 개선된 프롬프트 처리 로직으로 일기 생성
        diary = generate_diary_with_prompt_handling(diary_request)
        diary["kakao_text"] = kakao_text
        
        # 날짜 정보 추가
        if target_date:
            diary["target_date"] = target_date

        return diary

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 날짜별 대화 분석 엔드포인트
@app.post("/analyze-by-date")
async def analyze_by_date(
    file: UploadFile = File(...),
    target_date: str | None = None
):
    """
    카카오톡 대화를 날짜별로 분석하는 엔드포인트
    
    Args:
        file: 카카오톡 txt 파일
        target_date: 특정 날짜 (예: "20일"). None이면 모든 날짜 분석
    """
    try:
        content = (await file.read()).decode("utf-8", errors="ignore")
        
        # 날짜별 대화 추출
        chat_by_date = extract_chat_by_date(content, target_date)
        
        if not chat_by_date:
            raise HTTPException(status_code=400, detail="날짜별 대화가 감지되지 않았습니다.")
        
        # 날짜별 이벤트 분석
        events_by_date = analyze_events_by_date(chat_by_date)
        
        return {
            "chat_by_date": chat_by_date,
            "events_by_date": events_by_date,
            "available_dates": list(chat_by_date.keys())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 특정 날짜의 감성 일기 생성 엔드포인트
@app.post("/diary-by-date")
async def diary_by_date(
    file: UploadFile = File(...),
    target_date: str = "20일",  # 기본값으로 최근 날짜
    search_log: str = "없음",
    user_prompt: str | None = None,
    use_prompt: bool = True
):
    """
    특정 날짜의 대화를 기반으로 감성 일기를 생성하는 엔드포인트
    """
    try:
        content = (await file.read()).decode("utf-8", errors="ignore")
        
        # 특정 날짜의 대화만 추출
        chat_by_date = extract_chat_by_date(content, target_date)
        
        if not chat_by_date or target_date not in chat_by_date:
            raise HTTPException(status_code=400, detail=f"{target_date}의 대화가 감지되지 않았습니다.")
        
        # 해당 날짜의 대화 내용
        if target_date is not None:
            kakao_text = get_chat_for_date(chat_by_date, target_date)
        else:
            raise HTTPException(status_code=400, detail="유효한 날짜가 없습니다.")
        
        if not kakao_text.strip():
            raise HTTPException(status_code=400, detail=f"{target_date}에 유효한 대화가 없습니다.")
        
        # DiaryRequest 객체 생성
        diary_request = DiaryRequest(
            kakao_text=kakao_text,
            search_log=search_log,
            user_prompt=user_prompt,
            use_prompt=use_prompt
        )
        
        # 감성 일기 생성
        diary = generate_diary_with_prompt_handling(diary_request)
        diary["target_date"] = target_date
        diary["kakao_text"] = kakao_text
        
        return diary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 날짜별 분석 기능 테스트 엔드포인트
@app.get("/test-date-analysis")
async def test_date_analysis():
    """
    날짜별 분석 기능 테스트를 위한 정보 제공 엔드포인트
    """
    return {
        "message": "날짜별 분석 기능이 성공적으로 구현되었습니다!",
        "features": {
            "extract_chat_by_date": "카카오톡 대화를 날짜별로 구분",
            "analyze_events_by_date": "각 날짜별 이벤트 분석",
            "diary_by_date": "특정 날짜의 감성 일기 생성"
        },
        "endpoints": {
            "/analyze-by-date": "날짜별 대화 분석",
            "/diary-by-date": "특정 날짜의 감성 일기 생성",
            "/auto-diary": "기존 기능 + 날짜별 분석 옵션"
        },
        "usage": {
            "use_date_analysis": "true로 설정하면 날짜별 분석 사용",
            "target_date": "특정 날짜 지정 (예: '20일', '19일')",
            "available_dates": "파일에서 감지된 모든 날짜 목록"
        }
    }

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 또는 Flutter 앱 도메인만 제한적으로
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
) 