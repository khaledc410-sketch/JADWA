#!/bin/bash
export PYTHONPATH="/Users/khalharbi/Desktop/JADWA/backend/venv/lib/python3.9/site-packages:/Users/khalharbi/Desktop/JADWA/backend"
cd /Users/khalharbi/Desktop/JADWA/backend
exec /opt/anaconda3/bin/python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
