#!/bin/bash

# Start Redis in the background
redis-server &

# Start the Uvicorn server to run the Flask app
python3 -m uvicorn app:app --host 0.0.0.0 --port 5000 --workers 2 --log-level debug