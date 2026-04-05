#!/usr/bin/env python3
"""
Celery worker entry point for Feed Service

Run with:
    celery -A celery_worker worker --loglevel=info --concurrency=4

Or with specific queues:
    celery -A celery_worker worker --loglevel=info --queues=feed_fetches,feed_bulk
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.celery_app import celery_app

if __name__ == "__main__":
    celery_app.start()