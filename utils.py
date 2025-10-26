"""
Utility functions for the UX Evaluation System
"""
import os
import base64
import json
import re
from openai import OpenAI

# OpenAI Client 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_prompt(filename):
    """프롬프트 파일 로드"""
    filepath = os.path.join(os.path.dirname(__file__), filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def encode_image_to_base64(image_path):
    """이미지를 base64로 인코딩"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def prepare_image_messages(image_paths):
    """여러 이미지를 OpenAI Responses API 형식으로 변환"""
    image_contents = []
    for img_path in image_paths:
        base64_image = encode_image_to_base64(img_path)
        image_contents.append({
            "type": "input_image",
            "image_url": f"data:image/jpeg;base64,{base64_image}"
        })
    return image_contents

def extract_dashboard_json(response_text):
    """응답에서 <dashboard> 태그 안의 JSON 추출"""
    match = re.search(r'<dashboard>(.*?)</dashboard>', response_text, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
        # JSON 코드 블록 제거 (```json ... ```)
        json_str = re.sub(r'^```json\s*', '', json_str)
        json_str = re.sub(r'\s*```$', '', json_str)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return json_str  # 파싱 실패 시 원본 반환
    return None

def remove_dashboard_tags(response_text):
    """응답에서 <dashboard> 태그 제거하고 채팅 메시지만 반환"""
    cleaned = re.sub(r'<dashboard>.*?</dashboard>', '', response_text, flags=re.DOTALL)
    return cleaned.strip()

def format_json_for_display(json_obj):
    """JSON을 보기 좋게 포맷팅"""
    if isinstance(json_obj, str):
        return json_obj
    return json.dumps(json_obj, indent=2, ensure_ascii=False)


# Canvas 모드 지시사항
CANVAS_INSTRUCTION = """

## Output Format (IMPORTANT):

Analyze the user's message and determine its type:

**Case 1: Feedback/Modification Request**
- User wants to change, update, or fix something in the JSON
- Examples: "Change the screen_purpose", "Add more details", "This is wrong", "Update this part"
- Your response MUST include:
  1. <dashboard>full updated JSON here</dashboard>
  2. Brief explanation of what you changed (outside the tags)

**Case 2: Question/Clarification**
- User is asking a question or seeking clarification
- Examples: "Why did you...", "What does this mean?", "Can you explain?", "Tell me more about..."
- Your response should ONLY be a conversational answer
- Do NOT output <dashboard> tags

**Important Notes:**
- Always provide COMPLETE JSON (not partial updates) when updating the dashboard
- Wrap JSON output with <dashboard> and </dashboard> tags
- Keep chat explanations concise and helpful
- You have already analyzed the screenshots at the beginning - refer to your initial analysis

**Example Response for Case 1:**
<dashboard>
{
  "task_scenario_id": "Updated Flow",
  "screens": [...]
}
</dashboard>

I've updated the screen_purpose for "Product List Screen" to better reflect the user's goal.

**Example Response for Case 2:**
The screen_purpose describes what the user is trying to accomplish on that particular screen. It focuses on the user's goal rather than just listing UI elements.
"""
