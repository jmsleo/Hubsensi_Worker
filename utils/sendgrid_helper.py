import os
import logging
from postmarker.core import PostmarkClient

# Setup logging
logger = logging.getLogger(__name__)

# Postmark configuration dengan validation yang lebih toleran
POSTMARK_API_KEY = os.environ.get('POSTMARK_API_KEY')
FROM_EMAIL = os.environ.get('POSTMARK_FROM_EMAIL')
TEMPLATE_ID = os.environ.get('POSTMARK_TEMPLATE_ID', '0')
LOGO_URL = os.environ.get('LOGO_URL')

def validate_and_init_postmark():
    """Validasi dan inisialisasi Postmark dengan error handling yang baik"""
    try:
        # Check required variables
        if not POSTMARK_API_KEY:
            raise ValueError("POSTMARK_API_KEY tidak ditemukan")
        if not FROM_EMAIL:
            raise ValueError("POSTMARK_FROM_EMAIL tidak ditemukan")
        if not TEMPLATE_ID or TEMPLATE_ID == '0':
            raise ValueError("POSTMARK_TEMPLATE_ID tidak valid")
        if not LOGO_URL:
            raise ValueError("LOGO_URL tidak ditemukan")
        
        # Convert template ID
        template_id_int = int(TEMPLATE_ID)
        if template_id_int <= 0:
            raise ValueError("POSTMARK_TEMPLATE_ID harus berupa angka positif")
        
        # Initialize client
        client = PostmarkClient(server_token=POSTMARK_API_KEY)
        logger.info("Postmark client berhasil diinisialisasi")
        
        return client, template_id_int
        
    except Exception as e:
        logger.error(f"Gagal inisialisasi Postmark: {e}")
        return None, None

# Initialize pada import
postmark_client, TEMPLATE_ID_INT = validate_and_init_postmark()

def send_login_email(to_email: str, name: str, username: str, password: str, login_link: str) -> dict:
    """
    Mengirim email login info menggunakan template Postmark dengan error handling yang robust
    """
    # Validasi client
    if not postmark_client or not TEMPLATE_ID_INT:
        raise RuntimeError("Postmark client tidak tersedia. Periksa konfigurasi environment variables.")
    
    # Validasi input parameters
    if not all([to_email, name, username, password, login_link]):
        raise ValueError("Semua parameter email harus diisi")
    
    try:
        template_model = {
            "name": name,
            "username": username,
            "password": password,
            "login_link": login_link,
            "logo_url": LOGO_URL
        }
        
        logger.info(f"Mengirim email ke {to_email} dengan template ID {TEMPLATE_ID_INT}")
        
        resp = postmark_client.emails.send_with_template(
            From=FROM_EMAIL,
            To=to_email,
            TemplateId=TEMPLATE_ID_INT,
            TemplateModel=template_model
        )
        
        # Check response
        error_code = resp.get('ErrorCode', 0)
        if error_code == 0:
            logger.info(f"Email berhasil dikirim ke {to_email}. MessageID: {resp.get('MessageID')}")
            return {
                "status_code": 200,
                "body": resp,
                "headers": {},
                "success": True
            }
        else:
            error_msg = f"Postmark error {error_code}: {resp.get('Message', 'Unknown error')}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    except Exception as e:
        error_msg = f"Gagal mengirim email login info ke {to_email}: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)