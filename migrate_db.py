import os
import sqlite3
import psycopg2
from app import app, db
from models import User, ChatSession, ChatMessage
from datetime import datetime

def migrate_database():
    with app.app_context():
        # Create all tables in PostgreSQL
        db.create_all()
        
        # Check if we need to migrate data
        if os.path.exists('object_chat.db'):
            print("Found SQLite database, starting migration...")
            
            # Connect to SQLite
            sqlite_conn = sqlite3.connect('object_chat.db')
            sqlite_cursor = sqlite_conn.cursor()
            
            # Migrate users
            try:
                sqlite_cursor.execute("SELECT id, username, email, password_hash FROM user")
                users = sqlite_cursor.fetchall()
                for user in users:
                    id, username, email, password_hash = user
                    existing_user = User.query.filter_by(username=username).first()
                    if not existing_user:
                        new_user = User(id=id, username=username, email=email, password_hash=password_hash)
                        db.session.add(new_user)
                print(f"Migrated {len(users)} users")
            except Exception as e:
                print(f"Error migrating users: {e}")
            
            # Migrate chat sessions
            try:
                sqlite_cursor.execute("SELECT id, user_id, object_name, title, created_at, updated_at FROM chat_session")
                sessions = sqlite_cursor.fetchall()
                for session in sessions:
                    id, user_id, object_name, title, created_at, updated_at = session
                    existing_session = ChatSession.query.filter_by(id=id).first()
                    if not existing_session:
                        new_session = ChatSession(
                            id=id, 
                            user_id=user_id, 
                            object_name=object_name, 
                            title=title, 
                            created_at=created_at or datetime.utcnow(), 
                            updated_at=updated_at or datetime.utcnow()
                        )
                        db.session.add(new_session)
                print(f"Migrated {len(sessions)} chat sessions")
            except Exception as e:
                print(f"Error migrating chat sessions: {e}")
            
            # Migrate chat messages
            try:
                sqlite_cursor.execute("SELECT id, chat_session_id, role, content, timestamp FROM chat_message")
                messages = sqlite_cursor.fetchall()
                for message in messages:
                    id, chat_session_id, role, content, timestamp = message
                    existing_message = ChatMessage.query.filter_by(id=id).first()
                    if not existing_message:
                        new_message = ChatMessage(
                            id=id,
                            chat_session_id=chat_session_id,
                            role=role,
                            content=content,
                            timestamp=timestamp or datetime.utcnow()
                        )
                        db.session.add(new_message)
                print(f"Migrated {len(messages)} chat messages")
            except Exception as e:
                print(f"Error migrating chat messages: {e}")
            
            # Commit all changes
            db.session.commit()
            print("Migration completed successfully!")
            
            # Close SQLite connection
            sqlite_conn.close()
        else:
            print("No SQLite database found, creating fresh PostgreSQL database.")

if __name__ == '__main__':
    migrate_database()
