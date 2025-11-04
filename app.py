import gradio as gr
import os
from utils import (
    load_prompt,
    prepare_image_messages,
    extract_dashboard_json,
    remove_dashboard_tags,
    format_json_for_display,
    CANVAS_INSTRUCTION,
    client
)

# Phase state management: 1=Image upload, 2=DR generation and refinement, 3=UX Issue evaluation
phase_state = {
    "current": 1,
    "images": None,  # Stores uploaded images
    "dr_json": None,  # DR JSON generated in Phase 2
}

def start_dr_generation(images, progress=gr.Progress(track_tqdm=True)):
    """Phase 1 -> Phase 2: DR Generation Start"""
    print("\n" + "="*60)
    print("🔘 BUTTON CLICKED: Generate Design Representation")
    print("⏳ STATUS: Starting DR generation process...")
    print("="*60 + "\n")

    progress(0, desc="Processing images...")

    print(f"[DEBUG] Received images: {images}")
    print(f"[DEBUG] Images type: {type(images)}")

    if not images or len(images) == 0:
        print("[DEBUG] No images provided")
        return (
            gr.update(),  # phase1 keep
            gr.update(),  # phase2 keep
            gr.update(),  # phase3 keep
            "",
            []
        )

    # Gradio File component returns file path list
    # Each element might be a dictionary ({"name": "...", "data": "..."})
    image_paths = []
    if isinstance(images, list):
        for img in images:
            if isinstance(img, str):
                image_paths.append(img)
            elif isinstance(img, dict) and "name" in img:
                image_paths.append(img["name"])
            else:
                image_paths.append(str(img))
    else:
        image_paths = [images]

    print(f"[DEBUG] Processed image paths: {image_paths}")

    phase_state["current"] = 2
    phase_state["images"] = image_paths

    progress(0.2, desc="Loading prompts...")

    # Load system prompt
    try:
        system_prompt = load_prompt("prompt_dr_generator.md") + CANVAS_INSTRUCTION
        print("[DEBUG] System prompt loaded successfully")
    except Exception as e:
        print(f"[ERROR] Failed to load prompt: {e}")
        raise

    progress(0.4, desc="Encoding images...")

    # Prepare images
    try:
        image_contents = prepare_image_messages(image_paths)
        print(f"[DEBUG] Prepared {len(image_contents)} images for API")
    except Exception as e:
        print(f"[ERROR] Failed to prepare images: {e}")
        raise

    # Initial message (Responses API format)
    # System prompt passed via instructions parameter
    user_content = [
        {"type": "input_text", "text": "Here are the screenshots of a mobile app task flow. Please analyze them and generate the Design Representation JSON."}
    ] + image_contents

    initial_input = [
        {
            "role": "user",
            "content": user_content
        }
    ]

    print("[DEBUG] Calling OpenAI Responses API...")
    progress(0.6, desc="AI analysis in progress... (1-2 minutes)")

    # OpenAI Responses API call (using instructions parameter)
    try:
        response = client.responses.create(
            model="gpt-4o",
            instructions=system_prompt,
            input=initial_input
        )
        print("[DEBUG] API call successful")
        progress(0.9, desc="Processing results...")

        # Responses API uses response.output_text
        assistant_response = response.output_text
        print(f"[DEBUG] Response length: {len(assistant_response)} characters")

        # Extract JSON
        dr_json = extract_dashboard_json(assistant_response)
        chat_message = remove_dashboard_tags(assistant_response)

        # If no JSON found, display entire response in dashboard
        if dr_json is None:
            dr_json = assistant_response
            chat_message = "Design Representation has been generated. Please let me know if you'd like to make any modifications!"

        # Save state
        phase_state["dr_json"] = dr_json

        # Format for dashboard display
        dashboard_content = format_json_for_display(dr_json)

        # Chat history (save initial message including images)
        chat_history = [
            {
                "role": "user",
                "content": "Here are the screenshots. Please analyze them and generate the Design Representation JSON."
            },
            {
                "role": "assistant",
                "content": chat_message if chat_message else "Design Representation has been generated. Please let me know if you'd like to make any modifications!"
            }
        ]

        print("\n" + "="*60)
        print("✅ SUCCESS: DR generation completed")
        print("="*60 + "\n")

        return (
            gr.update(visible=False),  # Hide phase1
            gr.update(visible=True),   # Show phase2
            gr.update(visible=False),  # Keep phase3 hidden
            dashboard_content,
            chat_history
        )

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[ERROR] Exception in start_dr_generation: {error_details}")

        error_message = f"""# Error

**Error Type:** {type(e).__name__}

**Error Message:** {str(e)}

**Possible Solutions:**
1. Check if OPENAI_API_KEY is set correctly
2. Verify internet connection
3. Check if the model 'gpt-5-nano' is available in your account

**For Development:** Check terminal for full traceback
"""
        return (
            gr.update(visible=True),   # Keep phase1 visible
            gr.update(visible=False),  # Hide phase2
            gr.update(visible=False),  # Hide phase3
            error_message,
            [{"role": "assistant", "content": str(e)}]
        )

