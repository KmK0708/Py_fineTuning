import re

# 실제 폰 카카오톡 데이터
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

# 정규표현식들
date_pattern = re.compile(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일")
msg_pc_pattern = re.compile(r"^\[(.*?)\]\s*\[(오전|오후)\s*\d{1,2}:\d{2}\]\s*(.*)")
msg_phone_pattern = re.compile(r"^\d{4}년\s*\d{1,2}월\s*\d{1,2}일\s*(오전|오후)\s*\d{1,2}:\d{2},\s*(.*?)\s*:\s*(.*)")

print("=== 수정된 로직 테스트 ===")
lines = test_data.splitlines()
chat_by_date = {}
current_date = None

for line in lines:
    line = line.strip()
    if not line:
        continue
        
    date_match = date_pattern.search(line)
    if date_match:
        # 날짜 헤더 라인인지 확인 (메시지가 없는 경우)
        if not msg_phone_pattern.match(line) and not msg_pc_pattern.match(line):
            date_str = f"{date_match.group(1)}년 {int(date_match.group(2))}월 {int(date_match.group(3))}일"
            current_date = date_str
            if current_date not in chat_by_date:
                chat_by_date[current_date] = []
            print(f"📅 날짜 설정: {current_date}")
            continue
        
    # 컴퓨터 형식 메시지 라인인지 확인
    msg_pc_match = msg_pc_pattern.match(line)
    if msg_pc_match and current_date:
        msg_txt = msg_pc_match.group(3).strip()
        if not any(k in msg_txt for k in ["[사진]", "이모티콘", "님이 입장", "님이 나갔"]):
            chat_by_date[current_date].append(msg_txt)
            print(f"✅ PC 메시지 추가: '{msg_txt}'")
        continue
        
    # 폰 형식 메시지 라인인지 확인
    msg_phone_match = msg_phone_pattern.match(line)
    if msg_phone_match and current_date:
        msg_txt = msg_phone_match.group(3).strip()
        # 파일 확장자나 해시값 같은 파일명 제외
        if (not any(k in msg_txt for k in ["[사진]", "이모티콘", "님이 입장", "님이 나갔", "사진"]) and
            not re.match(r'^[a-f0-9]{32,}\.[a-z]+$', msg_txt) and  # 해시값 파일명
            not re.match(r'^.*\.(png|jpg|jpeg|gif|mp4|mov|avi)$', msg_txt.lower())):  # 일반 파일명
            chat_by_date[current_date].append(msg_txt)
            print(f"✅ 폰 메시지 추가: '{msg_txt}'")
        else:
            print(f"❌ 필터링됨: '{msg_txt}'")
        continue

print(f"\n=== 최종 결과 ===")
for date, messages in chat_by_date.items():
    print(f"📅 {date}: {len(messages)}개 메시지")
    for msg in messages:
        print(f"   - {msg}") 