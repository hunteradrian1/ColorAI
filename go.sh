#!/usr/bin/env bash
set -euo pipefail
# -e: exit immediately if a command fails
# -u: treat unset variables as errors
# -o pipefail: return the exit code of the first failed command in a pipeline

echo "Starting Flask local server + React client (no Node API)."

# Check if Flask/API port (4000) is already in use
if lsof -i:4000 -sTCP:LISTEN -t >/dev/null ; then
  echo "Port 4000 is already in use (Flask/API). Please free it first."
  exit 1
fi

# Check if React client port (3000) is already in use
if lsof -i:3000 -sTCP:LISTEN -t >/dev/null ; then
  echo "Port 3000 is already in use (React). Please free it first."
  exit 1
fi

# Verify that Python virtual environment exists
if [ ! -f ml/venv/bin/activate ]; then
  echo "Python virtual env not found. Run: cd ml && ./setup.sh"
  exit 1
fi

# Verify that at least one model file (.h5) exists in ml/models/
if ! ls ml/models/*.h5 1> /dev/null 2>&1; then
  echo "Model not found. Place model.h5 in ml/models/."
  exit 1
fi

# Ensure the React client has an .env file pointing to the Flask API
if [ ! -f client/.env.local ] && [ ! -f client/.env ]; then
  echo "REACT_APP_API_URL=http://localhost:4000/api" > client/.env.local
  echo "Created client/.env.local pointing to Flask API."
fi

# Start React client in the background (installs dependencies if needed)
(cd client && npm install && npm start) &

# Activate Python virtual environment
source ml/venv/bin/activate

# Start the Flask local server
python3 server/local_server.py