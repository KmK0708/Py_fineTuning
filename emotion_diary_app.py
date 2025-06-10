import os
import streamlit as st
from openai import OpenAI
import json

# 🔑 OpenAI API 설정
os.environ["OPENAI_API_KEY"] = ""  # 여기에 실제 키 입력 # 커밋할때 오류뜨니 바꿈
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
        user_input = f"""검색기록: {search_log}\n카카오톡 대화: {chat_log}\n요약: {summary}\n\n이 정보를 바탕으로 감정 분석과 감성적인 하루 일기를 JSON 형식으로 작성해줘."""

        response = client.chat.completions.create(
            model="ft:gpt-4o-mini-2024-07-18:juyoung:emotioncheck:BfrP3T8T",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "당신은 감정을 분석해서 JSON 형식으로만 응답해야 합니다. 예: {\"emotion\": \"우울\", \"message\": \"오늘 많이 힘드셨겠어요...\"}"},
                {"role": "user", "content": user_input}
            ]
        )

        # 결과 파싱 및 표시
        try:
            result = json.loads(response.choices[0].message.content)
            st.success("✅ 분석 완료")
            st.markdown(f"**🧠 감정:** {result.get('emotion', '없음')}")
            st.markdown(f"**📔 감성 일기:**\n\n{result.get('message', '없음')}")
        except Exception as e:
            st.error(f"⚠️ JSON 응답 파싱 실패: {e}")
            st.text("👀 원본 응답 내용:")
            st.text(response.choices[0].message.content)