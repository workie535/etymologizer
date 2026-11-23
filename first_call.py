from dotenv import load_dotenv
import anthropic

load_dotenv()  # reads your .env file

client = anthropic.Anthropic()  # finds your key automatically

message = client.messages.create(
    model="claude-haiku-5-5",
    max_tokens=500,
    messages=[
        {"role": "user", "content": "In two sentences, what makes Gothic architecture recognizable?"}
    ],
)

print(message.content[0].text)