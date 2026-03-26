import os
import base64
from io import BytesIO

from flask import Flask, request, jsonify, render_template
from PIL import Image
import anthropic
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    image = Image.open(file.stream)

    # Remove alpha channel if present
    image = image.convert("RGB")

    # Resize to max 1024px to keep API payload small
    image.thumbnail((1024, 1024))

    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    image_data = base64.standard_b64encode(buffer.getvalue()).decode("utf-8")

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "You are a Pinterest content creator. "
                            "Look at this image and write a short, engaging Pinterest-style caption for it. "
                            "Include 3-5 relevant hashtags at the end. "
                            "Keep the tone warm, inspiring, and relatable — the way a real Pinterest user would write. "
                            "Just return the caption and hashtags, nothing else."
                        ),
                    },
                ],
            }
        ],
    )

    caption = message.content[0].text
    return jsonify({"caption": caption})


if __name__ == "__main__":
    app.run(debug=True)
