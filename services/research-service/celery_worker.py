#!/usr/bin/env python3
"""
Celery worker entry point for Research Service.

Run with:
    celery -A celery_worker worker --loglevel=info --concurrency=4

Or with specific queues:
    celery -A celery_worker worker --loglevel=info --queues=research,research_batch

Run Celery Beat for scheduled tasks:
    celery -A celery_worker beat --loglevel=info

Or run both worker and beat together:
    celery -A celery_worker worker --beat --loglevel=info --concurrency=4
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.workers.celery_app import celery_app

if __name__ == "__main__":
    celery_app.start()
