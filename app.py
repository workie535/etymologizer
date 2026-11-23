import base64
import json
from flask import Flask, request, jsonify, send_file
from dotenv import load_dotenv
import anthropic

load_dotenv()
client = anthropic.Anthropic()
app = Flask(__name__)

SYSTEM_PROMPT = """You are an architectural historian who traces the lineage of buildings from photographs.

Analyze the building in the photo. Identify the architectural styles and influences visible in it, and point to the specific visible features that show each one.

Be honest about certainty: some influences are unmistakable in a photo, while others are only suggested. Mark each claim with a confidence of "high", "medium", or "low", and never present a guess as a fact.

Respond with ONLY valid JSON, no other text, in exactly this shape:
{
  "summary": "One or two sentences describing the building overall.",
  "influences": [
    {
      "style": "Name of the style or influence",
      "origin": "Where and when this style came from",
      "confidence": "high, medium, or low",
      "evidence": ["Specific visible feature", "Another feature"],
      "explanation": "How these features connect the building to this style."
    }
  ],
  "caveats": "What can't be determined from this photo."
}"""

SUPPORTED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def analyze_image(image_bytes, media_type):
    """Send a photo to Claude and return the parsed analysis."""
    image_data = base64.standard_b64encode(image_bytes).decode("utf-8")

    message = client.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": media_type, "data": image_data},
                    },
                    {"type": "text", "text": "Analyze this building."},
                ],
            }
        ],
    )

    raw = "".join(block.text for block in message.content if block.type == "text").strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(raw)


@app.route("/")
def home():
    return send_file("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    photo = request.files.get("photo")

    if photo is None:
        return jsonify({"error": "No photo was received. Choose a photo and try again."}), 400
    if photo.mimetype not in SUPPORTED_TYPES:
        return jsonify({"error": "That file type isn't supported. Use a JPEG, PNG, WebP, or GIF."}), 400

    try:
        result = analyze_image(photo.read(), photo.mimetype)
    except json.JSONDecodeError:
        return jsonify({"error": "The analysis came back in an unreadable format. Try again."}), 502
    except anthropic.APIError as e:
        return jsonify({"error": f"The AI service returned an error: {e}"}), 502

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=8000)