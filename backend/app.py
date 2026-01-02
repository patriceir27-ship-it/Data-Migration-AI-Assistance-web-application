from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
import json
import threading
import time
from datetime import datetime
from migration_engine import MigrationEngine
from storage_checker import StorageChecker
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='../frontend', template_folder='../frontend')
CORS(app, resources={r"/*": {"origins": "*"}})

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 * 1024  # 50GB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MIGRATION_LOG'] = 'migration_logs.json'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('logs', exist_ok=True)

# Initialize services
migration_engine = MigrationEngine()
storage_checker = StorageChecker()

# Active migrations tracker
active_migrations = {}

@app.route('/')
def index():
    """Serve the main application page"""
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'DataFlow AI Migration Service',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/check-storage', methods=['POST'])
def check_storage():
    """Check storage capacity before migration"""
    try:
        data = request.json
        source_info = data.get('source')
        dest_info = data.get('destination')
        file_size = data.get('file_size', 0)
        
        logger.info(f"Checking storage: {source_info} -> {dest_info}")
        
        # Check source storage
        source_check = storage_checker.check_capacity(source_info, file_size)
        
        # Check destination storage
        dest_check = storage_checker.check_capacity(dest_info, file_size)
        
        # Check compatibility
        compatibility = migration_engine.check_compatibility(source_info, dest_info)
        
        return jsonify({
            'success': True,
            'source_check': source_check,
            'destination_check': dest_check,
            'compatibility': compatibility,
            'recommendations': storage_checker.get_recommendations(
                source_check, dest_check, compatibility
            )
        })
        
    except Exception as e:
        logger.error(f"Storage check error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/connect-device', methods=['POST'])
def connect_device():
    """Connect to a device/database"""
    try:
        data = request.json
        device_type = data.get('device_type')
        connection_params = data.get('connection_params', {})
        
        logger.info(f"Connecting to {device_type}: {connection_params}")
        
        # Simulate connection (in production, implement actual connection logic)
        time.sleep(1)  # Simulate connection time
        
        return jsonify({
            'success': True,
            'device_type': device_type,
            'connection_status': 'connected',
            'device_info': {
                'storage_capacity': '1TB',
                'available_space': '350GB',
                'connection_speed': '100MB/s'
            }
        })
        
    except Exception as e:
        logger.error(f"Connection error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file uploads"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        files = request.files.getlist('file')
        file_info = []
        
        for file in files:
            if file.filename == '':
                continue
            
            # Generate unique filename
            filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save file
            file.save(filepath)
            
            # Get file info
            file_size = os.path.getsize(filepath)
            file_info.append({
                'filename': filename,
                'original_name': file.filename,
                'size': file_size,
                'size_human': human_readable_size(file_size),
                'path': filepath,
                'uploaded_at': datetime.utcnow().isoformat()
            })
            
            logger.info(f"Uploaded: {filename} ({file_size} bytes)")
        
        return jsonify({
            'success': True,
            'files': file_info,
            'total_size': sum(f['size'] for f in file_info),
            'total_files': len(file_info)
        })
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/start-migration', methods=['POST'])
def start_migration():
    """Start a new migration job"""
    try:
        data = request.json
        migration_id = f"mig_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Starting migration {migration_id}: {data}")
        
        # Create migration job
        migration_job = {
            'id': migration_id,
            'status': 'initializing',
            'progress': 0,
            'source': data.get('source'),
            'destination': data.get('destination'),
            'files': data.get('files', []),
            'settings': data.get('settings', {}),
            'started_at': datetime.utcnow().isoformat(),
            'last_update': datetime.utcnow().isoformat()
        }
        
        # Start migration in background thread
        thread = threading.Thread(
            target=run_migration,
            args=(migration_job,)
        )
        thread.daemon = True
        thread.start()
        
        # Track active migration
        active_migrations[migration_id] = migration_job
        
        return jsonify({
            'success': True,
            'migration_id': migration_id,
            'message': 'Migration started successfully'
        })
        
    except Exception as e:
        logger.error(f"Migration start error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/migration-status/<migration_id>', methods=['GET'])
def get_migration_status(migration_id):
    """Get status of a migration job"""
    migration = active_migrations.get(migration_id)
    
    if not migration:
        # Check if it's in log
        try:
            with open(app.config['MIGRATION_LOG'], 'r') as f:
                migrations = json.load(f)
                migration = migrations.get(migration_id)
        except:
            migration = None
    
    if migration:
        return jsonify({
            'success': True,
            'migration': migration
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Migration not found'
        }), 404

@app.route('/api/get-migrations', methods=['GET'])
def get_migrations():
    """Get list of all migrations"""
    migrations_list = list(active_migrations.values())
    
    # Add completed migrations from log
    try:
        with open(app.config['MIGRATION_LOG'], 'r') as f:
            completed_migrations = json.load(f)
            migrations_list.extend(completed_migrations.values())
    except:
        pass
    
    return jsonify({
        'success': True,
        'migrations': migrations_list[:50]  # Return last 50 migrations
    })

@app.route('/api/analyze-files', methods=['POST'])
def analyze_files():
    """Analyze files for migration optimization"""
    try:
        data = request.json
        files = data.get('files', [])
        
        analysis = migration_engine.analyze_files(files)
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'recommendations': migration_engine.get_optimization_recommendations(analysis)
        })
        
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

def run_migration(migration_job):
    """Run migration in background thread"""
    try:
        migration_id = migration_job['id']
        logger.info(f"Running migration {migration_id}")
        
        # Update status
        migration_job['status'] = 'in_progress'
        migration_job['progress'] = 10
        
        # Simulate migration process (replace with actual migration logic)
        for i in range(10, 101, 10):
            time.sleep(2)  # Simulate work
            
            migration_job['progress'] = i
            migration_job['last_update'] = datetime.utcnow().isoformat()
            
            # Update speed estimation
            migration_job['current_speed'] = f"{50 + i} MB/s"
            
            # Calculate estimated time remaining
            if i < 100:
                remaining_time = (100 - i) * 2  # 2 seconds per 10%
                migration_job['eta_seconds'] = remaining_time
            
            # Save progress
            active_migrations[migration_id] = migration_job
        
        # Mark as completed
        migration_job['status'] = 'completed'
        migration_job['completed_at'] = datetime.utcnow().isoformat()
        migration_job['progress'] = 100
        
        # Log migration
        log_migration(migration_job)
        
        # Remove from active migrations after 1 hour
        time.sleep(3600)
        if migration_id in active_migrations:
            del active_migrations[migration_id]
            
        logger.info(f"Migration {migration_id} completed successfully")
        
    except Exception as e:
        migration_job['status'] = 'failed'
        migration_job['error'] = str(e)
        migration_job['failed_at'] = datetime.utcnow().isoformat()
        log_migration(migration_job)
        logger.error(f"Migration {migration_job['id']} failed: {str(e)}")

def log_migration(migration_job):
    """Log migration to JSON file"""
    try:
        migrations = {}
        
        # Load existing migrations
        if os.path.exists(app.config['MIGRATION_LOG']):
            with open(app.config['MIGRATION_LOG'], 'r') as f:
                migrations = json.load(f)
        
        # Add/update migration
        migrations[migration_job['id']] = migration_job
        
        # Save back
        with open(app.config['MIGRATION_LOG'], 'w') as f:
            json.dump(migrations, f, indent=2, default=str)
            
    except Exception as e:
        logger.error(f"Failed to log migration: {str(e)}")

def human_readable_size(size_bytes):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
