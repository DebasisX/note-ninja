from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
import os
from werkzeug.utils import secure_filename
from docx import Document
from pdfminer.high_level import extract_text
import google.generativeai as genai

app = Flask(__name__)

# Configure Gemini AI
genai.configure(api_key="AIzaSyCWXsoDyEzYnXUZ6kkXSW7pQAMcukt5gTc")
model = genai.GenerativeModel('gemini-pro')

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'wav'}
AUDIO_FILE = os.path.join(UPLOAD_FOLDER, "recorded_audio.wav")

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(filepath):
    ext = filepath.rsplit('.', 1)[1].lower()
    try:
        if ext == 'txt':
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        elif ext == 'docx':
            doc = Document(filepath)
            return '\n'.join([para.text for para in doc.paragraphs])
        elif ext == 'pdf':
            return extract_text(filepath)
        return ""
    except Exception as e:
        raise Exception(f"Error extracting text: {str(e)}")

def generate_summary(text):
    try:
        prompt = """Please provide a detailed summary of the following transcipt in bullet points. 
        Focus on key points, main arguments, and important details. Avoid technical jargon and don't use asterisk
        instead use numbering like 1: this is a point \n 2: this is another point. \n  
        And use newline for each point
        :\n"""
        response = model.generate_content(prompt + text) 
        result_string = response.text.replace("**", "") 
        return result_string
    except Exception as e:
        return f"Summary error: {str(e)}"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/transcribe", methods=["POST"])
def transcribe():
    if "audio_data" not in request.files:
        return jsonify({"error": "No audio file uploaded"}), 400

    audio_file = request.files["audio_data"]
    audio_file.save(AUDIO_FILE)

    if not os.path.exists(AUDIO_FILE) or os.path.getsize(AUDIO_FILE) == 0:
        return jsonify({"error": "Invalid audio file"}), 400

    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(AUDIO_FILE) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)
            summary = generate_summary(text)
    except Exception as e:
        text = f"Error processing audio: {str(e)}"
        summary = text


    return jsonify({"text": summary})

@app.route("/upload", methods=["POST"])
def upload_files():
    if 'files' not in request.files:
        return jsonify({"error": "No files uploaded"}), 400
    
    files = request.files.getlist('files')
    results = []
    
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            
            try:
                text = extract_text_from_file(save_path)
                summary = generate_summary(text) if text else "No text extracted"
                results.append({
                    "filename": filename,
                    "summary": summary,
                    "status": "success"
                })
            except Exception as e:
                results.append({
                    "filename": filename,
                    "summary": str(e),
                    "status": "error"
                })

    return jsonify({
        "message": "Processing complete",
        "results": results
    })

if __name__ == "__main__":
    app.run(debug=True)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
   