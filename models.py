from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()

class Video(Base):
    __tablename__ = 'videos'
    id = Column(Integer, primary_key=True)
    youtube_id = Column(String(20), unique=True, nullable=False)
    title = Column(String(200))
    full_transcript = Column(Text)
    summary = Column(Text)
    chunks = relationship("SummaryChunk", back_populates="video")

class SummaryChunk(Base):
    __tablename__ = 'summary_chunks'
    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey('videos.id'))
    chunk_text = Column(Text)
    video = relationship("Video", back_populates="chunks")

engine = create_engine('sqlite:///youtube_transcripts.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def add_video(session, youtube_id, title, full_transcript, summary, chunks):
    video = Video(youtube_id=youtube_id, title=title, full_transcript=full_transcript, summary=summary)
    session.add(video)
    session.flush()  # This will assign an ID to the video

    for chunk in chunks:
        summary_chunk = SummaryChunk(video_id=video.id, chunk_text=chunk)
        session.add(summary_chunk)

    session.commit()

def get_video(session, youtube_id):
    return session.query(Video).filter_by(youtube_id=youtube_id).first()

def get_all_videos(session):
    return session.query(Video).all()

def delete_video(session, video_id):
    video = session.query(Video).get(video_id)
    if video:
        session.delete(video)
        session.commit()
        return True
    return False
