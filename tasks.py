import logging
from celery_worker import celery
from utils.sendgrid_helper import send_login_email

# Setup logging untuk debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@celery.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def send_email_task(self, to_email: str, name: str, username: str, password: str, login_link: str = None):
    """
    Task untuk mengirim email informasi login di background.
    Dengan retry mechanism dan proper error handling.
    """
    try:
        # Jika login_link tidak disediakan, buat default URL
        if not login_link:
            # Gunakan hardcoded URL untuk menghindari Flask context issue
            login_link = "https://www.hubsensi.com/auth/login"  # Ganti dengan domain Anda
        
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
        # Jika sudah mencapai max retries, jangan retry lagi
        if self.request.retries >= self.max_retries:
            logger.error(f"Max retries reached untuk email {to_email}")
            return f"Gagal mengirim email setelah {self.max_retries} percobaan: {str(e)}"
        
        # Retry dengan delay
        logger.warning(f"Retry {self.request.retries + 1} untuk email {to_email}")
        raise self.retry(countdown=60 * (self.request.retries + 1))