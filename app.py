from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import db, User, Video, add_video, get_video, get_all_videos, delete_video
from youtube_utils import get_video_id, get_transcript_and_process, get_video_title
from groq import Groq
import os
from dotenv import load_dotenv
from flask_cors import CORS
from markdown2 import Markdown

load_dotenv()  # This line is now near the top of the file

markdowner = Markdown()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback_secret_key")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///vidlink.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)
CORS(app)
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # type: ignore

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.get_by_username(username)
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        return 'Invalid username or password'
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.get_by_username(username):
            return 'Username already exists'
        user = User(username)
        user.set_password(password)
        user.save()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/add_video', methods=['POST'])
@login_required
def add_youtube_video():
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400

    data = request.get_json()
    if 'url' not in data:
        return jsonify({"error": "Missing 'url' in JSON data"}), 400

    url = data['url']
    video_id = get_video_id(url)

    existing_video = get_video(video_id)

    if existing_video:
        return jsonify({"message": "Video already exists in database"}), 200

    full_transcript, summary, chunks = get_transcript_and_process(video_id)
    if full_transcript and summary and chunks:
        try:
            video_title = get_video_title(video_id)
        except Exception as e:
            video_title = "Title unavailable"
            print(f"Error getting video title: {str(e)}")

        add_video(video_id, video_title, full_transcript, summary, chunks)
        return jsonify({"message": "Video processed and added successfully", "title": video_title}), 201
    else:
        return jsonify({"message": "Couldn't retrieve or process transcript"}), 400

@app.route('/ask_question', methods=['POST'])
@login_required
def ask_question():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    if 'question' not in data:
        return jsonify({"error": "Missing 'question' in JSON data"}), 400

    question = data['question']

    try:
        videos = get_all_videos()

        if not videos:
            return jsonify({"answer": "There are no videos in the database to answer questions from."}), 200

        video_summaries = [f"Video: {video.title}\nSummary: {video.summary}" for video in videos]

        prompt = f"""You have access to summaries of multiple YouTube videos. Analyze each video summary separately to answer the following question:

Question: {question}

Video Summaries:
{"\n\n".join(video_summaries)}

Please provide an answer based on the information from these video summaries. Use Markdown formatting in your response to enhance readability. Use bullet points, emphasis, or other Markdown features as appropriate."""

        groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an AI assistant that analyzes multiple YouTube video summaries. Your task is to answer questions by comparing and contrasting information from different videos, providing insights based on the content of each video separately."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant",
            max_tokens=500
        )

        answer = response.choices[0].message.content
        if answer is None:
            return jsonify({"error": "No response generated"}), 500

        html_answer = markdowner.convert(answer)

        return jsonify({"answer": html_answer}), 200
    except Exception as e:
        app.logger.error(f"Error processing question: {str(e)}")
        return jsonify({"error": f"Error processing question: {str(e)}"}), 500

@app.route('/get_videos', methods=['GET'])
@login_required
def get_videos():
    videos = get_all_videos()
    return jsonify({"videos": [{"id": str(v.id), "title": v.title} for v in videos]}), 200

@app.route('/delete_video/<video_id>', methods=['DELETE'])
@login_required
def delete_video_route(video_id):
    success = delete_video(video_id)
    if success:
        return jsonify({"message": "Video deleted successfully"}), 200
    else:
        return jsonify({"error": "Video not found"}), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=8080)
