from flask import *
from flask_login import LoginManager, current_user, UserMixin, login_user, logout_user, login_required

from dotenv import load_dotenv
import bcrypt

import os
import boto3


load_dotenv(override=True)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_PROJECT_ID = os.getenv("OPENAI_API_PROJECT_ID")

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
BUCKET_NAME = os.getenv("BUCKET_NAME")

FLASK_LOGIN_SECRET = os.getenv("FLASK_LOGIN_SECRET")
DYNAMODB_TABLE_NAME = "UserNotes"

from pythonFunctions import *
import markdown

from io import BytesIO

imageCache={}
markdownCache={}


app = Flask(__name__)
app.config['SECRET_KEY'] = FLASK_LOGIN_SECRET

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Initialize DynamoDB
dynamodb = boto3.resource(
    "dynamodb",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)
user_table = dynamodb.Table(DYNAMODB_TABLE_NAME)



# User Model for Flask-Login
class User(UserMixin):
    def __init__(self, email):
        self.id = email

@login_manager.user_loader
def load_user(email):
    response = user_table.get_item(Key={"email": email})
    user_data = response.get("Item")
    if user_data:
        return User(email=user_data["email"])
    return None

# Hash Password Function
def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

# Verify Password Function
def check_password(password, hashed):
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

# User Registration Route
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]

        if(user_table.get_item(Key={"email": email}).get("Item")):
            return """
            <p>Error: Email already exists</p>
            <a class="btn btn-primary" href="/login" role="button">Log in</a>
            <a class="btn btn-secondary" href="/register" role="button">Register</a>
            """
        else:
            password = request.form["password"]
            # Hash Password
            password_hash = hash_password(password)
            # Store in DynamoDB
            registerAttempt=user_table.put_item(Item={"email": email, "password_hash": password_hash})

            return """
            <p>Account created successfully! Please log in.</p>
            <a class="btn btn-primary" href="/login" role="button">Log in</a>
            """

    return render_template("register.html")

# User Login Route
@app.route("/login", methods=["GET", "POST"])
def login():
    global imageCache
    imageCache={}
    global markdownCache
    markdownCache={}
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # Fetch user details from DynamoDB
        response = user_table.get_item(Key={"email": email})
        user_data = response.get("Item")

        # Check if user exists and verify the password
        if user_data and check_password(password, user_data["password_hash"]):
            user = User(email=user_data["email"])
            login_user(user)
            return redirect("/")
        else:
            return("Invalid email or password")

    return render_template("login.html")


# Dashboard Route (Protected)
@app.route("/dashboard")
@login_required
def dashboard():
    return f"Hello, {current_user.id}! Welcome to your dashboard."

# Logout Route
@app.route("/logout")
@login_required
def logout():
    global imageCache
    imageCache={}
    global markdownCache
    markdownCache={}
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


OpenAIClient = openai.OpenAI(
  organization='org-9TmA6PyMH2ZihJtThj58RMZT',
  project=OPENAI_API_PROJECT_ID,
)

s3_client = boto3.client('s3',
                         aws_access_key_id=AWS_ACCESS_KEY_ID,
                         aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                         region_name=AWS_REGION)



@app.route("/")
@login_required
def home():
    return render_template("/index.html")

@app.route("/notes")
def notes():
    return render_template("/notes.html")


@app.route("/uploadImageQueryForparsing", methods=["POST"])
@login_required
def uploadImageQueryForparsing():
    image = request.files["image"]
    id = request.values["markdownID"]
    user_email=current_user.id
    
    # Generate markdown from the image
    markdownResponse = createNewParsedImageChat(OpenAIClient, image)
    
    # Upload the markdown file (expects a string)
    markdownCache[id] = markdownResponse
    upload_file(user_email+"/"+"markDowns/" + id + ".md", markdownResponse, s3_client, BUCKET_NAME)
    
    # Upload the image file (use a proper image extension and pass bytes)
    # Reset the stream pointer to the beginning if needed.
    image.seek(0)
    imageCache[id] = image.read()
    image.seek(0)
    upload_file(user_email+"/"+"images/" + id + ".jpg", image.read(), s3_client, BUCKET_NAME)
    
    # Convert markdown to HTML and return
    htmlForm = markdown.markdown(markdownResponse)
    print(htmlForm)
    print(id)
    return htmlForm
    
@app.route("/downloadMarkdown", methods=["GET"])
@login_required
def downloadMarkdown():
    user_email=current_user.id
    if(request.args['markdownID'] not in markdownCache):
        filename = user_email+"/"+"markDowns/"+request.args['markdownID']+".md"
        markdownResponse =  download_file(filename,s3_client,BUCKET_NAME)
        if(markdownResponse != None):
            htmlForm = markdown.markdown(markdownResponse)
            markdownCache[request.args['markdownID']] = markdownResponse
            print(htmlForm)
            print(id)
            return(htmlForm)
        else:
            return "Markdown not found"
    else:
        return(markdown.markdown((markdownCache[request.args['markdownID']])))

