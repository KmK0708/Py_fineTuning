import os
import streamlit as st
import datetime
import re
import platform
from openai import OpenAI
import json

# 🔑 OpenAI API 설정
os.environ["OPENAI_API_KEY"] = "s123"  # 여기에 실제 키 입력 # 커밋할때 오류뜨니 바꿈
client = OpenAI()

# Streamlit UI 설정
st.set_page_config(page_title="감성 일기 생성기", page_icon="📝")
st.title("🧠 하루 감정 분석 & 감성 일기 생성")

# 📌 사용자 입력 (파일 첨부)
kakao_file = st.file_uploader("📁 카카오톡 대화 파일 업로드", type="txt")

kakao_text_full = ""
if kakao_file is not None:
    # 파일 내용을 UTF-8로 읽음 (오류 발생 시 무시)
    kakao_text_full = kakao_file.read().decode("utf-8", errors='ignore')

    # 전체 대화 내용 표시 여부 선택
    if st.checkbox("📜 전체 대화 내용 보기"):
        st.text_area("📜 전체 대화 내용", kakao_text_full, height=300)

    # 파일 포인터를 다시 처음으로 돌려놓습니다. (파싱을 위해 다시 읽을 수 있도록)
    kakao_file.seek(0)
    st.success("카카오톡 파일이 성공적으로 업로드되었습니다. 잠시 후 오늘의 대화가 자동 추출됩니다.")
else:
    st.info("카카오톡 대화 파일을 업로드하시면 오늘의 대화가 자동 추출됩니다.")

# 📌 검색 기록 수동 입력
search_log = st.text_area("🔍 오늘의 검색 기록", height=100, placeholder="예: 무기력 극복법, 우울증 증상, 혼자 있는 법")

# 오늘 날짜 동적으로 가져오기
today_date = datetime.datetime.now()
# 운영체제에 따라 날짜 포맷팅 (Windows: %#m, Unix/macOS: %-m)
if platform.system() == "Windows":
    today_formatted = today_date.strftime("%Y년 %#m월 %#d일")
else:
    today_formatted = today_date.strftime("%Y년 %-m월 %-d일")

chat_log = ""
summary = ""

# 📤 카카오톡 자동 추출 (날짜 기반 파싱 강화)
if kakao_file is not None:
    # 다시 읽기 전에 seek(0)을 했으므로, 여기서 다시 읽어도 됩니다.
    kakao_text = kakao_file.read().decode("utf-8", errors='ignore')
    lines = kakao_text.splitlines()

    # 정규식을 사용하여 날짜 패턴을 정확히 매칭 (YYYY년 M월 D일 (요일))
    # 예: "---------- 2025년 7월 12일 토요일 ----------"
    date_separator_pattern = re.compile(r"^-+\s*(\d{4}년\s*\d{1,2}월\s*\d{1,2}일)\s*(?:\(.\)요일)?\s*-+$")

    collecting = False
    today_chat_lines = []

    for line in lines:
        line_stripped = line.strip()

        # 날짜 구분선 찾기
        date_match = date_separator_pattern.match(line_stripped)
        if date_match:
            extracted_date_str = date_match.group(1)
            # 현재 날짜와 일치하는지 확인 (형식을 맞춰서 비교)
            if extracted_date_str == today_formatted:
                collecting = True
            else:
                collecting = False # 다른 날짜가 시작되면 수집 중단
            continue # 날짜 구분선은 대화 내용이 아니므로 다음 줄로

        if collecting and line_stripped: # 수집 중이고 빈 줄이 아닐 때
            # "이름 [오전/오후 시간] 내용" 패턴을 가정하여 내용만 추출
            # 예시: "김철수 [오후 1:30] 안녕하세요!" -> "안녕하세요!"
            dialogue_match = re.match(r"\[.*?\]\s*\[(?:오전|오후)\s*\d{1,2}:\d{2}\]\s*(.*)", line_stripped)
            if dialogue_match:
                content = dialogue_match.group(1).strip()
                # 불필요한 내용 필터링 (사진, 이모티콘 등)
                if not any(keyword in content for keyword in ["[사진]", "[이모티콘]", "이모티콘", "님이 입장하셨습니다", "님이 나갔습니다"]):
                    today_chat_lines.append(content)
            else:
                # 대화 내용이 아닌 기타 정보 (예: 공지 등) 필터링
                if not any(keyword in line_stripped for keyword in ["[사진]", "[이모티콘]", "이모티콘", "님이 입장하셨습니다", "님이 나갔습니다"]):
                    today_chat_lines.append(line_stripped)

    # 추출된 대화 내용이 많을 경우, 최근 N줄만 사용 (더 많은 문맥을 위해 30줄 사용)
    chat_log = "\n".join(today_chat_lines[-30:])
    if chat_log: # 추출된 내용이 있을 경우에만 표시
        st.text_area("💬 오늘의 카카오톡 대화 요약 (자동 추출)", chat_log, height=150)
    else:
        st.info("오늘 날짜에 해당하는 카카오톡 대화 내용이 없거나 파싱할 수 없습니다.")


