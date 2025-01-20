# Python Flask Web
import os
from flask import Flask, render_template, request, url_for
from werkzeug.utils import secure_filename

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from configparser import ConfigParser
import time

# Config Parser
config = ConfigParser()
config.read("config.ini")
genai.configure(api_key=config["Gemini"]["API_KEY"])

UPLOAD_FOLDER = "static/data"
ALLOWED_EXTENSIONS = set(["mp4","mov","avi","webm","wmv","3gp","flv","mpg","mpeg"])

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# gemini-2.0-flash-exp
# gemini-1.5-flash-latest
gemini_model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp",
    safety_settings={
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    },
    generation_config={
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
    },
    system_instruction="請用繁體中文回答以下問題。",
)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    print("Submit!")
    if request.method == "POST":
        if "file1" not in request.files:
            print("No file part")
            return render_template("index.html")
        file = request.files["file1"]
        if file.filename == "":
            print("No selected file")
            return render_template("index.html")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            print(filename)
            global video_file_gemini
            video_file_gemini = upload_to_gemini(filename)
            result = "檔案已上傳成功! 並提供給Gemini處理完畢. 可以開始問問題囉!"
        return render_template(
            "index.html",
            prediction=result,
            filename=filename,
        )
    else:
        return render_template("index.html", prediction="Method not allowed")

@app.route("/call_gemini", methods=["POST"])
def call_gemini():
    if request.method == "POST":
        print("POST!")
        data = request.form
        print(data["message"])
        prompt = data["message"]
        response = gemini_model.generate_content(
            [prompt, video_file_gemini], request_options={"timeout": 600}
        )
        print(response)
        return response.text


def upload_to_gemini(filename):
    print(f"Uploading file...")
    video_file = genai.upload_file(path=f"static/data/{filename}")
    print(f"Completed upload: {video_file}")
    while video_file.state.name == "PROCESSING":
        print("Waiting for video to be processed.")
        time.sleep(1)
        video_file = genai.get_file(video_file.name)

    if video_file.state.name == "FAILED":
        raise ValueError(video_file.state.name)
    print(f"Video processing complete: " + video_file.uri)
    return video_file

if __name__ == "__main__":
    app.run()