def chat_dr(message, history, dashboard_content):
    """Phase 2: DR Generator와 대화"""
    print("\n" + "="*60)
    print("💬 CHAT INPUT SUBMITTED: DR Generator")
    print(f"⏳ STATUS: Processing user message...")
    print(f"📝 Message: {message[:100]}..." if len(message) > 100 else f"📝 Message: {message}")
    print("="*60 + "\n")

    if not message:
        return history, dashboard_content

    # Load system prompt
    system_prompt = load_prompt("prompt_dr_generator.md") + CANVAS_INSTRUCTION

    # Include current JSON state in context
    context_message = f"""Current Dashboard JSON:
```json
{dashboard_content}
```

User message: {message}
"""

    # Build complete conversation history (Responses API format)
    input_messages = []

    # Add existing history
    for msg in history:
        input_messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    # Add new user message
    input_messages.append({
        "role": "user",
        "content": context_message
    })

    # Call OpenAI Responses API (using instructions parameter)
    try:
        response = client.responses.create(
            model="gpt-4o",
            instructions=system_prompt,
            input=input_messages
        )

        assistant_response = response.output_text

        # Check for <dashboard> tags
        updated_json = extract_dashboard_json(assistant_response)
        chat_message = remove_dashboard_tags(assistant_response)

        # If feedback (JSON update)
        if updated_json is not None:
            phase_state["dr_json"] = updated_json
            updated_dashboard = format_json_for_display(updated_json)
        else:
            # If question (maintain dashboard)
            updated_dashboard = dashboard_content
            chat_message = assistant_response

        # Update history
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": chat_message})

        print("\n" + "="*60)
        print("✅ SUCCESS: DR chat response completed")
        print("="*60 + "\n")

        return history, updated_dashboard

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": error_msg})
        return history, dashboard_content

def confirm_dr(dashboard_content, progress=gr.Progress(track_tqdm=True)):
    """Phase 2 -> Phase 3: Confirm DR and Start UX Issue Evaluation"""
    print("\n" + "="*60)
    print("🔘 BUTTON CLICKED: Confirm DR and Start UX Issue Analysis")
    print("⏳ STATUS: Starting UX Issue evaluation process...")
    print("="*60 + "\n")

    progress(0, desc="Preparing UX Issue analysis...")

    phase_state["current"] = 3

    # Load system prompt
    system_prompt = load_prompt("prompt_heuristic_evaluator.md") + CANVAS_INSTRUCTION
    progress(0.3, desc="Preparing images and DR data...")

    # Prepare images (reuse images saved from Phase 1)
    image_contents = prepare_image_messages(phase_state["images"])

    # Convert DR JSON to string
    dr_json_str = format_json_for_display(phase_state["dr_json"])

    # Initial message (Responses API format)
    user_content = [
        {"type": "input_text", "text": f"""Here are the screenshots and the task flow description JSON:

Task Flow JSON:
```json
{dr_json_str}
```

Please conduct heuristic evaluation and generate UX issues JSON."""}
    ] + image_contents

    initial_input = [
        {
            "role": "user",
            "content": user_content
        }
    ]

    progress(0.5, desc="Conducting heuristic evaluation... (1-2 minutes)")

    # OpenAI Responses API call (using instructions parameter)
    try:
        response = client.responses.create(
            model="gpt-4o",
            instructions=system_prompt,
            input=initial_input
        )

        progress(0.9, desc="Processing results...")
        assistant_response = response.output_text

        # Extract JSON
        ux_json = extract_dashboard_json(assistant_response)
        chat_message = remove_dashboard_tags(assistant_response)

        # If no JSON found, display entire response in dashboard
        if ux_json is None:
            ux_json = assistant_response
            chat_message = "UX Issue analysis is complete. Please let me know if you have any questions or would like to make modifications!"

        # Format for dashboard display
        dashboard_content = format_json_for_display(ux_json)

        # Chat history
        ux_chat_history = [
            {
                "role": "user",
                "content": "Please analyze the task flow and generate UX issues."
            },
            {
                "role": "assistant",
                "content": chat_message if chat_message else "UX Issue analysis is complete. Please let me know if you have any questions or would like to make modifications!"
            }
        ]

        print("\n" + "="*60)
        print("✅ SUCCESS: UX Issue evaluation completed")
        print("="*60 + "\n")

        return (
            gr.update(visible=False),  # Hide phase2
            gr.update(visible=True),   # Show phase3
            dashboard_content,
            ux_chat_history
        )

    except Exception as e:
        error_message = f"Error: {str(e)}"
        return (
            gr.update(visible=False),
            gr.update(visible=True),
            error_message,
            [{"role": "assistant", "content": error_message}]
        )

