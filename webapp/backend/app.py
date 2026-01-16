"""
Flask backend API for Commitment Tracker.
"""

from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from flask_cors import CORS
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from webapp.database.database import Database
from webapp.backend.priority_predictor import load_model, predict_priority
from webapp.backend.helpers import calculate_urgency

app = Flask(__name__, 
            template_folder=Path(__file__).parent.parent / 'frontend' / 'templates',
            static_folder=Path(__file__).parent.parent / 'frontend' / 'static')
app.secret_key = 'commitment-tracker-secret-key-change-in-production'
CORS(app)

db = Database()

# Load ML model at startup
print("Loading ML model...")
load_model()
print("Application ready!")

@app.route('/')
def index():
    """Redirect to login if not authenticated, else dashboard."""
    if 'user_id' not in session:
        return redirect('/login')
    return redirect('/dashboard')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page - GET shows form, POST processes login."""
    if request.method == 'GET':
        return render_template('login.html')
    
    # POST request - process login
    username = request.form.get('username', '').strip()
    
    if not username:
        return render_template('login.html', error='Username is required')
    
    # Get or create user
    user = db.get_user_by_username(username)
    if not user:
        user_id = db.create_user(username)
        if user_id is None:
            return render_template('login.html', error='Failed to create user')
        user = db.get_user_by_username(username)
    
    # Set session
    session['user_id'] = user['id']
    session['username'] = user['username']
    
    # Check for urgent commitments and show modal
    urgent = db.get_urgent_commitments(user['id'], limit=5)
    
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    """Dashboard page - shows commitments."""
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    username = session['username']
    
    # Get filter status and sort preference
    status_filter = request.args.get('status', '')
    sort_priority = request.args.get('sort', '')  # 'high_to_low' or 'low_to_high'
    
    if status_filter:
        commitments = db.get_user_commitments(user_id, status_filter, sort_priority)
    else:
        commitments = db.get_user_commitments(user_id, None, sort_priority)
    
    # Format deadlines, calculate urgency, and ensure priority exists
    for commit in commitments:
        deadline_dt = None
        if commit.get('deadline'):
            try:
                deadline_dt = datetime.fromisoformat(commit['deadline'])
                commit['deadline_formatted'] = deadline_dt.strftime('%Y-%m-%d %H:%M')
                commit['deadline_date'] = deadline_dt.date()
                commit['is_overdue'] = deadline_dt < datetime.now() and commit['status'] == 'Pending'
            except:
                commit['deadline_formatted'] = commit['deadline']
                commit['is_overdue'] = False
        else:
            commit['deadline_formatted'] = 'No deadline'
            commit['is_overdue'] = False
        
        # Calculate urgency indicator
        urgency = calculate_urgency(deadline_dt, commit.get('status', 'Pending'))
        commit['urgency'] = urgency
        
        # Ensure priority field exists (for old records)
        if 'priority' not in commit or not commit['priority']:
            commit['priority'] = 'Medium'
    
    # Get urgent commitments for modal
    urgent = db.get_urgent_commitments(user_id, limit=5)
    for commit in urgent:
        if commit.get('deadline'):
            try:
                dt = datetime.fromisoformat(commit['deadline'])
                commit['deadline_formatted'] = dt.strftime('%Y-%m-%d %H:%M')
            except:
                commit['deadline_formatted'] = commit['deadline']
    
    show_urgent_modal = len(urgent) > 0 and 'urgent_shown' not in session
    
    return render_template('dashboard.html', 
                         username=username,
                         commitments=commitments,
                         urgent_commitments=urgent,
                         show_urgent_modal=show_urgent_modal,
                         current_filter=status_filter,
                         current_sort=sort_priority)

@app.route('/add_commitment', methods=['POST'])
def add_commitment():
    """Add a new commitment with ML priority prediction."""
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    subject = request.form.get('subject', '').strip()
    description = request.form.get('description', '').strip()
    deadline_str = request.form.get('deadline', '').strip() or None
    status = request.form.get('status', 'Pending')
    
    if not subject:
        return redirect('/dashboard?error=Subject is required')
    
    # Convert deadline format if provided
    deadline_dt = None
    if deadline_str:
        try:
            # Convert from HTML datetime-local format to datetime
            deadline_dt = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
            deadline_iso = deadline_dt.isoformat()
        except:
            deadline_iso = None
    else:
        deadline_iso = None
    
    # Automatically predict priority using ML model
    commitment_text = f"{subject} {description}".strip()
    priority = predict_priority(commitment_text, deadline_dt)
    
    db.create_commitment(user_id, subject, description, deadline_iso, status, priority)
    
    return redirect('/dashboard?success=Commitment added successfully')

@app.route('/api/commitments/<int:commitment_id>/status', methods=['PUT'])
def update_status(commitment_id):
    """Update commitment status only."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    status = data.get('status')
    
    if status not in ['Pending', 'Completed', 'Overdue']:
        return jsonify({'error': 'Invalid status'}), 400
    
    success = db.update_commitment_status(commitment_id, session['user_id'], status)
    
    if not success:
        return jsonify({'error': 'Commitment not found'}), 404
    
    return jsonify({'success': True, 'message': 'Status updated'})

@app.route('/api/commitments/<int:commitment_id>', methods=['DELETE'])
def delete_commitment(commitment_id):
    """Delete a commitment."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    success = db.delete_commitment(commitment_id, session['user_id'])
    
    if not success:
        return jsonify({'error': 'Commitment not found'}), 404
    
    return jsonify({'success': True, 'message': 'Commitment deleted'})

@app.route('/logout', methods=['POST'])
def logout():
    """Logout user."""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out'})

@app.route('/api/mark_urgent_shown', methods=['POST'])
def mark_urgent_shown():
    """Mark urgent modal as shown."""
    if 'user_id' in session:
        session['urgent_shown'] = True
    return jsonify({'success': True})

@app.route('/api/predict_priority', methods=['POST'])
def predict_priority_api():
    """API endpoint to predict priority (for real-time prediction)."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    subject = data.get('subject', '').strip()
    description = data.get('description', '').strip()
    deadline_str = data.get('deadline', '').strip() or None
    
    commitment_text = f"{subject} {description}".strip()
    
    deadline_dt = None
    if deadline_str:
        try:
            deadline_dt = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
        except:
            pass
    
    priority = predict_priority(commitment_text, deadline_dt)
    
    return jsonify({'priority': priority})

@app.route('/api/commitments/<int:commitment_id>', methods=['PUT'])
def update_commitment(commitment_id):
    """Update a commitment."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    
    success = db.update_commitment(
        commitment_id,
        session['user_id'],
        subject=data.get('subject'),
        description=data.get('description'),
        deadline=data.get('deadline'),
        status=data.get('status'),
        priority=data.get('priority')
    )
    
    if not success:
        return jsonify({'error': 'Commitment not found or update failed'}), 404
    
    return jsonify({'success': True, 'message': 'Commitment updated'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
