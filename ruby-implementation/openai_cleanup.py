from openai import OpenAI
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def clean_text(text):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that formats and cleans up text.",
            },
            {
                "role": "user",
                "content": f"Please clean up and format the following text:\n\n{text}",
            },
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    # Read input text from command line
    input_text = sys.argv[1]
    cleaned_text = clean_text(input_text)
    print(cleaned_text)
