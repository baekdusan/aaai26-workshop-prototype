# Mobile App UX Evaluation System

**2-Phase Heuristic Evaluation Service**

A research prototype for evaluating mobile app user experience through AI-assisted heuristic evaluation. This system features a Canvas-mode interface where users can iteratively refine Design Representations and UX issue analyses through natural language conversation.

> **Note**: This is a prototype developed for the AAAI'26 Workshop submission.

## 🎯 Overview

This system implements a 2-phase evaluation workflow:

1. **Design Representation (DR) Generation**: Analyzes screenshots to create structured task flow descriptions
2. **Heuristic Evaluation**: Identifies UX issues based on established heuristic principles

The interface follows a Canvas-mode paradigm inspired by ChatGPT Canvas:
- **Left Panel**: Live-updating JSON dashboard
- **Right Panel**: Conversational AI agent for refinement and inquiry

## ✨ Key Features

### Screenshot Upload
- Support for multiple screenshot uploads (up to 16 images)
- Real-time image preview gallery
- Automatic image encoding for API transmission

### Design Representation Generation and Refinement
- **Dashboard (Left)**: Displays task flow JSON structure including:
  - Screen identification and purpose
  - User activities per screen
  - Interaction sequences
  - Navigational triggers
- **DR Generator (Right)**: Conversational agent that:
  - Responds to feedback by updating JSON
  - Answers questions without modifying JSON
  - Maintains conversation history

### UX Issue Evaluation
- **Dashboard (Left)**: Displays identified UX issues with:
  - Issue descriptions
  - Violated heuristic principles
  - Importance scores (1-7 scale)
  - Recommendations
- **Heuristic Evaluator (Right)**: Conversational agent that:
  - Refines issue descriptions based on feedback
  - Explains heuristic violations
  - Adjusts importance scores
- JSON export functionality for identified issues

## 🔧 Technical Architecture

### Core Technologies
- **Framework**: Gradio 5.x
- **LLM API**: OpenAI Responses API
- **Model**: GPT-5-nano (optimized for cost-efficiency)
- **Language**: Python 3.10+

### API Design
- Uses OpenAI's Responses API (latest generation)
- System prompts via `instructions` parameter
- Base64 image encoding for screenshot analysis
- Conversational context maintenance across turns

### Canvas Mode Implementation
The system employs a custom Canvas instruction that enables the LLM to:
1. Distinguish between modification requests and informational queries
2. Output JSON updates within `<dashboard>` tags when appropriate
3. Provide conversational responses for questions

## 📋 Requirements

- Python 3.10 or higher
- OpenAI API key with access to GPT-5-nano
- Dependencies listed in `requirements.txt`

## 🚀 Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/aaai26-workshop-prototype.git
cd aaai26-workshop-prototype
```

### 2. Create Virtual Environment

```bash
conda create -n aaai26 python=3.10 -y
conda activate aaai26
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Key

Set your OpenAI API key as an environment variable:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

Alternatively, create a `.env` file:

```bash
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

### 5. Run the Application

```bash
python app.py
```

The application will launch at `http://localhost:7860`

## 📁 Project Structure

```
.
├── app.py                              # Main Gradio application
├── utils.py                            # Utility functions (API calls, parsing)
├── requirements.txt                    # Python dependencies
├── prompt_dr_generator.md              # System prompt for DR Generator
├── prompt_heuristic_evaluator.md       # System prompt for Heuristic Evaluator
├── Agent4_Terms_and_definitions.md     # Reference: terminology definitions
├── Agent4_heuristics.md                # Reference: heuristic principles
└── README.md                           # This file
```

## 🎨 Usage Guide

### Step 1: Upload Screenshots
1. Navigate to the upload section
2. Select multiple screenshots showing a task flow (in sequence)
3. Click "Generate Design Representation"

### Step 2: Refine Design Representation
- **Review** the generated task flow JSON in the left dashboard
- **Interact** with the DR Generator via the chat interface:
  - **Feedback example**: "Make the screen_purpose more specific"
  - **Question example**: "What does user_activities represent?"
- Click "Confirm DR and Start UX Issue Analysis" when satisfied

### Step 3: Evaluate UX Issues
- **Review** identified UX issues in the left dashboard
- **Interact** with the Heuristic Evaluator:
  - **Feedback example**: "The importance_score seems too low"
  - **Question example**: "Why is this issue critical?"
- Click "Download UX Issues" to export the analysis

## 🤖 Canvas Mode Behavior

### Automatic Intent Recognition

The LLM automatically classifies user messages as either:

**Modification Request** → Updates JSON + Provides explanation
- Indicators: "change", "update", "fix", "modify", "make it more..."
- Output: `<dashboard>updated JSON</dashboard>` + explanation

**Informational Query** → Maintains JSON + Provides answer
- Indicators: "what", "why", "how", "explain", "tell me about..."
- Output: Conversational answer only

### Example Interactions

```
User: "Make the screen_purpose more detailed"
→ Dashboard: JSON updated with enhanced screen_purpose
→ Chat: "I've updated the screen_purpose to provide more detail."

User: "What does navigational_interaction mean?"
→ Dashboard: No change
→ Chat: "Navigational_interaction refers to the user action that..."
```

## 🔬 Customization

### Modifying Evaluation Criteria

Edit the prompt files to adjust evaluation logic:
- `prompt_dr_generator.md`: Customize DR structure and analysis approach
- `prompt_heuristic_evaluator.md`: Modify heuristic principles and severity criteria

### Changing the Model

Edit `app.py` to use different models:
```python
response = client.responses.create(
    model="gpt-5",  # Change to gpt-5, gpt-5-mini, etc.
    instructions=system_prompt,
    input=initial_input
)
```

### Adjusting Canvas Instructions

Modify `CANVAS_INSTRUCTION` in `utils.py` to change how the LLM handles updates vs. queries.

## 💰 Cost Considerations

**GPT-5-nano Pricing** (as of deployment):
- Input: $0.05 per 1M tokens
- Output: $0.40 per 1M tokens

**Typical Usage**:
- Initial DR generation: ~5,000-10,000 tokens (with images)
- Refinement turns: ~500-2,000 tokens each
- UX evaluation: ~8,000-15,000 tokens (with images)

**Estimated cost per full evaluation**: $0.01 - $0.05

## ⚠️ Limitations and Considerations

- **Image Limit**: Maximum 16 screenshots per evaluation (OpenAI API constraint)
- **Token Usage**: Images consume significant tokens via base64 encoding
- **Model Availability**: Requires access to GPT-5-nano model
- **Language**: Prompts are in English; UI labels in screenshots are preserved in original language
- **Evaluation Quality**: Dependent on screenshot quality and task flow clarity

## 📄 License

This project is released under the MIT License. See `LICENSE` file for details.

## 🤝 Contributing

This is a research prototype. For questions or collaboration inquiries, please contact [dusanisbaek@gmail.com].

## 🙏 Acknowledgments

- Built with [Gradio](https://gradio.app/)
- Powered by [OpenAI Responses API](https://platform.openai.com/docs/)
- Heuristic principles adapted from established HCI literature

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Status**: Research Prototype
