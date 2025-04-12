import os
import datetime
import subprocess

def backup_database():
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("DATABASE_URL not found in environment")
        return
    
    # Parse the URL to get connection details
    # Format: postgresql://username:password@host:port/database
    parts = database_url.replace('postgresql://', '').split('@')
    credentials = parts[0].split(':')
    username = credentials[0]
    password = credentials[1] if len(credentials) > 1 else ''
    
    host_parts = parts[1].split('/')
    host_port = host_parts[0].split(':')
    host = host_port[0]
    port = host_port[1] if len(host_port) > 1 else '5432'
    database = host_parts[1].split('?')[0]  # Remove query parameters if any
    
    # Create backup filename with timestamp
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"backup_{database}_{timestamp}.sql"
    
    # Set PGPASSWORD environment variable
    os.environ['PGPASSWORD'] = password
    
    # Run pg_dump command
    cmd = f"pg_dump -h {host} -p {port} -U {username} -d {database} -f {backup_file}"
    subprocess.run(cmd, shell=True)
    
    print(f"Backup created: {backup_file}")

if __name__ == '__main__':
    backup_database()
