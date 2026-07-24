from datetime import datetime

from pgvector.sqlalchemy import Vector

from config.extensions.database_config import db



class Document(db.Model):

    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class DocumentChunk(db.Model):

    __tablename__ = "document_chunks"

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id"), nullable=False)
    chunk_number = db.Column(db.Integer,nullable=False)
    content = db.Column(db.Text,nullable=False)
    embedding = db.Column(Vector(384), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)