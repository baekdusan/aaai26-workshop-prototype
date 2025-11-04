"""
Utility functions for the UX Evaluation System
"""
import os
import base64
import json
import re
from openai import OpenAI

# Initialize OpenAI Client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_prompt(filename):
    """Load prompt file"""
    filepath = os.path.join(os.path.dirname(__file__), filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def encode_image_to_base64(image_path):
    """Encode image to base64"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def prepare_image_messages(image_paths):
    """Convert multiple images to OpenAI Responses API format"""
    image_contents = []
    for img_path in image_paths:
        base64_image = encode_image_to_base64(img_path)
        image_contents.append({
            "type": "input_image",
            "image_url": f"data:image/jpeg;base64,{base64_image}"
        })
    return image_contents

def extract_dashboard_json(response_text):
    """Extract JSON from within <dashboard> tags in response"""
    match = re.search(r'<dashboard>(.*?)</dashboard>', response_text, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
        # Remove JSON code block markers (```json ... ```)
        json_str = re.sub(r'^```json\s*', '', json_str)
        json_str = re.sub(r'\s*```$', '', json_str)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return json_str  # Return original string if parsing fails
    return None

def remove_dashboard_tags(response_text):
    """Remove <dashboard> tags from response and return only chat message"""
    cleaned = re.sub(r'<dashboard>.*?</dashboard>', '', response_text, flags=re.DOTALL)
    return cleaned.strip()

def format_json_for_display(json_obj):
    """Format JSON for display"""
    if isinstance(json_obj, str):
        return json_obj
    return json.dumps(json_obj, indent=2, ensure_ascii=False)


# Canvas mode instructions
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
