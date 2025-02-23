from flask import *
from flask_login import LoginManager, current_user, UserMixin, login_user, logout_user, login_required
from dotenv import load_dotenv
import bcrypt
import os
import boto3
import base64
import io
import markdown
from io import BytesIO
from werkzeug.utils import secure_filename  # needed for upload_temp
import tempfile  # for getting a reliable temp directory
import openai  # ensure openai is imported

# Load environment variables
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
# (Assuming createNewParsedImageChat, upload_file, download_file, delete_file, getDirectoryFiles, etc. are defined)

imageCache = {}
markdownCache = {}

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
        if user_table.get_item(Key={"email": email}).get("Item"):
            return """
            <p>Error: Email already exists</p>
            <a class="btn btn-primary" href="/login" role="button">Log in</a>
            <a class="btn btn-secondary" href="/register" role="button">Register</a>
            """
        else:
            password = request.form["password"]
            password_hash = hash_password(password)
            user_table.put_item(Item={"email": email, "password_hash": password_hash})
            return """
            <p>Account created successfully! Please log in.</p>
            <a class="btn btn-primary" href="/login" role="button">Log in</a>
            """
    return render_template("register.html")

# User Login Route
@app.route("/login", methods=["GET", "POST"])
def login():
    global imageCache, markdownCache
    imageCache = {}
    markdownCache = {}
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        response = user_table.get_item(Key={"email": email})
        user_data = response.get("Item")
        if user_data and check_password(password, user_data["password_hash"]):
            user = User(email=user_data["email"])
            login_user(user)
            return redirect("/")
        else:
            return "Invalid email or password"
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
    global imageCache, markdownCache
    imageCache = {}
    markdownCache = {}
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

OpenAIClient = openai.OpenAI(
    organization='org-9TmA6PyMH2ZihJtThj58RMZT',
    project=OPENAI_API_PROJECT_ID,
)

s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

@app.route("/")
@login_required
def home():
    return render_template("index.html")

@app.route("/AR")
def AR():
    return render_template("AR.html")

@app.route("/notes")
def notes():
    return render_template("notes.html")

@app.route("/uploadImageQueryForparsing", methods=["POST"])
@login_required
def uploadImageQueryForparsing():
    user_email = current_user.id
    markdown_id = request.values.get("markdownID")
    if not markdown_id:
        return jsonify({"error": "Markdown ID is required"}), 400

    if "image" in request.files:
        image = request.files["image"]
        image_format = "jpg"
        image_bytes = image.read()
    elif "image_base64" in request.form:
        image_data = request.form["image_base64"]
        try:
            image_data = image_data.split(",")[1]
            image_bytes = base64.b64decode(image_data)
            image_format = "jpg"
        except Exception as e:
            return jsonify({"error": f"Invalid base64 format: {str(e)}"}), 400
    else:
        return jsonify({"error": "No image provided"}), 400

    image_io = io.BytesIO(image_bytes)
    markdownResponse = createNewParsedImageChat(OpenAIClient, image_io)

    markdown_key = f"{user_email}/markDowns/{markdown_id}.md"
    markdownCache[markdown_key] = markdownResponse
    upload_file(markdown_key, markdownResponse, s3_client, BUCKET_NAME)

    image_key = f"{user_email}/images/{markdown_id}.{image_format}"
    upload_file(image_key, image_bytes, s3_client, BUCKET_NAME)
    imageCache[image_key] = image_bytes

    return jsonify({
        "message": "VR image uploaded successfully",
        "markdown_url": f"https://{BUCKET_NAME}.s3.amazonaws.com/{markdown_key}",
        "image_url": f"https://{BUCKET_NAME}.s3.amazonaws.com/{image_key}"
    })

@app.route("/downloadMarkdown", methods=["GET"])
@login_required
def downloadMarkdown():
    user_email = current_user.id
    markdown_id = request.args.get("markdownID")
    if not markdown_id:
        return jsonify({"error": "Markdown ID is required"}), 400
    markdown_key = f"{user_email}/markDowns/{markdown_id}.md"
    if markdown_key not in markdownCache:
        markdownResponse = download_file(markdown_key, s3_client, BUCKET_NAME)
        if markdownResponse:
            markdownCache[markdown_key] = markdownResponse
        else:
            return "Markdown not found", 404
    return markdown.markdown(markdownCache[markdown_key])

@app.route("/downloadImage", methods=["GET"])
@login_required
def downloadImage():
    if request.args['imageID'] not in imageCache:
        user_email = current_user.id
        filename = f"{user_email}/images/{request.args['imageID']}.jpg"
        imageResponse = download_file(filename, s3_client, BUCKET_NAME)
        if imageResponse is not None:
            imageCache[request.args['imageID']] = imageResponse
            return f"""
            <img src="data:image/jpeg;base64,{base64.b64encode(imageResponse).decode('utf-8')}" style="width: auto; height: 100%;" />
            """
        else:
            return "Image not found"
    else:
        return f"""
        <img src="data:image/jpeg;base64,{base64.b64encode(imageCache[request.args['imageID']]).decode('utf-8')}" style="width: auto; height: 100%;" />
        """

