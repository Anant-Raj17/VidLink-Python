from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255))  # Increased from 128 to 255

    def __init__(self, username):
        self.username = username

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @classmethod
    def get(cls, user_id):
        return cls.query.get(int(user_id))

    @classmethod
    def get_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    def save(self):
        db.session.add(self)
        db.session.commit()

class Video(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    youtube_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    full_transcript: Mapped[str] = mapped_column(Text)
    summary: Mapped[str] = mapped_column(Text)
    chunks: Mapped[str] = mapped_column(Text)  # Changed from ARRAY(db.Text) to Text

    def __init__(self, youtube_id, title, full_transcript, summary, chunks):
        self.youtube_id = youtube_id
        self.title = title
        self.full_transcript = full_transcript
        self.summary = summary
        self.chunks = chunks

def add_video(youtube_id, title, full_transcript, summary, chunks):
    video = Video(youtube_id=youtube_id, title=title, full_transcript=full_transcript, summary=summary, chunks=chunks)
    db.session.add(video)
    db.session.commit()

def get_video(youtube_id):
    return Video.query.filter_by(youtube_id=youtube_id).first()

def get_all_videos():
    return Video.query.all()

def delete_video(video_id):
    video = Video.query.get(video_id)
    if video:
        db.session.delete(video)
        db.session.commit()
        return True
    return False
