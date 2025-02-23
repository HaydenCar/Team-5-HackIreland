from flask import Flask, request, render_template, send_from_directory
import os

app = Flask(__name__)

# Ensure uploads directory exists
os.makedirs("uploads", exist_ok=True)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return "No file uploaded", 400

    file = request.files["file"]
    if file.filename == "":
        return "No file selected", 400

    # Save the uploaded file
    file_path = os.path.join("uploads", file.filename)
    file.save(file_path)

    return render_template("view.html", image_url=file_path)


# Serve uploaded files
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory("uploads", filename)


if __name__ == "__main__":
    app.run(debug=True)
