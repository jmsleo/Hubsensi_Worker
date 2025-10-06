# tasks.py
import logging
from celery_worker import celery
from utils.sendgrid_helper import send_login_email
from flask import url_for

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@celery.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def send_email_task(self, to_email: str, name: str, username: str, password: str):
    """
    Task untuk mengirim email informasi login di background.
    """
    try:
        # url_for akan berfungsi karena task berjalan dalam konteks aplikasi
        login_link = url_for('auth.login', _external=True)

        logger.info(f"Mengirim email ke {to_email} untuk user {name}")

        result = send_login_email(
            to_email=to_email,
            name=name,
            username=username,
            password=password,
            login_link=login_link
        )

        logger.info(f"Email berhasil dikirim ke {to_email}")
        return f"Email berhasil dikirim ke {to_email}"

    except Exception as e:
        logger.error(f"Gagal mengirim email ke {to_email}: {str(e)}")
        raise self.retry(exc=e)