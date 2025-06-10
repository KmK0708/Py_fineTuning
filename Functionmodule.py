import json

def json_to_jsonl(input_file, output_file):
    """
    JSON 파일을 JSONL 형식으로 변환
    
    Args:
        input_file (str): 입력 JSON 파일 경로
        output_file (str): 출력 JSONL 파일 경로
    """
    try:
        # JSON 파일 읽기
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # JSONL 파일로 쓰기
        with open(output_file, 'w', encoding='utf-8') as f:
            # 데이터가 리스트인 경우 각 요소를 한 줄씩
            if isinstance(data, list):
                for item in data:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
            # 데이터가 단일 객체인 경우 그대로 한 줄로
            else:
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
        
        print(f"변환 완료: {input_file} -> {output_file}")
        
    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {input_file}")
    except json.JSONDecodeError:
        print(f"JSON 형식이 올바르지 않습니다: {input_file}")
    except Exception as e:
        print(f"오류 발생: {e}")


def convert_to_finetune_format(input_file, output_file, format_type="openai"):
    """
    JSONL 파일을 파인튜닝 형식으로 변환
    
    Args:
        input_file (str): 입력 JSONL 파일 경로
        output_file (str): 출력 JSONL 파일 경로
        format_type (str): 변환할 형식 ("openai", "alpaca", "conversation")
    """
    
    def extract_conversation(data):
        """대화 데이터 추출"""
        content = data.get('talk', {}).get('content', {})
        
        # HS (Human Speech)와 SS (System Speech) 순서대로 정렬
        conversations = []
        for i in range(1, 4):  # HS01~HS03, SS01~SS03
            human_key = f"HS{i:02d}"
            system_key = f"SS{i:02d}"
            
            if human_key in content and system_key in content:
                conversations.append({
                    "human": content[human_key],
                    "assistant": content[system_key]
                })
        
        return conversations
    
    def get_persona_context(data):
        """페르소나 정보 추출"""
        profile = data.get('profile', {})
        emotion = profile.get('emotion', {})
        
        context = f"당신은 공감적이고 도움이 되는 상담사입니다. "
        context += f"상대방의 감정 상태는 '{emotion.get('type', '')}'이며, "
        context += f"상황은 '{emotion.get('situation', [])}'입니다. "
        context += "상대방의 감정을 이해하고 적절한 조언을 제공해주세요."
        
        return context
    
    converted_data = []
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    data = json.loads(line.strip())
                    conversations = extract_conversation(data)
                    context = get_persona_context(data)
                    
                    if format_type == "openai":
                        # OpenAI GPT 파인튜닝 형식
                        for conv in conversations:
                            converted_data.append({
                                "messages": [
                                    {"role": "system", "content": context},
                                    {"role": "user", "content": conv["human"]},
                                    {"role": "assistant", "content": conv["assistant"]}
                                ]
                            })
                    
                    elif format_type == "alpaca":
                        # Alpaca 형식
                        for conv in conversations:
                            converted_data.append({
                                "instruction": context,
                                "input": conv["human"],
                                "output": conv["assistant"]
                            })
                    
                    elif format_type == "conversation":
                        # 일반적인 대화 형식
                        for conv in conversations:
                            converted_data.append({
                                "context": context,
                                "question": conv["human"],
                                "answer": conv["assistant"]
                            })
                    
                    elif format_type == "multi_turn":
                        # 멀티턴 대화 형식
                        if conversations:
                            messages = [{"role": "system", "content": context}]
                            for conv in conversations:
                                messages.append({"role": "user", "content": conv["human"]})
                                messages.append({"role": "assistant", "content": conv["assistant"]})
                            converted_data.append({"messages": messages})
                
                except json.JSONDecodeError:
                    print(f"Line {line_num}: JSON 파싱 오류")
                    continue
        
        # 변환된 데이터를 JSONL로 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in converted_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        print(f"변환 완료: {len(converted_data)}개의 샘플 생성")
        print(f"출력 파일: {output_file}")
        
    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {input_file}")
    except Exception as e:
        print(f"오류 발생: {e}")



if __name__ == "__main__":
    input_file = "output.jsonl"
    
    # 다양한 형식으로 변환
    formats = ["openai"] # , "alpaca", "conversation", "multi_turn"
    
    for fmt in formats:
        output_file = f"finetune_{fmt}.jsonl"
        convert_to_finetune_format(input_file, output_file, fmt)
        print(f"\n{fmt.upper()} 형식 변환 완료\n" + "="*50)
    
    # 결과 확인
    print("\n변환 결과 미리보기:")
    try:
        with open("finetune_openai.jsonl", 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= 2:  # 처음 2개 샘플만 보여주기
                    break
                data = json.loads(line)
                print(f"\nSample {i+1}:")
                print(json.dumps(data, ensure_ascii=False, indent=2))
    except FileNotFoundError:
        print("변환된 파일을 찾을 수 없습니다.")