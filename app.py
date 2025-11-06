# app.py
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

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

    if not log_snippet:
        return jsonify({"error": "No log provided"}), 400

    try:
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
          "recommendation": "Short actionable advice for the analyst"
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

        # Try to parse JSON
        import json
        result = json.loads(response.text)
        return jsonify(result)

    except Exception as e:
        return jsonify({
            "error": "Analysis failed",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)