@echo off
REM Installation script for AI Commitment Tracker

echo ========================================
echo AI Commitment Tracker - Installation
echo ========================================
echo.

echo Step 1: Upgrading pip, setuptools, and wheel...
pip install --upgrade pip setuptools wheel
echo.

echo Step 2: Installing scikit-learn with pre-built wheels...
pip install scikit-learn --only-binary :all:
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Warning: scikit-learn installation failed with --only-binary flag.
    echo Trying alternative method...
    pip install scikit-learn==1.3.2 --only-binary :all:
)
echo.

echo Step 3: Installing other dependencies...
pip install Flask==3.0.0
pip install flask-cors==4.0.0
pip install joblib>=1.3.0
echo.

echo Step 4: Verifying installation...
python -c "import sklearn; import joblib; import flask; print('✓ All dependencies installed successfully!')"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Error: Some dependencies failed to install.
    echo Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo You can now run the application with:
echo   python run.py
echo.
pause

