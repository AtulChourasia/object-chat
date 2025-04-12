import os
import tempfile
import json
from app import app, db
from models import User, ChatSession, ChatMessage

# Handle Google Cloud credentials in production
if os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON'):
    # Write the credentials to a temporary file
    creds_dict = json.loads(os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON'))
    creds_file = tempfile.NamedTemporaryFile(delete=False)
    with open(creds_file.name, 'w') as f:
        json.dump(creds_dict, f)
    
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_file.name
    print(f"Google Cloud credentials written to temporary file: {creds_file.name}")

# Create an admin user for initial access
def setup_database():
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Check if admin user exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@example.com')
            admin.set_password(os.getenv('ADMIN_PASSWORD', 'changeme123'))
            db.session.add(admin)
            db.session.commit()
            print("Admin user created")
        else:
            print("Admin user already exists")

if __name__ == '__main__':
    # Run database setup
    setup_database()
