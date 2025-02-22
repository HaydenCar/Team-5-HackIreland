import openai
from flask import request, Flask, render_template, jsonify
from botocore.exceptions import ClientError
import base64
import io
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

def upload_file(filename, fileContent, s3_client, BUCKET_NAME):
    if filename.endswith('.md'):
        # Upload markdown file (expects a string, so we encode it)
        print(s3_client.put_object(
            Body=io.BytesIO(fileContent.encode('utf-8')),
            Bucket=BUCKET_NAME,
            Key=filename,
            ContentType='text/markdown'
        ))
        return jsonify({'message': 'File uploaded successfully'}), 200
    if filename.endswith('.jpg'):
        # Upload image file (expects bytes, no need to encode)
        print(s3_client.put_object(
            Body=io.BytesIO(fileContent),
            Bucket=BUCKET_NAME,
            Key=filename,
            ContentType='image/jpg'
        ))
        return jsonify({'message': 'File uploaded successfully'}), 200

    return jsonify({'error': 'Incompatible file type'}), 400

    
def download_file(filename, s3_client, BUCKET_NAME):
    try:
        if filename.endswith('.md'):
            s3_response = s3_client.get_object(Bucket=BUCKET_NAME, Key=filename)
            file_content = s3_response['Body'].read().decode('utf-8')
            # You can also set response headers if you want to force a download
            return file_content
        if filename.endswith('.jpg'):
            s3_response = s3_client.get_object(Bucket=BUCKET_NAME, Key=filename)
            file_content = s3_response['Body'].read()
            return file_content
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            return jsonify({'error': 'File not found'}), 404

def delete_file(filename, s3_client, BUCKET_NAME):
    try:
        s3_client.delete_object(Bucket=BUCKET_NAME, Key=filename)
        return jsonify({'message': 'File deleted successfully'}), 200
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            return jsonify({'error': 'File not found'}), 404