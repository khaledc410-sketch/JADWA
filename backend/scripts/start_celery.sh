#!/bin/bash
export PYTHONPATH="/Users/khalharbi/Desktop/JADWA/backend/venv/lib/python3.9/site-packages:/Users/khalharbi/Desktop/JADWA/backend"
cd /Users/khalharbi/Desktop/JADWA/backend
exec /opt/anaconda3/bin/python3 -m celery -A app.tasks.celery_app worker --loglevel=info --concurrency=4
