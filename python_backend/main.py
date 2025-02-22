from flask import request, Flask, render_template

from API_KEYS import *
from pythonFunctions import *
import markdown


app = Flask(__name__)

client = openai.OpenAI(
  organization='org-9TmA6PyMH2ZihJtThj58RMZT',
  project=OPENAI_API_PROJECT_ID,
)

@app.route("/")
def home():
    return render_template("/index.html")



@app.route("/uploadImageQuery", methods=["POST"])
def uploadImageQuery():
    image = request.files.get("file")
    if image:
        # Do something with the uploaded file
        return createNewImageChat(client, image)
    else:
        return "No file uploaded"
    
@app.route("/uploadImageQueryForparsing", methods=["POST"])
def uploadImageQueryForparsing():
    image = request.files.get("file")
    if image:
        markdownResponse = createNewParsedImageChat(client, image)
        htmlForm = markdown.markdown(markdownResponse)
        print(htmlForm)
        return(htmlForm)
    else:
        return "No file uploaded"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000,debug=True)