# 하루 요약 수동 입력
summary = st.text_area("📝 하루 요약", height=100, placeholder="예: 하루종일 무기력했고, 식사도 거름. 감정 관련 검색이 많았음.")

# 🧠 감정 분석 및 일기 생성
if st.button("✨ 감성 일기 생성"):
    # 분석할 정보가 모두 비어있을 경우 경고
    if not search_log and not chat_log and not summary:
        st.warning("분석할 정보(검색 기록, 카카오톡 대화, 하루 요약)를 최소 하나 이상 입력해주세요.")
    else:
        with st.spinner("AI가 감정을 분석 중입니다..."):
            user_input = f"""
            검색기록: {search_log}
            카카오톡 대화: {chat_log}
            요약: {summary}

            이 정보를 바탕으로 아래 항목들을 포함한 감정 분석과 감성 일기를 JSON 형식으로 생성해줘:

            1. 감정 분석: {{"감정명": "...", "정도": "...", "원인": "..."}}
            2. 감정 털어놓기: {{"방법": "..."}}
            3. 하루 계획: {{"할 일": "...", "마음 챙김": "..."}}
            4. 하루 일기: 반드시 한국어로 쓴 일기 형식으로 작성, 최소 **5문장 이상**, 감정과 상황을 **감성적인 부드러운 문장**으로 작성해야 합니다. 해결방안도 같이 작성해주세요. 사용자가 입력하지 않은 상황은 적지 마세요. 외국어는 사용하면 안됩니다.

            응답은 반드시 JSON 형식으로만 해줘.
            """

            try:
                # API 호출 방식 수정: client.chat().completions().create() -> client.chat.completions.create()
                response = client.chat.completions.create(
                    model="ft:gpt-4o-mini-2024-07-18:juyoung:emotioncheck:BfrP3T8T", # 사용자 지정 모델명 유지
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": "당신은 사용자 데이터를 바탕으로 감정 분석과 감성 일기를 json으로 작성해주는 AI입니다."},
                        {"role": "user", "content": user_input}
                    ]
                )
                result = json.loads(response.choices[0].message.content)

                st.success("✅ 분석 완료")

                # 결과 출력
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

            except json.JSONDecodeError as e:
                st.error(f"⚠️ AI 응답이 올바른 JSON 형식이 아닙니다: {e}")
                if response and response.choices:
                    st.text("👀 AI 원본 응답 내용:")
                    st.code(response.choices[0].message.content)
            except Exception as e:
                st.error(f"⚠️ 일기 생성 중 오류 발생: {e}")
                if 'response' in locals() and response and response.choices:
                    st.text("👀 AI 원본 응답 내용 (오류 발생 전):")
                    st.code(response.choices[0].message.content)
