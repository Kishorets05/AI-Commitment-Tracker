# 📁 AI Commitment Tracker - Folder Structure

## Project Root
```
Email Commitment/
│
├── 📄 run.py                          # Main application entry point
├── 📄 requirements.txt                # Python dependencies
├── 📄 README.md                        # Project documentation
├── 📄 INSTALL.md                       # Installation guide
├── 📄 install_dependencies.bat         # Windows dependency installer
│
└── 📂 webapp/                         # Main application package
    │
    ├── 📂 backend/                    # Backend logic & API
    │   ├── 📄 app.py                  # Flask application & routes
    │   ├── 📄 priority_predictor.py   # ML model + Hybrid Intelligence
    │   ├── 📄 helpers.py              # Utility functions (urgency calculation)
    │   ├── 📄 priority_model.pkl     # Trained ML model (scikit-learn)
    │   ├── 📄 test_priority_rules.py  # Test script for priority rules
    │   ├── 📂 __pycache__/            # Python cache (auto-generated)
    │   └── 📂 api/                    # API endpoints (if needed)
    │
    ├── 📂 database/                   # Database layer
    │   ├── 📄 database.py             # SQLite database operations
    │   ├── 📄 __init__.py             # Package initialization
    │   ├── 📄 commitments.db          # SQLite database file
    │   └── 📂 __pycache__/            # Python cache (auto-generated)
    │
    ├── 📂 frontend/                    # Frontend assets
    │   ├── 📂 templates/              # HTML templates (Jinja2)
    │   │   ├── 📄 login.html          # Login page template
    │   │   └── 📄 dashboard.html     # Main dashboard template
    │   │
    │   └── 📂 static/                  # Static assets
    │       ├── 📂 css/                 # Stylesheets
    │       │   └── 📄 style.css       # Main stylesheet
    │       └── 📂 js/                 # JavaScript files
    │           └── 📄 dashboard.js    # Dashboard interactions
    │
    └── 📄 data.csv                     # Optional: CSV data (if used)
```

## 📋 Detailed File Descriptions

### Root Level Files

| File | Purpose |
|------|---------|
| `run.py` | Main entry point - starts Flask server |
| `requirements.txt` | Python package dependencies |
| `README.md` | Project overview, features, setup instructions |
| `INSTALL.md` | Detailed installation & troubleshooting guide |
| `install_dependencies.bat` | Windows batch script for dependency installation |

### Backend (`webapp/backend/`)

| File | Purpose |
|------|---------|
| `app.py` | Flask application with all routes (login, dashboard, API endpoints) |
| `priority_predictor.py` | **Hybrid Intelligence System**: ML model loading + rule-based priority adjustments |
| `helpers.py` | Utility functions for urgency calculation and formatting |
| `priority_model.pkl` | Pre-trained scikit-learn model (TF-IDF + Logistic Regression) |
| `test_priority_rules.py` | Test suite for verifying priority rule logic |

### Database (`webapp/database/`)

| File | Purpose |
|------|---------|
| `database.py` | SQLite database operations (CRUD for users & commitments) |
| `__init__.py` | Package initialization |
| `commitments.db` | SQLite database file (auto-created, contains users & commitments tables) |

### Frontend (`webapp/frontend/`)

#### Templates (`templates/`)
| File | Purpose |
|------|---------|
| `login.html` | Login page with username input |
| `dashboard.html` | Main dashboard with commitment list, filters, add form |

#### Static Assets (`static/`)
| File | Purpose |
|------|---------|
| `css/style.css` | All styling (responsive design, animations, badges) |
| `js/dashboard.js` | Client-side interactions (status updates, delete, logout) |

## 🔄 Data Flow

```
User Input (HTML Form)
    ↓
Flask Route (app.py)
    ↓
Database Layer (database.py)
    ↓
Priority Prediction (priority_predictor.py)
    ├── ML Model (priority_model.pkl)
    └── Rule-Based Adjustments
    ↓
SQLite Storage (commitments.db)
    ↓
Template Rendering (dashboard.html)
    ↓
User Interface (HTML + CSS + JS)
```

## 🎯 Key Components

### 1. **Hybrid Intelligence System**
- **Location**: `webapp/backend/priority_predictor.py`
- **Function**: Combines ML predictions with rule-based adjustments
- **Rules**: Financial tasks, Professional tasks, Urgency override

### 2. **Database Schema**
- **Users Table**: id, username, created_at
- **Commitments Table**: id, user_id, subject, description, deadline, status, priority, created_at, updated_at

### 3. **Frontend Features**
- Login system with session management
- Dynamic priority badges (High/Medium/Low)
- Urgency indicators (hours/days left)
- Status filters (All/Pending/Completed/Overdue)
- Priority sorting (High to Low / Low to High)
- Urgent commitments modal popup

## 📦 Dependencies

See `requirements.txt` for complete list:
- Flask (web framework)
- Flask-CORS (CORS support)
- joblib (ML model loading)
- scikit-learn (ML model dependencies)

## 🚀 Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python run.py
```

The application will be available at: `http://localhost:5000`

## 📝 Notes

- `__pycache__/` folders are auto-generated by Python (can be ignored)
- `commitments.db` is created automatically on first run
- `priority_model.pkl` must be present for ML predictions to work
- All HTML templates use Jinja2 syntax for dynamic content
- CSS uses modern features (gradients, animations, glassmorphism)

