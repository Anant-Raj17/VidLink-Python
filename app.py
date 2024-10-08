from flask import Flask, request, jsonify, render_template
from models import Session, add_video, get_video, get_all_videos, delete_video
from youtube_utils import get_video_id, get_transcript_and_process, get_video_title
from groq import Groq
import os
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()
app = Flask(__name__)
CORS(app)
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_video', methods=['POST'])
def add_youtube_video():
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400

    data = request.get_json()
    if 'url' not in data:
        return jsonify({"error": "Missing 'url' in JSON data"}), 400

    url = data['url']
    video_id = get_video_id(url)

    session = Session()
    existing_video = get_video(session, video_id)

    if existing_video:
        session.close()
        return jsonify({"message": "Video already exists in database"}), 200

    full_transcript, summary, chunks = get_transcript_and_process(video_id)
    if full_transcript and summary and chunks:
        try:
            video_title = get_video_title(video_id)
        except Exception as e:
            video_title = "Title unavailable"
            print(f"Error getting video title: {str(e)}")

        add_video(session, video_id, video_title, full_transcript, summary, chunks)
        session.close()
        return jsonify({"message": "Video processed and added successfully", "title": video_title}), 201
    else:
        session.close()
        return jsonify({"message": "Couldn't retrieve or process transcript"}), 400

@app.route('/ask_question', methods=['POST'])
def ask_question():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    if 'question' not in data:
        return jsonify({"error": "Missing 'question' in JSON data"}), 400

    question = data['question']

    session = Session()
    videos = get_all_videos(session)

    if not videos:
        session.close()
        return jsonify({"answer": "There are no videos in the database to answer questions from."}), 200

    # Combine all video summaries
    combined_context = " ".join([str(video.summary) for video in videos])

    # Prepare the prompt for Groq AI
    prompt = f"Context: {combined_context}\n\nQuestion: {question}\n\nAnswer:"

    try:
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on the given context from multiple YouTube video summaries."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant",
            max_tokens=500
        )

        answer = response.choices[0].message.content
        session.close()
        return jsonify({"answer": answer}), 200
    except Exception as e:
        session.close()
        print(f"Error in Groq API call: {str(e)}")
        return jsonify({"error": f"Error processing question: {str(e)}"}), 500

@app.route('/get_videos', methods=['GET'])
def get_videos():
    session = Session()
    videos = get_all_videos(session)
    session.close()
    return jsonify({"videos": [{"id": v.id, "title": v.title} for v in videos]}), 200

@app.route('/delete_video/<int:video_id>', methods=['DELETE'])
def delete_video_route(video_id):
    session = Session()
    success = delete_video(session, video_id)
    session.close()
    if success:
        return jsonify({"message": "Video deleted successfully"}), 200
    else:
        return jsonify({"error": "Video not found"}), 404

if __name__ == '__main__':
       app.run(debug=True, host='0.0.0.0', port=8080)