def chat_ux(message, history, dashboard_content):
    """Phase 3: Heuristic Evaluator와 대화"""
    print("\n" + "="*60)
    print("💬 CHAT INPUT SUBMITTED: Heuristic Evaluator")
    print(f"⏳ STATUS: Processing user message...")
    print(f"📝 Message: {message[:100]}..." if len(message) > 100 else f"📝 Message: {message}")
    print("="*60 + "\n")

    if not message:
        return history, dashboard_content

    # 시스템 프롬프트 로드
    system_prompt = load_prompt("prompt_heuristic_evaluator.md") + CANVAS_INSTRUCTION

    # 현재 JSON 상태를 컨텍스트에 포함
    context_message = f"""Current UX Issues JSON:
```json
{dashboard_content}
```

User message: {message}
"""

    # Build complete conversation history (Responses API format)
    input_messages = []

    # Add existing history
    for msg in history:
        input_messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    # Add new user message
    input_messages.append({
        "role": "user",
        "content": context_message
    })

    # Call OpenAI Responses API (using instructions parameter)
    try:
        response = client.responses.create(
            model="gpt-4o",
            instructions=system_prompt,
            input=input_messages
        )

        assistant_response = response.output_text

        # <dashboard> 태그 확인
        updated_json = extract_dashboard_json(assistant_response)
        chat_message = remove_dashboard_tags(assistant_response)

        # 피드백인 경우 (JSON 업데이트)
        if updated_json is not None:
            updated_dashboard = format_json_for_display(updated_json)
        else:
            # 질문인 경우 (대시보드 유지)
            updated_dashboard = dashboard_content
            chat_message = assistant_response

        # 히스토리 업데이트
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": chat_message})

        print("\n" + "="*60)
        print("✅ SUCCESS: UX chat response completed")
        print("="*60 + "\n")

        return history, updated_dashboard

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": error_msg})
        return history, dashboard_content

def download_ux_issues(dashboard_content):
    """UX 이슈 다운로드"""
    print("\n" + "="*60)
    print("🔘 BUTTON CLICKED: Download UX Issues")
    print("⏳ STATUS: Preparing download file...")
    print("="*60 + "\n")

    import tempfile
    import json

    # Save as JSON file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        # If dashboard_content is already a JSON string
        if isinstance(dashboard_content, str):
            try:
                # Validate JSON format
                json_obj = json.loads(dashboard_content)
                json.dump(json_obj, f, indent=2, ensure_ascii=False)
            except:
                # If not JSON, save as plain text
                f.write(dashboard_content)
        else:
            json.dump(dashboard_content, f, indent=2, ensure_ascii=False)

        print("\n" + "="*60)
        print("✅ SUCCESS: Download file prepared")
        print(f"📁 File path: {f.name}")
        print("="*60 + "\n")

        return f.name

def reset_app():
    """앱 초기화"""
    print("\n" + "="*60)
    print("🔘 BUTTON CLICKED: Reset")
    print("⏳ STATUS: Resetting application to initial state...")
    print("="*60 + "\n")

    phase_state["current"] = 1
    phase_state["images"] = None
    phase_state["dr_json"] = None

    print("\n" + "="*60)
    print("✅ SUCCESS: Application reset completed")
    print("="*60 + "\n")

    return (
        gr.update(visible=True),   # Show phase1
        gr.update(visible=False),  # Hide phase2
        gr.update(visible=False),  # Hide phase3
        None,  # Clear images
        "",    # Clear dashboard2
        [],    # Clear chatbot2
        "",    # Clear dashboard3
        []     # Clear chatbot3
    )

# Custom CSS for fixed-height dashboards
CUSTOM_CSS = """
#dashboard2-code textarea, #dashboard2-code pre {
    height: 600px !important;
    max-height: 600px !important;
    overflow-y: auto !important;
}
#dashboard3-code textarea, #dashboard3-code pre {
    height: 600px !important;
    max-height: 600px !important;
    overflow-y: auto !important;
}
"""

