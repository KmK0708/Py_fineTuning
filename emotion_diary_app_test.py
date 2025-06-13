import os
import streamlit as st
import datetime
import re
import platform
from openai import OpenAI
import json

# 🔑 OpenAI API 설정
# os.environ["OPENAI_API_KEY"] = "in_your_API"   여기에 실제 키 입력 # 커밋할때 오류뜨니 바꿈
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
# ------------- 1) 기본 설정 -------------
st.set_page_config(page_title="감성 일기 생성기", page_icon="📝")
st.title("🧠 하루 감정 분석 & 감성 일기 생성")

# ------------- 2) 파일 업로드 -------------
uploaded = st.file_uploader("📁 카카오톡 대화 파일 (.txt)", type="txt")

raw_text = ""
if uploaded:
    raw_text = uploaded.read().decode("utf-8", errors="ignore")
    st.success("✅ 파일 업로드 완료")
    if st.checkbox("전체 파일 미리 보기"):
        st.text_area("📜 원본 데이터", raw_text, height=250)

# ------------- 3) 오늘 날짜 계산 -------------
today = datetime.datetime.now()
today_str = f"{today.year}년 {today.month}월 {today.day}일"   # 예: 2025년 6월 12일

# ------------- 4) 카톡 → 오늘 대화만 추출 -------------
def extract_today(text: str, date_str: str) -> str:
    lines = text.splitlines()
    chat = []
    collect = False

    # 헤더: '---- 2025년 6월 7일 토요일 ----'  또는  '2025년 6월 7일 토요일'
    date_hdr = re.compile(rf"^[-\s]*{re.escape(date_str)}.*$")

    # 메시지: ① [이름] 오후 1:23 내용   ② 오후 1:23 [이름] 내용
    msg1 = re.compile(r"^\[(.*?)\]\s*(오전|오후)\s*\d{1,2}:\d{2}\s*(.*)")
    msg2 = re.compile(r"^(오전|오후)\s*\d{1,2}:\d{2}\s*\[(.*?)\]\s*(.*)")

    for ln in lines:
        ln = ln.strip()
        if date_hdr.match(ln):
            collect = True
            continue
        if collect:
            if date_hdr.match(ln):      # 다음 날짜 만나면 종료
                break
            # 실 메시지 추출
            m = msg1.match(ln) or msg2.match(ln)
            if m:
                msg_txt = m.group(3).strip()
                # 불필요 라인 제거
                if not any(k in msg_txt for k in ("[사진]", "이모티콘", "님이 입장", "님이 나갔")):
                    chat.append(msg_txt)
    return "\n".join(chat[-30:])   # 최근 30줄만

# -------- 자동 요약 생성 (chat_log 기반) --------
chat_log = extract_today(raw_text, today_str) if uploaded else ""
auto_summary = ""
if chat_log:
    try:
        with st.spinner("🧠 대화 요약 생성 중..."):
            summary_prompt = f"""
            아래는 오늘 하루의 카카오톡 대화입니다:

            ---
            {chat_log}
            ---

            이 내용을 바탕으로 오늘 어떤 일이 있었는지 2~3문장으로 요약해줘.
            감정적 표현 없이, 일어난 일 위주로 설명해줘. 예: '오전에는 병원에 대한 대화가 있었고, 오후에는 발표 준비에 대한 걱정이 담긴 대화가 있었다.'
            반드시 한글로 작성하고, JSON으로 다음처럼 응답해줘:

            {{
              "summary": "..."
            }}
            """
            resp_sum = client.chat.completions.create(
                model="ft:gpt-4o-mini-2024-07-18:juyoung:emotioncheck:BfrP3T8T",  # 또는 gpt-4o
                messages=[{"role": "user", "content": summary_prompt}]
            )
            auto_summary = json.loads(resp_sum.choices[0].message.content)["summary"]
            st.text_area("📝 자동 생성된 하루 요약", auto_summary, height=80)
    except Exception as e:
        st.warning("하루 요약 생성 실패. 수동으로 입력해주세요.")
        auto_summary = ""

