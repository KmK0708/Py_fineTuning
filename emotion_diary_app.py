import os
import streamlit as st
from openai import OpenAI
import json

# 🔑 OpenAI API 설정
os.environ["OPENAI_API_KEY"] = "123"  # 여기에 실제 키 입력 # 커밋할때 오류뜨니 바꿈
client = OpenAI()

# 📋 Streamlit UI 설정
st.set_page_config(page_title="감성 일기 생성기", page_icon="📝")
st.title("🧠 하루 감정 분석 & 감성 일기 생성")

# 📌 사용자 입력
search_log = st.text_area("🔍 오늘의 검색 기록", height=100, placeholder="예: 무기력 극복법, 우울증 증상, 혼자 있는 법")
chat_log = st.text_area("💬 카카오톡 대화 요약", height=100, placeholder="예: 아무것도 하기 싫어, 너무 우울해")
summary = st.text_area("📝 하루 요약", height=100, placeholder="예: 하루종일 무기력했고, 식사도 거름. 감정 관련 검색이 많았음.")

if st.button("✨ 감성 일기 생성"):
    with st.spinner("AI가 감정을 분석 중입니다..."):
         user_input = f"""
검색기록: {search_log}
카카오톡 대화: {chat_log}
요약: {summary}

이 정보를 바탕으로 아래 항목들을 포함한 감정 분석과 감성 일기를 JSON 형식으로 생성해줘:

1. 감정 분석: {{감정명: {{정도: "...", 원인: "..."}}}}
2. 감정 털어놓기: {{방법: "..."}}
3. 하루 계획: {{할 일: "...", 마음 챙김: "..."}}
4. 하루 일기: 한국어로 쓴 일기 형식으로 작성, 최소 **5문장 이상**, 감정과 상황을 **감성적인 부드러운 문장**으로 작성해야합니다. 해결방안도 같이 작성해주세요. 사용자가 입력하지 않은 상황은 적지 않습니다.

응답은 반드시 JSON 형식으로만 해줘.
"""

    try:
        response = client.chat.completions.create(
            model="ft:gpt-4o-mini-2024-07-18:juyoung:emotioncheck:BfrP3T8T",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "당신은 사용자 데이터를 바탕으로 감정 분석과 감성 일기를 JSON 형식으로만 응답하는 AI입니다."},
                {"role": "user", "content": user_input}
            ]
        )

        result = json.loads(response.choices[0].message.content)

        st.success("✅ 분석 완료")

        # ✅ 출력 구성
        if "감정 분석" in result:
            st.markdown("### 🧠 감정 분석")
            st.json(result["감정 분석"])
        if "감정 털어놓기" in result:
            st.markdown("### 💬 감정 털어놓기")
            st.json(result["감정 털어놓기"])
        if "하루 계획" in result:
            st.markdown("### 🗓️ 하루 계획")
            st.json(result["하루 계획"])
        if "하루 일기" in result:
            st.markdown("### 📔 감성 일기")
            st.markdown(result["하루 일기"])

    except Exception as e:
        st.error(f"⚠️ JSON 응답 파싱 실패: {e}")
        st.text("👀 원본 응답 내용:")
        st.text(response.choices[0].message.content)