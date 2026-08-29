"""
Run script for Commitment Tracker.
"""

import sys
from pathlib import Path

# Add webapp to path
sys.path.append(str(Path(__file__).parent))

from webapp.backend.app import app

if __name__ == '__main__':
    print("=" * 50)
    print("Commitment Tracker")
    print("=" * 50)
    print("Starting server on http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)


