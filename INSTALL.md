# Installation Guide

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Troubleshooting scikit-learn Installation

If you encounter compilation errors when installing scikit-learn:

**Option 1: Install pre-built wheel (Recommended)**
```bash
pip install --upgrade pip setuptools wheel
pip install scikit-learn --only-binary :all:
pip install -r requirements.txt
```

**Option 2: Use specific version with pre-built wheels**
```bash
pip install scikit-learn==1.3.2 --only-binary :all:
pip install -r requirements.txt
```

**Option 3: Install Visual C++ Build Tools (if building from source)**
- Download from [Microsoft Visual C++ Build Tools](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022)
- Install "C++ build tools" workload
- Then retry: `pip install -r requirements.txt`

### 3. Verify Installation

```bash
python -c "import sklearn; import joblib; print('✓ All dependencies installed')"
```

### 4. Run the Application

```bash
python run.py
```

Or:

```bash
cd webapp/backend
python app.py
```

The application will start on `http://localhost:5000`

## Model File

Make sure `webapp/backend/priority_model.pkl` exists. If not, the app will still work but will use "Medium" as default priority.

