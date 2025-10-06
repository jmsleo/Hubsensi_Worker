# celery_init.py
import logging
import os
from celery_worker import celery

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simplified initialization tanpa Flask context untuk menghindari crash loop
try:
    logger.info("Celery worker initialized without Flask context to prevent crashes")
    logger.info("Flask context akan dibuat per-task jika diperlukan")
    
except Exception as e:
    logger.error(f"Failed to initialize Celery: {e}")
    raise