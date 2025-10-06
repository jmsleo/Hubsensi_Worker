# celery_worker.py
import os
from factory import create_app
from celery import Celery

# Buat instance aplikasi Flask
flask_app = create_app(os.getenv('FLASK_CONFIG') or 'default')
# Inisialisasi Celery
celery = Celery(flask_app.import_name, broker=flask_app.config['CELERY_BROKER_URL'])
celery.conf.update(flask_app.config)
class ContextTask(celery.Task):
    def __call__(self, *args, **kwargs):
        with flask_app.app_context():
            return self.run(*args, **kwargs)

celery.Task = ContextTask