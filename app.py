# app.py
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
from dotenv import load_dotenv
import openrouter

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Use Gemini 2.0 Flash (as of Oct 2025, model name is likely 'gemini-2.0-flash-exp')
# If not available, fall back to 'gemini-1.5-flash'
MODEL_NAME = "gemini-2.0-flash-exp"  # or try "gemini-1.5-flash" if 2.0 isn't public yet

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_log():
    data = request.json
    log_snippet = data.get("log", "").strip()
    model_choice = data.get("model", "gemini")

    if not log_snippet:
        return jsonify({"error": "No log provided"}), 400

    try:
        if model_choice == 'gemini':
            model = genai.GenerativeModel(MODEL_NAME)
            prompt = f"""
            You are an expert cybersecurity analyst in a Security Operations Center (SOC).
            Analyze the following log entry for potential threats:

            LOG: {log_snippet}

            Respond in this exact JSON format:
            {{
              "threat_detected": true or false,
              "threat_type": "e.g., Brute Force, DDoS, Malware, Suspicious IP, or None",
              "confidence": "High / Medium / Low",
              "recommendation": "Short actionable advice for the analyst",
              "how_to_do": "A small paragraph with easy to understand, practical instructions on how to solve the issue."
            }}
            """

            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    max_output_tokens=500,
                    temperature=0.3
                )
            )

            import json
            result = json.loads(response.text)
            return jsonify(result)

        elif model_choice in ['deepseek', 'qwen']:
            if not OPENROUTER_API_KEY:
                return jsonify({"error": "OpenRouter API key is not configured on the server"}), 400

            client = openrouter.Client(api_key=OPENROUTER_API_KEY)
            model_name = "deepseek/deepseek-chat-v3.1:free" if model_choice == 'deepseek' else "qwen/qwen3-coder:free"

            prompt = f"""
            You are an expert cybersecurity analyst in a Security Operations Center (SOC).
            Analyze the following log entry for potential threats:

            LOG: {log_snippet}

            Respond in this exact JSON format:
            {{
              "threat_detected": true or false,
              "threat_type": "e.g., Brute Force, DDoS, Malware, Suspicious IP, or None",
              "confidence": "High / Medium / Low",
              "recommendation": "Short actionable advice for the analyst",
              "how_to_do": "A small paragraph with easy to understand, practical instructions on how to solve the issue."
            }}
            """

            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a cybersecurity expert."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )

            import json
            result = json.loads(response.choices[0].message.content)
            return jsonify(result)

    except Exception as e:
        return jsonify({
            "error": "Analysis failed",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
