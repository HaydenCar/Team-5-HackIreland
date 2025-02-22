from flask import request, Flask, render_template, jsonify

import os
import boto3

from API_KEYS import *
from pythonFunctions import *
import markdown
import random

from io import BytesIO


app = Flask(__name__)

OpenAIClient = openai.OpenAI(
  organization='org-9TmA6PyMH2ZihJtThj58RMZT',
  project=OPENAI_API_PROJECT_ID,
)

s3_client = boto3.client('s3',
                         aws_access_key_id=AWS_ACCESS_KEY_ID,
                         aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                         region_name=AWS_REGION)



@app.route("/")
def home():
    return render_template("/index.html")

@app.route("/notes")
def notes():
    return render_template("/notes.html")


@app.route("/uploadImageQuery", methods=["POST"])
def uploadImageQuery():
    image = request.files.get("file")
    if image:
        # Do something with the uploaded file
        return createNewImageChat(OpenAIClient, image)
    else:
        return "No file uploaded"
    
@app.route("/uploadImageQueryForparsing", methods=["POST"])
def uploadImageQueryForparsing():
    image = request.files.get("file")
    if image:
        id=str(random.random())[2:]
        markdownResponse = createNewParsedImageChat(OpenAIClient, image)
        upload_markdown("exampleMarkdowns/exampleMarkdown"+id+".md",markdownResponse,s3_client,BUCKET_NAME)
        htmlForm = markdown.markdown(markdownResponse)
        print(htmlForm)
        print(id)
        return(htmlForm)
    else:
        return "No file uploaded"
    
@app.route("/downloadMarkdown", methods=["GET"])
def downloadMarkdown():
    filename = "exampleMarkdowns/exampleMarkdown"+request.args['markdownID']+".md"
    markdownResponse =  download_markdown(filename,s3_client,BUCKET_NAME)
    htmlForm = markdown.markdown(markdownResponse)
    print(htmlForm)
    print(id)
    return(htmlForm)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000,debug=True)

