# HubSensi_(GitHub Production)/celery_worker.py
import os
import logging
from celery import Celery
from dotenv import load_dotenv

# Setup logging untuk Celery
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Muat environment variables terlebih dahulu
load_dotenv()

# Validate Celery configuration
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND')

if not CELERY_BROKER_URL:
    raise ValueError("CELERY_BROKER_URL environment variable is required")
if not CELERY_RESULT_BACKEND:
    raise ValueError("CELERY_RESULT_BACKEND environment variable is required")

logger.info(f"Initializing Celery with broker: {CELERY_BROKER_URL}")

# Buat instance Celery dengan konfigurasi yang stabil
celery = Celery(
    "HubSensi",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=['tasks']
)

# Konfigurasi Celery yang optimal dan stabil
celery.conf.update(
    task_track_started=True,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Jakarta',
    enable_utc=True,
    
    # Worker configuration untuk stabilitas
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=50,  # Restart worker setelah 50 tasks untuk mencegah memory leak
    
    # Retry configuration
    task_default_retry_delay=60,
    task_max_retries=3,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    
    # Connection settings untuk stabilitas
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    
    # Disable problematic features yang bisa menyebabkan crash
    worker_disable_rate_limits=True,
    task_ignore_result=False,
    
    # Pool settings untuk mencegah deadlock
    worker_pool_restarts=True,
)

logger.info("Celery worker configuration completed")