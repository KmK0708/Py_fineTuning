import os
# openai 가져오기
from openai import OpenAI

os.environ["OPENAI_API_KEY"] = '1234' # 커밋할때 오류뜨니 바꿈

# client 인스턴스 가져오기
client = OpenAI()

# chat. completions. create 메서드를 호출하여 응답을 받음 
response = client.chat.completions.create(
    model="ft:gpt-4o-mini-2024-07-18:juyoung:emotioncheck:BfrP3T8T",
    response_format={"type": "json_object"},
    messages=[
    
    {
        "role": "user",
        "content": "날짜: 2025-06-07\n"
                "검색기록: [\"우울증 증상\", \"무기력 극복법\", \"혼자 있는 법\", \"자기전 마음을 편하게 하는 방법\"]\n"
                "카카오톡 대화: [\"오늘 아무것도 하기 싫었어\", \"나 너무 무기력해\", \"밥도 안 먹었어 그냥 누워 있었어\", \"괜히 눈물 날 것 같아\"]\n"
                "요약: 사용자는 하루 종일 무기력하고 우울한 기분을 느꼈으며, 식사도 거르고 대화를 거의 하지 않았다. "
                "여러 감정 관련 키워드를 검색하고, 누군가에게 우울한 감정을 털어놓았다.\n\n"
                "이 정보를 바탕으로 감정 분석과 감성적인 하루 일기를 JSON 형식으로 작성해줘."
    }
    ]
)
# 응답 출력
print(response.choices[0].message.content)

# ✅ 토큰 사용량 출력
print("Prompt tokens:", response.usage.prompt_tokens)
print("Completion tokens:", response.usage.completion_tokens)
print("Total tokens:", response.usage.total_tokens)