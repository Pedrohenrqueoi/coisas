# -*- coding: utf-8 -*-
"""
Celery Worker Entry Point
Run with: celery -A celery_worker.celery worker --loglevel=info
"""
import os
from app import create_app, celery

# Create Flask app context
flask_app = create_app(os.getenv('FLASK_ENV', 'development'))
flask_app.app_context().push()

# Import tasks to register them
from app.tasks.video_tasks import *