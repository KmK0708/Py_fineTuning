import os
import re
import json
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()


# ✅ 요청 모델
class DiaryRequest(BaseModel):
    kakao_text: str
    search_log: str | None = "없음"


# ✅ 오늘 날짜를 카카오톡 날짜 포맷에 맞게 반환
def get_today_str_kakao():
    today = datetime.now()
    return f"{today.year}년 {today.month}월 {today.day}일"


def extract_today_chat(text: str, _: str = "") -> str:
    lines = text.splitlines()
    chat = []

    # ✅ [이름] [오후 3:36] 메시지
    msg = re.compile(r"^\[(.*?)\]\s*\[(오전|오후)\s*\d{1,2}:\d{2}\]\s*(.*)")

    for ln in lines:
        ln = ln.strip()
        m = msg.match(ln)
        if m:
            msg_txt = m.group(3).strip()
            if not any(k in msg_txt for k in ["[사진]", "이모티콘", "님이 입장", "님이 나갔"]):
                chat.append(msg_txt)

    return "\n".join(chat[-30:])


# ✅ 1. 카카오톡 txt 업로드 및 오늘 대화 미리보기
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

        # 2단계: 감성 일기 생성
        diary_prompt = f"""
        ### 입력 정보
        - 검색기록: {data.search_log}
        - 카카오톡 대화: {data.kakao_text}
        - 요약: {summary}

        ### 지시사항
        1) 사용자 대화에는 감정이 숨겨져 있을 수 있으므로, 상황의 흐름과 말투에서 감정을 섬세하게 추론하세요.
        2) 아래 JSON **구조** 그대로 채워서 출력하세요(필드명 변경 금지).
        3) 예시처럼 각 항목은 3문장 이상, 따뜻하고 진심 어린 말로 작성하세요.
        4) 외국어, 욕설이 있어도 무시하지 말고 감정을 정확히 해석하세요.

        {{
          "상황설명": "...",
          "감정표현": "...",
          "공감과인정": "...",
          "따뜻한위로": "...",
          "실용적제안": "..."
        }}
        모든 응답은 한국어로 따뜻하고 진심어리게 작성하고, 각각 2~3문장 이상 작성하세요.
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

        return diary

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/auto-diary")
async def auto_diary(file: UploadFile = File(...), search_log: str = "없음"):
    try:
        content = (await file.read()).decode("utf-8", errors="ignore")

        # 1단계: 카카오톡 대화 추출
        kakao_text = extract_today_chat(content)

        if not kakao_text.strip():
            raise HTTPException(status_code=400, detail="카카오톡 대화가 감지되지 않았습니다.")

        # 2단계: 요약 생성
        summary_prompt = f"""
        아래는 카카오톡 대화 내용입니다:
        ---
        {kakao_text}
        ---

        위 대화를 요약해줘. 감정 표현 없이 무슨 일이 있었는지 2~3문장으로 설명해줘.
        절대로 설명 없이 다음 JSON 형식만 출력하세요:

        {{
          "summary": "..."
        }}
        """

        summary_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": summary_prompt}]
        )

        summary_raw = summary_response.choices[0].message.content
        print("📄 요약 응답 원문:\n", summary_raw)

        try:
            summary = json.loads(summary_raw)["summary"]
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=500,
                detail=f"요약 응답 파싱 실패: {e}\n원문: {summary_raw}"
            )

        # 3단계: 감성일기 생성
        diary_prompt = f"""
        ### 입력 정보
        - 검색기록: {search_log}
        - 카카오톡 대화: {kakao_text}
        - 요약: {summary}

        ### 지시사항
        아래 형식으로만 출력하세요. 설명 문장 없이 JSON만 출력하세요:

        {{
          "상황설명": "...",
          "감정표현": "...",
          "공감과인정": "...",
          "따뜻한위로": "...",
          "실용적제안": "..."
        }}

        모든 항목은 진심 어린 한국어로 2~3문장 이상 작성하세요.
        """

        diary_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "당신은 감성적인 작가이자 상담가입니다. 반드시 JSON 형식으로만 응답하세요. 설명이나 서론 없이."
                },
                {
                    "role": "user",
                    "content": diary_prompt
                }
            ]
        )

        diary_raw = diary_response.choices[0].message.content
        print("📄 감성일기 응답 원문:\n", diary_raw)

        try:
            diary = json.loads(diary_raw)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=500,
                detail=f"일기 응답 파싱 실패: {e}\n원문: {diary_raw}"
            )

        diary["summary"] = summary
        diary["kakao_text"] = kakao_text

        return diary

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


        # ### 작성 지침
        # 1) 사용자 대화에는 감정이 숨겨져 있을 수 있으므로, 상황의 흐름과 말투에서 감정을 섬세하게 추론하세요.
        # 2) 아래 JSON **구조** 그대로 채워서 출력하세요(필드명 변경 금지).
        # 3) 예시처럼 각 항목은 3문장 이상, 따뜻하고 진심 어린 말로 작성하세요.
        # 4) 외국어, 욕설이 있어도 무시하지 말고 감정을 정확히 해석하세요.

        # {{
        #   "상황설명": "...",
        #   "감정표현": "...",
        #   "공감과인정": "...",
        #   "따뜻한위로": "...",
        #   "실용적제안": "..."
        # }}