# AI Commitment Tracker

A web application for tracking personal commitments with ML-powered priority prediction, deadline management, and status tracking.

## Features

- **User Authentication**: Simple username-based login (no password required)
- **Manual Commitment Entry**: Add commitments with subject, description, and deadline
- **ML Priority Prediction**: Automatically predicts priority (High/Medium/Low) using trained scikit-learn model
- **Rule-Based Override**: Urgent keywords (exam, interview, test) with short deadlines automatically set to High priority
- **Status Management**: Track commitments as Pending, Completed, or Overdue
- **Priority Display**: Visual priority badges (High/Medium/Low) for each commitment
- **Manual Priority Override**: Users can manually set priority if needed
- **Urgent Alerts**: Automatically shows most urgent commitments (nearest deadlines) on login
- **Filtering**: Filter commitments by status (All, Pending, Completed, Overdue)
- **Priority Sorting**: Commitments sorted by deadline urgency (nearest first)

## Project Structure

```
webapp/
├── frontend/
│   ├── templates/
│   │   ├── login.html          # Login page
│   │   └── dashboard.html      # Main dashboard
│   └── static/
│       ├── css/
│       │   └── style.css       # All styling
│       └── js/
│           └── dashboard.js    # Minimal JavaScript for interactions
├── backend/
│   └── app.py                  # Flask application
└── database/
    └── database.py             # Database operations
```

## Setup Instructions

### 1. Install Dependencies

**Important:** scikit-learn requires special installation on Windows to avoid compilation errors.

```bash
# First, upgrade pip and install build tools
pip install --upgrade pip setuptools wheel

# Install scikit-learn with pre-built wheels (avoids compilation)
pip install scikit-learn --only-binary :all:

# Install other dependencies
pip install -r requirements.txt
```

**Alternative:** If the above doesn't work, try:
```bash
pip install scikit-learn==1.3.2 --only-binary :all:
pip install -r requirements.txt
```

### 2. Run the Application

```bash
cd webapp/backend
python app.py
```

The application will start on `http://localhost:5000`

### 3. Usage

1. **Login**: Enter any username (new users are automatically created)
2. **Add Commitment**: Fill in the form to add a new commitment
3. **Manage Status**: Use buttons to change commitment status
4. **Filter**: Click filter buttons to view commitments by status
5. **Sign Out**: Click "Sign Out" button to logout

## Database

- SQLite database stored in `webapp/database/commitments.db`
- Two tables: `users` and `commitments`
- Automatic schema creation on first run

## ML Model Integration

The application uses a pre-trained scikit-learn model (`priority_model.pkl`) to automatically predict commitment priority.

### Model Details
- **File Location**: `webapp/backend/priority_model.pkl`
- **Model Type**: scikit-learn Pipeline (TF-IDF + Logistic Regression)
- **Input Format**: `"commitment_text deadline_<hours_left>"`
- **Output**: `"High"`, `"Medium"`, or `"Low"`

### Priority Prediction Flow
1. User enters commitment text and deadline
2. System calculates hours remaining until deadline
3. Rule-based override checks for urgent keywords (exam, interview, test) with ≤12 hours → forces "High"
4. If no override, ML model predicts priority based on text and deadline
5. Priority is displayed automatically in the UI
6. User can manually override priority if needed

### Edge Cases
- **No deadline**: Uses default 168 hours (7 days) for prediction
- **Urgent keywords**: If text contains "exam", "examination", "interview", or "test" AND deadline ≤12 hours → automatically "High"
- **Model not loaded**: Falls back to "Medium" priority

## Technologies

- **Backend**: Python Flask
- **Frontend**: HTML, CSS, minimal JavaScript
- **Database**: SQLite
- **ML Framework**: scikit-learn, joblib
- **Session Management**: Flask sessions

## Security Notes

- This is a simple application for personal use
- No password authentication (username only)
- Session-based authentication
- Change `secret_key` in production

## License

This project is for educational and personal use.

