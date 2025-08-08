import re

# 테스트 데이터
test_data = """2025년 8월 8일 오전 12:51
2025년 8월 8일 오전 12:51, 영제 : 어휴 힘들다
2025년 8월 8일 오전 1:40, 주영 : 아 오라클
2025년 8월 8일 오전 1:40, 주영 : 지옥가네
2025년 8월 8일 오전 1:40, 주영 : 시발
2025년 8월 8일 오전 1:40, 영제 : ㄹㅇ?
2025년 8월 8일 오전 1:40, 주영 : 871bcca5055ab9d32cfea7369ddd9e0b42386529a1b368370c778eef05e4def6.png
2025년 8월 8일 오전 1:40, 주영 : 253.18 매수인데
2025년 8월 8일 오전 1:41, 주영 : 시발
2025년 8월 8일 오전 1:42, 주영 : 그냥
2025년 8월 8일 오전 1:42, 주영 : 나스닥전체가
2025년 8월 8일 오전 1:42, 주영 : 흐르는구나
2025년 8월 8일 오전 1:43, 영제 : 그런거같음
2025년 8월 8일 오전 1:43, 영제 : 아프다..
2025년 8월 8일 오전 1:43, 주영 : 시ㅣㅣㅣㅣ바ㅏㅏ"""

# 현재 정규표현식
msg_phone = re.compile(r"^\d{4}년\s*\d{1,2}월\s*\d{1,2}일\s*(오전|오후)\s*\d{1,2}:\d{2},\s*(.*?)\s*:\s*(.*)")

print("=== 새로운 필터링 테스트 결과 ===")
for line in test_data.splitlines():
    line = line.strip()
    if not line:
        continue
        
    match = msg_phone.match(line)
    if match:
        name = match.group(2)
        message = match.group(3)
        
        # 새로운 필터링 로직 적용
        if (not any(k in message for k in ["[사진]", "이모티콘", "님이 입장", "님이 나갔", "사진"]) and
            not re.match(r'^[a-f0-9]{32,}\.[a-z]+$', message) and  # 해시값 파일명
            not re.match(r'^.*\.(png|jpg|jpeg|gif|mp4|mov|avi)$', message.lower())):  # 일반 파일명
            print(f"✅ 유효한 메시지: '{name}' -> '{message}'")
        else:
            print(f"❌ 필터링됨: '{name}' -> '{message}'")
    else:
        print(f"❌ 매칭안됨: '{line}'") 