# Gradio interface configuration
with gr.Blocks(title="2-Phase UX Evaluation System", css=CUSTOM_CSS) as demo:

    # Title (always visible)
    gr.Markdown("# Mobile App UX Evaluation System")
    gr.Markdown("## 2-Phase Heuristic Evaluation Service")

    # Phase 1: Image upload
    with gr.Column(visible=True) as phase1:
        gr.Markdown("---")
        gr.Markdown("## Step 1: Screenshot Upload")

        with gr.Row():
            with gr.Column(scale=3):
                gr.Markdown("### 🖼️ Preview")
                image_preview = gr.Gallery(
                    label="Uploaded Screenshots",
                    show_label=True,
                    columns=5,
                    preview=True,
                    height=600
                )
            with gr.Column(scale=1):
                gr.Markdown("### 📸 Image")
                image_input = gr.File(
                    label="Upload mobile app screenshots here",
                    file_count="multiple",
                    file_types=["image"],
                    type="filepath",
                    height=600
                )
        generate_btn = gr.Button("✅ Generate Design Representation", variant="primary", size="lg", scale=2)


    # Phase 2: DR Generation and Refinement
    with gr.Column(visible=False) as phase2:
        gr.Markdown("---")
        gr.Markdown("## Step 2: Design Representation Generation and Refinement")

        with gr.Row():
            # Left: Dashboard
            with gr.Column(scale=1):
                gr.Markdown("### 📊 Design Representation Dashboard")
                dashboard2 = gr.Code(
                    value="",
                    language="json",
                    interactive=False,
                    show_label=False,
                    elem_id="dashboard2-code"
                )

            # Right: DR Generator chatbot
            with gr.Column(scale=1):
                gr.Markdown("### 💬 DR Generator")
                chatbot2 = gr.Chatbot(
                    [],
                    height=600,
                    show_label=False,
                    type="messages"
                )

                chat_input2 = gr.Textbox(
                    placeholder="Provide feedback on the Design Representation...",
                    show_label=False,
                    scale=4
                )

        confirm_dr_btn = gr.Button("✅ Confirm DR and Start UX Issue Analysis", variant="primary", size="lg")
        reset_btn = gr.Button("🔄 Reset", variant="secondary")

    # Phase 3: UX Issue Evaluation
    with gr.Column(visible=False) as phase3:
        gr.Markdown("---")
        gr.Markdown("## Step 3: UX Issue Evaluation")

        with gr.Row():
            # Left: Dashboard
            with gr.Column(scale=1):
                gr.Markdown("### 📊 UX Issue Dashboard")
                dashboard3 = gr.Code(
                    value="",
                    language="json",
                    interactive=False,
                    show_label=False,
                    elem_id="dashboard3-code"
                )

            # Right: Heuristic Evaluator chatbot
            with gr.Column(scale=1):
                gr.Markdown("### 💬 Heuristic Evaluator")
                chatbot3 = gr.Chatbot(
                    [],
                    height=600,
                    show_label=False,
                    type="messages"
                )

                chat_input3 = gr.Textbox(
                    placeholder="Provide feedback on the UX Issues...",
                    show_label=False,
                    scale=4
                )

        download_btn = gr.Button("📥 Download UX Issues", variant="secondary", size="lg")
        reset_btn = gr.Button("🔄 Reset", variant="secondary")

    # Event handlers

    # Update preview when images are uploaded
    image_input.change(
        fn=lambda files: files if files else [],
        inputs=[image_input],
        outputs=[image_preview]
    )

    # Start DR generation (Phase 1 -> Phase 2)
    generate_btn.click(
        fn=start_dr_generation,
        inputs=[image_input],
        outputs=[phase1, phase2, phase3, dashboard2, chatbot2],
        show_progress="full",
        api_name="start_dr_generation"
    )

    # Phase 2: Chat with DR Generator
    chat_input2.submit(
        fn=chat_dr,
        inputs=[chat_input2, chatbot2, dashboard2],
        outputs=[chatbot2, dashboard2]
    ).then(
        fn=lambda: "",
        outputs=[chat_input2]
    )

    # Confirm DR (Phase 2 -> Phase 3)
    confirm_dr_btn.click(
        fn=confirm_dr,
        inputs=[dashboard2],
        outputs=[phase2, phase3, dashboard3, chatbot3],
        show_progress="full"
    )

    # Phase 3: Chat with Heuristic Evaluator
    chat_input3.submit(
        fn=chat_ux,
        inputs=[chat_input3, chatbot3, dashboard3],
        outputs=[chatbot3, dashboard3]
    ).then(
        fn=lambda: "",
        outputs=[chat_input3]
    )

    # Download UX issues
    download_btn.click(
        fn=download_ux_issues,
        inputs=[dashboard3],
        outputs=[gr.File()]
    )

    # Reset application
    reset_btn.click(
        fn=reset_app,
        outputs=[phase1, phase2, phase3, image_input, dashboard2, chatbot2, dashboard3, chatbot3]
    )

if __name__ == "__main__":
    demo.launch(share=False, server_name="0.0.0.0", server_port=7860)
