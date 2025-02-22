from flask import request, Flask, render_template, jsonify

from dotenv import load_dotenv

import os
import boto3

from python_backend.API_KEYS import OPENAI_API_KEY, OPENAI_API_PROJECT_ID

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_PROJECT_ID = os.getenv("OPENAI_API_PROJECT_ID")

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
BUCKET_NAME = os.getenv("BUCKET_NAME")

from pythonFunctions import *
import markdown

from io import BytesIO

imageCache={}
markdownCache={}


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



    
@app.route("/uploadImageQueryForparsing", methods=["POST"])
def uploadImageQueryForparsing():
    image = request.files["image"]
    id = request.values["markdownID"]
    
    # Generate markdown from the image
    markdownResponse = createNewParsedImageChat(OpenAIClient, image)
    
    # Upload the markdown file (expects a string)
    markdownCache[id] = markdownResponse
    upload_file("markDowns/" + id + ".md", markdownResponse, s3_client, BUCKET_NAME)
    
    # Upload the image file (use a proper image extension and pass bytes)
    # Reset the stream pointer to the beginning if needed.
    image.seek(0)
    imageCache[id] = image.read()
    image.seek(0)
    upload_file("images/" + id + ".jpg", image.read(), s3_client, BUCKET_NAME)
    
    # Convert markdown to HTML and return
    htmlForm = markdown.markdown(markdownResponse)
    print(htmlForm)
    print(id)
    return htmlForm
    
@app.route("/downloadMarkdown", methods=["GET"])
def downloadMarkdown():
    if(request.args['markdownID'] not in markdownCache):
        filename = "markDowns/"+request.args['markdownID']+".md"
        markdownResponse =  download_file(filename,s3_client,BUCKET_NAME)
        htmlForm = markdown.markdown(markdownResponse)
        markdownCache[request.args['markdownID']] = markdownResponse
        print(htmlForm)
        print(id)
        return(htmlForm)
    else:
        return(markdown.markdown((markdownCache[request.args['markdownID']])))

@app.route("/downloadImage", methods=["GET"])
def downloadImage():
    if(request.args['imageID'] not in imageCache):
        filename = "images/"+request.args['imageID']+".jpg"
        imageResponse =  download_file(filename,s3_client,BUCKET_NAME)
        imageCache[request.args['imageID']] = imageResponse
        return """
        <img src="data:image/jpeg;base64,{}" style="width: auto; height: 100%;" />
        """.format(base64.b64encode(imageResponse).decode("utf-8"),)
    else:
        return """
        <img src="data:image/jpeg;base64,{}" style="width: auto; height: 100%;" />
        """.format(base64.b64encode(imageCache[request.args['imageID']]).decode("utf-8"),)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000,debug=True)