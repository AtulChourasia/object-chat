from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model, UserMixin):
    """User model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with chat sessions
    chat_sessions = db.relationship('ChatSession', back_populates='user', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class ChatSession(db.Model):
    """Model for storing chat sessions"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    object_name = db.Column(db.String(64), nullable=False)
    title = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='chat_sessions')
    messages = db.relationship('ChatMessage', back_populates='chat_session', cascade='all, delete-orphan', order_by='ChatMessage.timestamp')
    
    # Object persona stored as JSON
    _persona = db.Column(db.Text)
    
    @property
    def persona(self):
        """Get the persona as a dictionary"""
        if self._persona:
            return json.loads(self._persona)
        return None
    
    @persona.setter
    def persona(self, value):
        """Store the persona as JSON"""
        if value is None:
            self._persona = None
        else:
            self._persona = json.dumps(value)
    
    def __repr__(self):
        return f'<ChatSession {self.id}: {self.object_name}>'

class ChatMessage(db.Model):
    """Model for storing individual chat messages"""
    id = db.Column(db.Integer, primary_key=True)
    chat_session_id = db.Column(db.Integer, db.ForeignKey('chat_session.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    chat_session = db.relationship('ChatSession', back_populates='messages')
    
    def __repr__(self):
        return f'<ChatMessage {self.id}: {self.role}>'