@app.route("/downloadImage", methods=["GET"])
@login_required
def downloadImage():
    if(request.args['imageID'] not in imageCache):
        user_email=current_user.id
        filename = user_email+"/"+"images/"+request.args['imageID']+".jpg"
        imageResponse =  download_file(filename,s3_client,BUCKET_NAME)
        if(imageResponse != None):
            imageCache[request.args['imageID']] = imageResponse
            return """
            <img src="data:image/jpeg;base64,{}" style="width: auto; height: 100%;" />
            """.format(base64.b64encode(imageResponse).decode("utf-8"),)
        else:
            return "Image not found"
    else:
        return """
        <img src="data:image/jpeg;base64,{}" style="width: auto; height: 100%;" />
        """.format(base64.b64encode(imageCache[request.args['imageID']]).decode("utf-8"),)

@app.route("/deleteImageAndMarkdown", methods=["POST"])
@login_required
def deleteImageAndMarkdown():
    user_email=current_user.id
    if(request.form["dataID"] in imageCache):
        del imageCache[request.form["dataID"]]
        del markdownCache[request.args['markdownID']]
    imageName = user_email+"/"+"images/"+request.form["dataID"]+".jpg"

    markDownName = user_email+"/"+"markDowns/"+request.form["dataID"]+".md"
    imageResponse=delete_file(imageName,s3_client,BUCKET_NAME)
    markDownResponse=delete_file(markDownName,s3_client,BUCKET_NAME)
    if(imageResponse and markDownResponse):
        return "Deleted"
    else:
        return "Failed"

@app.route("/getAllData", methods=["GET"])
@login_required
def getAllData():
    user_email=current_user.id
    onlineMarkdowns=[key.split("/")[2] for key in getDirectoryFiles(user_email+"/"+"markDowns",s3_client,BUCKET_NAME)]
    onlineImages=[key.split("/")[2] for key in getDirectoryFiles(user_email+"/"+"images",s3_client,BUCKET_NAME)]
    return """
    <html>
    <head>
        <title>All Data</title>
    </head>
    <body>
        <h1>Cached Markdown</h1>
        <ul>
    {}
        </ul>
        <h1>Online Markdown</h1>
        <ul>
    {}
        </ul>
        <h1>Cached Images</h1>
        <ul>
    {}
        </ul>
        <h1>Online Images</h1>
        <ul>
    {}
        </ul>
    </body>
    </html>
    """.format(
        "\n".join("<li>{}</li>".format(key) for key in markdownCache),
        "\n".join("<li>{}</li>".format(key) for key in onlineMarkdowns if key not in [key+".md" for key in markdownCache]),
        "\n".join("<li>{}</li>".format(key) for key in imageCache),
        "\n".join("<li>{}</li>".format(key) for key in onlineImages if key not in [key+".jpg" for key in imageCache]),
    )

@app.route("/getOnlineMarkdown", methods=["GET"])
@login_required
def get_online_markdown():
    user_email = current_user.id  # current user's email
    prefix = f"{user_email}/markDowns/"
    
    # Retrieve files under the current user's markdown folder.
    files = getDirectoryFiles(prefix, s3_client, BUCKET_NAME)
    
    # Remove the prefix and the ".md" suffix from each key.
    online_markdowns = [ key[len(prefix):-3] for key in files ]
    
    return jsonify(online_markdowns)


@app.route("/notes/<note_id>")
def show_note(note_id):
    # Convert underscores back to spaces if needed
    # (Assuming your S3 keys use spaces, e.g., "Page 6")
    note_name = note_id.replace("_", " ")
    filename = "markDowns/" + note_name + ".md"
    md_content = download_file(filename, s3_client, BUCKET_NAME)
    if md_content:
        html_content = markdown.markdown(md_content)
    else:
        html_content = "<p>Markdown not found</p>"
    # Render the same notes.html template, passing the content
    return render_template("notes.html", note_content=html_content, active_note=note_name)


@app.route("/createNote", methods=["POST"])
@login_required
def create_note():
    data = request.get_json()
    note_name = data.get("note_name")
    if not note_name:
        return jsonify({"success": False, "error": "No note name provided."})
    
    user_email = current_user.id  # current user's email
    # Sanitize the note name: trim whitespace and replace spaces with underscores.
    sanitized_name = note_name.strip().replace(" ", "_")
    
    # Define the initial content for the markdown note
    initial_content = f"# {note_name}\n\n"
    
    # Build the S3 key using the user folder, the markdown folder, and the sanitized note name.
    s3_key = f"{user_email}/markDowns/{sanitized_name}.md"
    
    try:
        s3_client.put_object(Bucket=BUCKET_NAME, Key=s3_key, Body=initial_content)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    
    return jsonify({"success": True, "note_name": note_name})



if __name__ == "__main__":
        app.run(host="0.0.0.0", port=5000,debug=True)