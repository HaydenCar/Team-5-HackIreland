import openai
import base64
def createNewTextChat(client,chatRequest):
    output=""
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": chatRequest}],
        stream=True,
    )
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            output += chunk.choices[0].delta.content

    return output

import base64

def createNewImageChat(client, image_file):
    # Convert image to base64
    image_data = base64.b64encode(image_file.read()).decode("utf-8")

    # Call OpenAI's vision model
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an AI that can process text on images."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Please respond with only the text you can read, with no other text."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
                ],
            },
        ],
    )

    # Extract and return the response
    return response.choices[0].message.content

def createNewParsedImageChat(client, image_file):
    # Convert image to base64
    image_data = base64.b64encode(image_file.read()).decode("utf-8")

    # Call OpenAI's vision model
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an AI that can process text on images and turn them into markdown."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Please respond with a markdown form of the text of the image I've given you, tidied up and made more presentable. Only include the content of the markdown in the output, Do not include the surrounding brackets or such. Do not include any images."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
                ],
            },
        ],
    )
    print(response.choices[0].message.content)
    # Extract and return the response
    return response.choices[0].message.content