# ------------- 5) 기타 수동 입력 -------------
search_log = st.text_area("🔍 오늘의 검색 기록 (선택)", height=80)
user_summary = auto_summary or st.text_area("✍️ 직접 입력할 하루 요약 (필요 시)", height=80)

# ------------- 6) GPT 호출 -------------
if st.button("✨ 감성 일기 생성"):
    if not any([chat_log, search_log, user_summary]):
        st.warning("검색 기록, 대화, 요약 중 하나 이상은 입력해야 합니다.")
        st.stop()

    prompt = f"""
    ### 입력 정보
        - 검색 기록: {search_log or "없음"}
        - 카카오톡 대화: {chat_log or "없음"}
        - 하루 요약: {user_summary or "없음"}

    ### 작성 지침
    1) 사용자 대화에는 감정이 숨겨져 있을 수 있으므로, 상황의 흐름과 말투에서 감정을 섬세하게 추론하세요.
    2) 아래 JSON **구조** 그대로 채워서 출력하세요(필드명 변경 금지).
    3) 예시처럼 각 항목은 3문장 이상, 따뜻하고 진심 어린 말로 작성하세요.
    4) 대화 속 비속어/분노 표현이 있어도 무시하지 말고, 그 안에 숨은 감정을 정리해서 표현하세요.
    5) 외국어/영어/암호화폐 용어는 그대로 써도 되지만, 사용자가 **느낀 감정**에 집중해서 위로와 조언을 구성하세요.
    6) **다른 텍스트는 절대 포함하지 마세요. 코드블록도 넣지 마세요.**

    {{
      "상황설명": "...",
      "감정표현": "...",
      "공감과인정": "...",
      "따뜻한위로": "...",
      "실용적제안": "..."
    }}
    위의 나온 것들을 총합해서 아래 예시와 같이 총합해서 작성해야합니다.
    예시) 오늘은 ~~한 일이 있었군요. 그래서 ~~한 감정을 느꼈겠어요. 그 감정은 너무 자연스럽고 당연한 거예요. 지금 이 순간 당신에게 필요한 건 ~~, 그리고 앞으로는 ~~ 해보는 걸 추천해요.

    각 필드는 3 문장 이상, 따뜻하고 부드러운 한국어로 작성하고
    사용자가 주지 않은 사실은 절대 넣지 마세요.
    """

    with st.spinner("AI가 글을 작성 중입니다..."):
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"system","content":"당신은 사용자의 일상 대화를 바탕으로, 그 안에 숨어 있는 감정과 스트레스를 추론하여 따뜻하게 공감해주는 작가이자 상담가입니다. \
                            욕설, 무기력한 말투, 조급한 표현 속에서 진짜 감정을 파악하고, 그것에 맞춰 다정한 위로와 실질적인 제안을 주는 역할입니다. \
                            모든 출력은 반드시 JSON으로 주어야 하며, 사용자가 주지 않은 배경은 추측하지 마세요. \
                           ⛔ 절대 출력 앞뒤에 설명을 붙이지 마세요."},
                          {"role":"user","content":prompt}]
            )
            result = json.loads(resp.choices[0].message.content)
        except json.JSONDecodeError as e:
            st.error("⚠️ JSON 파싱 실패. 프롬프트·출력 구조를 다시 확인하세요.")
            st.code(resp.choices[0].message.content)
            st.stop()
        except Exception as e:
            st.error(f"⚠️ OpenAI 호출 오류: {e}")
            st.stop()

    # ------------- 7) 결과 표시 -------------
    st.success("✅ 완성")
    for key,label in [("상황설명","📝 상황 설명"),("감정표현","💭 감정 표현"),
                      ("공감과인정","🤝 공감과 인정"),("따뜻한위로","🌷 따뜻한 위로"),
                      ("실용적제안","💡 실용적 제안")]:
        if key in result:
            st.markdown(f"#### {label}")
            st.write(result[key])