@app.route("/deleteImageAndMarkdown", methods=["POST"])
@login_required
def deleteImageAndMarkdown():
    user_email = current_user.id
    if request.form["dataID"] in imageCache:
        del imageCache[request.form["dataID"]]
        del markdownCache[request.args['markdownID']]
    imageName = f"{user_email}/images/{request.form['dataID']}.jpg"
    markDownName = f"{user_email}/markDowns/{request.form['dataID']}.md"
    imageResponse = delete_file(imageName, s3_client, BUCKET_NAME)
    markDownResponse = delete_file(markDownName, s3_client, BUCKET_NAME)
    if imageResponse and markDownResponse:
        return "Deleted"
    else:
        return "Failed"

@app.route("/getAllData", methods=["GET"])
@login_required
def getAllData():
    user_email = current_user.id
    user_markdowns = getDirectoryFiles(f"{user_email}/markDowns", s3_client, BUCKET_NAME)
    user_images = getDirectoryFiles(f"{user_email}/images", s3_client, BUCKET_NAME)
    markdown_list = [key.split("/")[-1] for key in user_markdowns]
    image_list = [key.split("/")[-1] for key in user_images]
    return jsonify({
        "cached_markdowns": list(markdownCache.keys()),
        "online_markdowns": markdown_list,
        "cached_images": list(imageCache.keys()),
        "online_images": image_list
    })

@app.route("/getOnlineMarkdown", methods=["GET"])
@login_required
def get_online_markdown():
    user_email = current_user.id
    prefix = f"{user_email}/markDowns/"
    files = getDirectoryFiles(prefix, s3_client, BUCKET_NAME)
    online_markdowns = [ key[len(prefix):-3] for key in files ]
    return jsonify(online_markdowns)

@app.route("/notes/<note_id>")
@login_required
def show_note(note_id):
    note_name = note_id.replace("_", " ")
    user_email = current_user.id
    s3_key = f"{user_email}/markDowns/{note_name.replace(' ', '_')}.md"
    md_content = download_file(s3_key, s3_client, BUCKET_NAME)
    if md_content:
        html_content = markdown.markdown(md_content)
    else:
        html_content = "<p>Markdown not found</p>"
    # Pass the note_id as active_note_id for use in the modal
    return render_template("notes.html", note_content=html_content, active_note=note_name, active_note_id=note_id)


@app.route("/createNote", methods=["POST"])
@login_required
def create_note():
    data = request.get_json()
    note_name = data.get("note_name")
    if not note_name:
        return jsonify({"success": False, "error": "No note name provided."})
    user_email = current_user.id
    sanitized_name = note_name.strip().replace(" ", "_")
    initial_content = f"# {note_name}\n\n"
    s3_key = f"{user_email}/markDowns/{sanitized_name}.md"
    try:
        s3_client.put_object(Bucket=BUCKET_NAME, Key=s3_key, Body=initial_content)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    return jsonify({"success": True, "note_name": note_name})

@app.route("/uploadTemp", methods=["POST"])
@login_required
def upload_temp():
    image_file = request.files.get("image")
    note_id = request.form.get("noteID")
    if not image_file or not note_id:
        flash("Image or Note ID is missing", "error")
        return redirect(url_for("home"))
    
    # Use the OS temporary directory
    temp_dir = tempfile.gettempdir()
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    filename = secure_filename(image_file.filename)
    temp_path = os.path.join(temp_dir, filename)
    image_file.save(temp_path)
    flash("Image uploaded to temp folder!", "success")
    
    # Redirect to the highlight page using the saved filename as the image ID
    return redirect(url_for("highlight", imageID=filename, noteID=note_id))


# NEW: Highlight endpoint
@app.route("/highlight")
@login_required
def highlight():
    image_id = request.args.get("imageID")
    note_id = request.args.get("noteID")
    if not image_id or not note_id:
        flash("Image ID and Note ID are required", "error")
        return redirect(url_for("notes"))
    user_email = current_user.id
    image_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{user_email}/images/{image_id}.jpg"
    return render_template("highlight.html", image_url=image_url, image_id=image_id, note_id=note_id)

if __name__ == "__main__":
    try:
        from pyngrok import ngrok
        # Open a tunnel on port 5000 and get a public URL
        public_url = ngrok.connect(5000)
        print(" * ngrok tunnel available at:", public_url)
    except ImportError:
        print(" * pyngrok is not installed. To install, run 'pip install pyngrok'")
    app.run(host="0.0.0.0", port=5008, debug=False)

