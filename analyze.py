import base64
import json
from dotenv import load_dotenv
import anthropic

load_dotenv()
client = anthropic.Anthropic()

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

# Read the photo and convert it into text the API can carry
with open("building.jpg", "rb") as f:
    image_data = base64.standard_b64encode(f.read()).decode("utf-8")

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
                    "source": {"type": "base64", "media_type": "image/jpeg", "data": image_data},
                },
                {"type": "text", "text": "Analyze this building."},
            ],
        }
    ],
)

# Collect the text blocks and clean up any code fences around the JSON
raw = "".join(block.text for block in message.content if block.type == "text").strip()
raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

result = json.loads(raw)

# Save the structured result for the interface to use later
with open("result.json", "w") as f:
    json.dump(result, f, indent=2)

# Print a readable version
print("\n" + result["summary"])

print("\nINFLUENCES")
for item in result["influences"]:
    print(f"\n• {item['style']} ({item['confidence']} confidence)")
    print(f"  Origin: {item['origin']}")
    print(f"  Evidence: {'; '.join(item['evidence'])}")
    print(f"  {item['explanation']}")

print("\nCAVEATS\n" + result["caveats"])