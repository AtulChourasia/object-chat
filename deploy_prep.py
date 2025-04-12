import os
import tempfile
import json
import traceback

print("Starting deploy_prep.py script...")

# Handle Google Cloud credentials in production
try:
    if os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON'):
        print("Found GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable")
        # Write the credentials to a temporary file
        creds_dict = json.loads(os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON'))
        creds_file = tempfile.NamedTemporaryFile(delete=False)
        with open(creds_file.name, 'w') as f:
            json.dump(creds_dict, f)
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_file.name
        print(f"Google Cloud credentials written to temporary file: {creds_file.name}")
    else:
        print("No GOOGLE_APPLICATION_CREDENTIALS_JSON found")
except Exception as e:
    print(f"Error setting up Google Cloud credentials: {e}")
    traceback.print_exc()
    print("Continuing with deployment despite credential error")

# Import app and models after setting up credentials
try:
    from app import app, db
    from models import User, ChatSession, ChatMessage
    print("Successfully imported app and models")
except Exception as e:
    print(f"Error importing app or models: {e}")
    traceback.print_exc()
    raise

# Create an admin user for initial access
def setup_database():
    try:
        print("Setting up database...")
        with app.app_context():
            # Create tables if they don't exist
            print("Creating database tables...")
            db.create_all()
            print("Database tables created successfully")
            
            # Check if admin user exists
            print("Checking for admin user...")
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                print(f"Creating admin user with password from environment variable")
                admin = User(username='admin', email='admin@example.com')
                admin.set_password(os.getenv('ADMIN_PASSWORD', 'changeme123'))
                db.session.add(admin)
                db.session.commit()
                print("Admin user created successfully")
            else:
                print("Admin user already exists")
    except Exception as e:
        print(f"Error setting up database: {e}")
        traceback.print_exc()
        raise

if __name__ == '__main__':
    try:
        # Run database setup
        setup_database()
        print("Database setup completed successfully")
    except Exception as e:
        print(f"Fatal error in deploy_prep.py: {e}")
        traceback.print_exc()
        # Exit with error code to signal deployment failure
        import sys
        sys.exit(1)
