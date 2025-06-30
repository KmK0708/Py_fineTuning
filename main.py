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
from fastapi.responses import ORJSONResponse


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
        
        # 이벤트 분석 프롬프트 (Few-Shot 예시 추가)
        event_analysis_prompt = f"""
        아래 카카오톡 대화에서 어떤 주요 이벤트나 일이 있었는지 분석해주세요.

        ### 분석 규칙
        1. 대화 내용을 기반으로 사실에 입각하여 분석합니다.
        2. 주요 이벤트는 3-5개 키워드나 짧은 구문으로 요약합니다.
        3. 전체적인 감정 분위기는 "긍정", "부정", "중립" 중 하나로 명확히 판단합니다.

        ### 예시
        ---
        #### 입력
        - 대화 내용: "오늘 팀 프로젝트 회의 길어져서 힘들었어. 저녁은 치킨 먹고 힘냄. 내일은 발표 준비해야지."

        #### 출력
        {{
            "date": "해당 날짜",
            "events": ["팀 프로젝트 회의", "저녁 치킨", "발표 준비"],
            "summary": "팀 프로젝트 회의가 길어져 피로감을 느꼈으나, 저녁으로 치킨을 먹으며 기운을 회복했습니다. 다음 날 있을 발표 준비에 대한 계획을 세웠습니다.",
            "emotion": "중립"
        }}
        ---
        
        ### 실제 분석
        이제 아래 대화 내용을 바탕으로 위 규칙과 예시를 따라 분석해주세요.

        #### 입력
        - 대화 내용: {chat_text}

        #### 출력 (이 JSON 형식만 생성하세요)
        {{
            "date": "{date}",
            "events": [],
            "summary": "",
            "emotion": ""
        }}
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",  # 더 강력한 모델로 변경
                messages=[{"role": "user", "content": event_analysis_prompt}],
                temperature=0.2 # 일관성을 위해 temperature 낮춤
            )
            
            content = response.choices[0].message.content
            if content is None:
                raise ValueError("API 응답이 비어있습니다")

            try:
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                result = json.loads(content)
            except json.JSONDecodeError as e:
                print(f"--- ❌ 날짜({date}) 이벤트 JSON 파싱 오류 ---")
                print(f"오류: {e}")
                print(f"원본 API 응답:\n```\n{content}\n```")
                print("--------------------")
                raise HTTPException(status_code=500, detail=f"날짜({date}) 이벤트 API 응답 파싱 실패: {e}")
            
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
        # 1단계: 요약 생성 (더 구체적인 프롬프트)
        summary_prompt = f"""
        아래 카카오톡 대화를 분석하여 객관적이고 일관된 요약을 작성하세요.

        대화 내용:
        {data.kakao_text}

        요약 작성 규칙:
        1. 감정 표현 없이 사실만 기술
        2. 주요 주제 1-2개 중심으로 요약
        3. 2-3문장으로 제한
        4. 구체적인 사건이나 활동 위주로 작성

        다음 JSON 형식으로만 응답하세요:
        {{
          "summary": "구체적인 사건이나 활동을 중심으로 한 객관적 요약"
        }}
        """

        summary_response = client.chat.completions.create(
            model="gpt-4o",  # 더 강력한 모델로 변경
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0.2  # 일관성을 위해 temperature 더 낮춤
        )
        
        summary_content = summary_response.choices[0].message.content
        if summary_content is None:
            raise ValueError("요약 API 응답이 비어있습니다")
        
        try:
            # AI 응답에서 순수 JSON만 추출
            if "```json" in summary_content:
                summary_content = summary_content.split("```json")[1].split("```")[0].strip()
            
            if not summary_content.startswith('{'):
                # 응답이 JSON 형식이 아니면, AI가 요약만 텍스트로 보냈다고 가정
                summary = summary_content
            else:
                summary = json.loads(summary_content)["summary"]

        except json.JSONDecodeError as e:
            print("--- ❌ 요약 JSON 파싱 오류 ---")
            print(f"오류: {e}")
            print("원본 요약 API 응답:")
            print(f"```\n{summary_content}\n```")
            print("--------------------")
            # 파싱 실패 시, 원본 텍스트를 요약으로 사용
            summary = summary_content if summary_content else "요약 생성 실패"
        except (KeyError, IndexError):
             # "summary" 키가 없는 경우, 원본 텍스트를 요약으로 사용
            summary = summary_content

        # 2단계: 프롬프트 충돌 감지 (프롬프트가 있는 경우)
        conflict_info = None
        if data.user_prompt and data.use_prompt:
            conflict_info = detect_prompt_conflict(data.user_prompt, data.kakao_text)
            print(f"🔍 충돌 감지 결과: {conflict_info}")

        # 3단계: 감성 일기 생성 (Few-Shot 예시 추가)
        diary_prompt = f"""
        당신은 카카오톡 대화를 분석하여, 주어진 규칙과 예시에 따라 일관된 감성 일기를 작성하는 전문가입니다.

        ### 작성 규칙
        1. 대화 내용을 객관적으로 분석하여 일관된 해석을 제공해야 합니다.
        2. 감정은 대화의 맥락과 말투에서 추론하되, 과도한 추측은 지양해야 합니다.
        3. 각 섹션은 명확한 역할과 구조를 가져야 하며, 2-3 문장으로 작성해야 합니다.
        4. 사용자 의도가 있다면 최우선으로 고려하되, 대화 내용과의 일관성을 유지해야 합니다.

        ### 예시 (이 구조와 스타일을 반드시 따르세요)
        ---
        #### 입력
        - 대화 내용: "친구랑 영화보러 갔어. 완전 재밌었음! 근데 팝콘 너무 비싸더라 ㅠㅠ"
        - 요약: "친구와 함께 영화를 관람했으며, 영화는 재미있었지만 팝콘 가격에 대한 아쉬움을 표현함."
        - 사용자 의도: 없음
        - 검색 기록: "주변 영화관"

        #### 출력
        {{
          "상황설명": "친구와 함께 영화관에 방문하여 영화를 관람했습니다. 영화 자체는 매우 재미있게 즐겼지만, 매점에서 판매하는 팝콘의 가격이 예상보다 비싸다고 느꼈습니다.",
          "감정표현": "영화에 대한 즐거움과 긍정적인 감정이 주를 이루고 있습니다. 동시에, 팝콘 가격에 대해서는 아쉬움과 약간의 불만 섞인 감정이 드러납니다.",
          "공감과인정": "영화를 보며 즐거운 시간을 보내셨군요! 재미있는 영화는 하루를 특별하게 만들어주죠. 하지만 비싼 팝콘 가격에 아쉬움을 느끼는 마음도 충분히 이해됩니다.",
          "따뜻한위로": "즐거운 경험에 작은 아쉬움이 더해져 속상하셨겠어요. 그래도 영화가 재미있었다니 정말 다행이에요. 그 즐거운 기억에 더 집중해보는 건 어떨까요?",
          "실용적제안": "다음에는 영화관에 가기 전에 미리 간식을 준비하거나, 통신사 할인 등 팝콘을 저렴하게 구매할 수 있는 팁을 찾아보는 것도 좋은 방법이 될 수 있습니다."
        }}
        ---

        ### 실제 작성
        이제 아래 정보를 바탕으로 위 규칙과 예시를 따라 실제 일기를 작성해주세요.

        #### 입력
        - 대화 내용: {data.kakao_text}
        - 요약: {summary}
        - 사용자 의도: {data.user_prompt if data.use_prompt and data.user_prompt else "없음"}
        - 검색 기록: {data.search_log}
        {f"- 충돌 감지: {conflict_info['conflict_type']} (신뢰도: {conflict_info['confidence']:.2f})" if conflict_info and conflict_info['has_conflict'] else ""}

        #### 출력 (이 JSON 형식만 생성하세요)
        {{
            "상황설명": "",
            "감정표현": "",
            "공감과인정": "",
            "따뜻한위로": "",
            "실용적제안": ""
        }}
        """

        diary_response = client.chat.completions.create(
            model="gpt-4o",  # 더 강력한 모델로 변경
            messages=[
                {"role": "user", "content": diary_prompt}
            ],
            temperature=0.2,  # 일관성을 위해 temperature 더 낮춤
            max_tokens=1500
        )

        diary_content = diary_response.choices[0].message.content
        if diary_content is None:
            raise ValueError("일기 생성 API 응답이 비어있습니다")

        try:
            # AI 응답에서 순수 JSON만 추출 (가끔 ```json ... ``` 형식으로 감싸서 옴)
            if "```json" in diary_content:
                diary_content = diary_content.split("```json")[1].split("```")[0].strip()
            
            # 중괄호가 누락된 경우를 대비한 처리
            if not diary_content.startswith('{'):
                diary_content = '{' + diary_content
            if not diary_content.endswith('}'):
                # 가장 마지막 '}'를 찾아 그 이후를 자름
                last_brace_index = diary_content.rfind('}')
                if last_brace_index != -1:
                    diary_content = diary_content[:last_brace_index+1]

            diary = json.loads(diary_content)
        except json.JSONDecodeError as e:
            print("--- ❌ JSON 파싱 오류 ---")
            print(f"오류: {e}")
            print("원본 API 응답:")
            print(f"```\n{diary_content}\n```")
            print("--------------------")
            raise HTTPException(status_code=500, detail=f"API 응답 파싱 실패: {e}")

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
    diary = generate_diary_with_prompt_handling(data)
    return ORJSONResponse(content=diary)
    
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

        return ORJSONResponse(content=diary)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 일관성 테스트를 위한 함수들
def run_consistency_test(kakao_text: str, test_count: int = 5) -> dict:
    """
    동일한 입력에 대해 여러 번 테스트하여 일관성을 검증합니다.
    
    Args:
        kakao_text: 테스트할 카카오톡 대화 내용
        test_count: 테스트 횟수 (기본값: 5)
    
    Returns:
        dict: 일관성 테스트 결과
    """
    results = []
    
    print(f"🔄 일관성 테스트 시작: {test_count}회 실행")
    
    for i in range(test_count):
        try:
            # DiaryRequest 객체 생성
            diary_request = DiaryRequest(
                kakao_text=kakao_text,
                search_log="일관성 테스트용",
                user_prompt=None,
                use_prompt=False  # 프롬프트 없이 순수 대화만으로 테스트
            )
            
            # 일기 생성
            result = generate_diary_with_prompt_handling(diary_request)
            results.append({
                "test_number": i + 1,
                "summary": result.get("summary", ""),
                "situation": result.get("상황설명", ""),
                "emotion": result.get("감정표현", ""),
                "comfort": result.get("따뜻한위로", ""),
                "suggestion": result.get("실용적제안", ""),
                "empathy": result.get("공감과인정", "")
            })
            
            print(f"✅ 테스트 {i+1}/{test_count} 완료")
            
        except Exception as e:
            print(f"❌ 테스트 {i+1} 실패: {e}")
            results.append({
                "test_number": i + 1,
                "error": str(e)
            })
    
    return analyze_consistency(results)

def analyze_consistency(results: list) -> dict:
    """
    테스트 결과들의 일관성을 분석합니다.
    
    Args:
        results: 테스트 결과 리스트
    
    Returns:
        dict: 일관성 분석 결과
    """
    if not results:
        return {"error": "테스트 결과가 없습니다."}
    
    # 성공한 테스트만 필터링
    successful_results = [r for r in results if "error" not in r]
    
    if len(successful_results) < 2:
        return {
            "total_tests": len(results),
            "successful_tests": len(successful_results),
            "consistency_score": 0.0,
            "message": "성공한 테스트가 부족하여 일관성을 분석할 수 없습니다.",
            "results": results
        }
    
    # 각 섹션별 유사도 계산
    sections = {
        "summary": [r["summary"] for r in successful_results],
        "situation": [r["situation"] for r in successful_results],
        "emotion": [r["emotion"] for r in successful_results],
        "empathy": [r["empathy"] for r in successful_results],
        "comfort": [r["comfort"] for r in successful_results],
        "suggestion": [r["suggestion"] for r in successful_results]
    }
    
    section_similarities = {}
    for section_name, texts in sections.items():
        section_similarities[section_name] = calculate_text_similarity(texts)
    
    # 전체 일관성 점수 계산 (가중 평균)
    weights = {
        "summary": 0.2,      # 요약은 핵심이므로 높은 가중치
        "situation": 0.25,   # 상황설명도 중요
        "emotion": 0.2,      # 감정표현
        "empathy": 0.15,     # 공감과인정
        "comfort": 0.1,      # 따뜻한위로
        "suggestion": 0.1    # 실용적제안
    }
    
    overall_consistency = sum(
        section_similarities[section] * weight 
        for section, weight in weights.items()
    )
    
    # 일관성 등급 결정
    if overall_consistency >= 0.8:
        consistency_grade = "매우 높음"
        grade_color = "🟢"
    elif overall_consistency >= 0.6:
        consistency_grade = "높음"
        grade_color = "🟡"
    elif overall_consistency >= 0.4:
        consistency_grade = "보통"
        grade_color = "🟠"
    else:
        consistency_grade = "낮음"
        grade_color = "🔴"
    
    # 개선 제안 생성
    improvement_suggestions = []
    if overall_consistency < 0.6:
        improvement_suggestions.append("전체적인 일관성이 낮습니다. 프롬프트를 더 구체적으로 개선해주세요.")
    
    low_consistency_sections = [
        section for section, score in section_similarities.items() 
        if score < 0.4
    ]
    if low_consistency_sections:
        improvement_suggestions.append(f"다음 섹션들의 일관성이 낮습니다: {', '.join(low_consistency_sections)}")
    
    return {
        "total_tests": len(results),
        "successful_tests": len(successful_results),
        "consistency_score": round(overall_consistency, 3),
        "consistency_grade": consistency_grade,
        "grade_color": grade_color,
        "detailed_similarity": {
            section: round(score, 3) for section, score in section_similarities.items()
        },
        "message": f"일관성 점수: {overall_consistency:.1%} ({consistency_grade})",
        "improvement_suggestions": improvement_suggestions,
        "results": results
    }

def calculate_text_similarity(texts: list) -> float:
    """
    텍스트 리스트 간의 유사도를 계산합니다.
    
    Args:
        texts: 비교할 텍스트 리스트
    
    Returns:
        float: 유사도 점수 (0.0 ~ 1.0)
    """
    if len(texts) < 2:
        return 1.0
    
    # 간단한 키워드 기반 유사도 계산
    similarities = []
    
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            text1 = texts[i].lower()
            text2 = texts[j].lower()
            
            # 공통 키워드 수 계산
            words1 = set(text1.split())
            words2 = set(text2.split())
            
            if len(words1) == 0 or len(words2) == 0:
                similarity = 0.0
            else:
                common_words = words1.intersection(words2)
                total_words = words1.union(words2)
                similarity = len(common_words) / len(total_words)
            
            similarities.append(similarity)
    
    return sum(similarities) / len(similarities) if similarities else 0.0

# 일관성 테스트 엔드포인트
@app.post("/consistency-test")
async def consistency_test_endpoint(
    file: UploadFile = File(...),
    test_count: int = 5,
    target_date: str | None = None,
    use_date_analysis: bool = False
):
    """
    일관성 테스트를 수행하는 엔드포인트
    
    Args:
        file: 카카오톡 txt 파일
        test_count: 테스트 횟수 (기본값: 5)
        target_date: 특정 날짜 (use_date_analysis가 True일 때)
        use_date_analysis: 날짜별 분석 사용 여부
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
                    target_date = available_dates[-1]
                else:
                    raise HTTPException(status_code=400, detail="유효한 날짜가 없습니다.")
            
            # 해당 날짜의 대화 내용
            if target_date is not None:
                kakao_text = get_chat_for_date(chat_by_date, target_date)
            else:
                raise HTTPException(status_code=400, detail="유효한 날짜가 없습니다.")
                
        else:
            # 기존 방식 (최근 30줄)
            kakao_text = extract_today_chat(content)
            target_date = None
        
        if not kakao_text.strip():
            raise HTTPException(status_code=400, detail="카카오톡 대화가 감지되지 않았습니다.")
        
        # 일관성 테스트 실행
        test_result = run_consistency_test(kakao_text, test_count)
        
        # 추가 정보 포함
        test_result["input_info"] = {
            "target_date": target_date,
            "use_date_analysis": use_date_analysis,
            "text_length": len(kakao_text),
            "test_count": test_count
        }
        
        return ORJSONResponse(content=test_result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 일관성 테스트 정보 제공 엔드포인트
@app.get("/consistency-test-info")
async def consistency_test_info():
    """
    일관성 테스트 기능에 대한 정보를 제공하는 엔드포인트
    """
    return ORJSONResponse(content={
        "message": "일관성 테스트 기능이 구현되었습니다!",
        "description": "동일한 입력에 대해 여러 번 테스트하여 결과의 일관성을 검증합니다.",
        "endpoint": "/consistency-test",
        "parameters": {
            "file": "카카오톡 txt 파일",
            "test_count": "테스트 횟수 (기본값: 5)",
            "target_date": "특정 날짜 (예: '18일')",
            "use_date_analysis": "날짜별 분석 사용 여부"
        },
        "output": {
            "consistency_score": "일관성 점수 (0.0 ~ 1.0)",
            "consistency_grade": "일관성 등급 (매우 높음/높음/보통/낮음)",
            "detailed_similarity": "각 섹션별 유사도 점수",
            "results": "각 테스트 결과"
        },
        "usage_tips": [
            "test_count는 3~10 사이로 설정하는 것을 권장합니다",
            "일관성 점수가 0.6 이상이면 양호한 수준입니다",
            "낮은 일관성은 프롬프트 개선이 필요할 수 있습니다"
        ]
    })

# 날짜별 분석 기능 테스트 엔드포인트
@app.get("/test-date-analysis")
async def test_date_analysis():
    """
    날짜별 분석 기능 테스트를 위한 정보 제공 엔드포인트
    """
    return ORJSONResponse(content={
        "message": "날짜별 분석 기능이 성공적으로 구현되었습니다!",
        "features": {
            "extract_chat_by_date": "카카오톡 대화를 날짜별로 구분",
            "analyze_events_by_date": "각 날짜별 이벤트 분석",
            "diary_by_date": "특정 날짜의 감성 일기 생성"
        },
        "endpoints": {
            "/auto-diary": "메인 기능 - 파일 업로드 + 모든 옵션",
            "/generate-diary": "텍스트 기반 일기 생성",
            "/test-date-analysis": "기능 테스트용"
        },
        "usage": {
            "use_date_analysis": "true로 설정하면 날짜별 분석 사용",
            "target_date": "특정 날짜 지정 (예: '20일', '19일')",
            "available_dates": "파일에서 감지된 모든 날짜 목록"
        }
    })

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 또는 Flutter 앱 도메인만 제한적으로
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 루트 엔드포인트 - 서버 연결 확인용
@app.get("/")
async def root():
    """
    서버 연결 확인을 위한 루트 엔드포인트
    """
    return ORJSONResponse(content={
        "message": "감성 일기 생성 서버가 정상적으로 실행 중입니다!",
        "status": "running",
        "version": "1.0.0",
        "available_endpoints": [
            "/",
            "/generate-diary",
            "/auto-diary", 
            "/consistency-test",
            "/consistency-test-info",
            "/test-date-analysis"
        ],
        "features": [
            "카카오톡 대화 기반 감성 일기 생성",
            "프롬프트 충돌 감지 및 처리",
            "날짜별 대화 분석",
            "일관성 테스트",
            "감정 분석"
        ]
    }) 