import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List
from database import db
import logging

logger = logging.getLogger(__name__)


async def get_email_settings():
    """E-posta ayarlarını veritabanından getir"""
    settings = await db.email_settings.find_one({"id": "email_settings"}, {"_id": 0})
    
    if not settings:
        # Varsayılan ayarlar
        return {
            "smtp_host": "smtp.visupanel.com",
            "smtp_port": 587,
            "smtp_user": "info@visupanel.com",
            "smtp_password": "",
            "sender_name": "IZE Case Resolver",
            "sender_email": "info@visupanel.com",
            "email_enabled": True
        }
    
    return settings


def generate_email_body(case_data: dict, language: str = "tr") -> str:
    """Analiz sonucu için e-posta gövdesi oluştur"""
    
    if language == "tr":
        # Türkçe şablon
        warranty_status = "Garanti Kapsamında" if case_data.get("warranty_decision") == "COVERED" else "Garanti Dışı"
        within_warranty = "Evet" if case_data.get("is_within_2_year_warranty") else "Hayır"
        
        body = f"""Sayın Yetkili,

{case_data.get('ize_no', 'N/A')} numaralı IZE dosyanız analiz edilmiştir.

ARAÇ BİLGİLERİ
--------------
Firma: {case_data.get('company', 'N/A')}
Plaka: {case_data.get('plate', 'N/A')}
Şasi No: {case_data.get('vin', 'N/A')}
Kilometre: {case_data.get('repair_km', 'N/A')} km
Garanti Başlangıç: {case_data.get('warranty_start_date', 'N/A')}
Onarım Tarihi: {case_data.get('repair_date', 'N/A')}

GARANTİ DEĞERLENDİRMESİ
-----------------------
2 Yıl Garanti Süresi İçinde: {within_warranty}
Garanti Kararı: {warranty_status}

ARIZA BİLGİLERİ
---------------
Müşteri Şikayeti: {case_data.get('failure_complaint', 'N/A')}
Arıza Nedeni: {case_data.get('failure_cause', 'N/A')}

KARAR GEREKÇELERİ
-----------------
"""
        rationales = case_data.get('decision_rationale', [])
        if rationales:
            for i, rationale in enumerate(rationales, 1):
                body += f"{i}. {rationale}\n"
        else:
            body += "Belirtilmemiş\n"

        body += f"""
YAPILAN İŞLEMLER
----------------
"""
        operations = case_data.get('operations_performed', [])
        if operations:
            for op in operations:
                body += f"• {op}\n"
        else:
            body += "Belirtilmemiş\n"

        body += f"""
DEĞİŞEN PARÇALAR
----------------
"""
        parts = case_data.get('parts_replaced', [])
        if parts:
            for part in parts:
                if isinstance(part, dict):
                    body += f"• {part.get('partName', 'N/A')} - {part.get('description', '')}\n"
                else:
                    body += f"• {part}\n"
        else:
            body += "Belirtilmemiş\n"

        body += f"""
ONARIM ÖZETİ
------------
{case_data.get('repair_process_summary', 'Belirtilmemiş')}

---
Bu e-posta IZE Case Resolver sistemi tarafından otomatik olarak gönderilmiştir.
Detaylı bilgi için lütfen sistem yöneticinizle iletişime geçin.
"""
    else:
        # English template
        warranty_status = "Covered" if case_data.get("warranty_decision") == "COVERED" else "Out of Coverage"
        within_warranty = "Yes" if case_data.get("is_within_2_year_warranty") else "No"
        
        body = f"""Dear Sir/Madam,

Your IZE file {case_data.get('ize_no', 'N/A')} has been analyzed.

VEHICLE INFORMATION
-------------------
Company: {case_data.get('company', 'N/A')}
Plate: {case_data.get('plate', 'N/A')}
VIN: {case_data.get('vin', 'N/A')}
Mileage: {case_data.get('repair_km', 'N/A')} km
Warranty Start: {case_data.get('warranty_start_date', 'N/A')}
Repair Date: {case_data.get('repair_date', 'N/A')}

WARRANTY EVALUATION
-------------------
Within 2 Year Warranty: {within_warranty}
Warranty Decision: {warranty_status}

FAILURE INFORMATION
-------------------
Customer Complaint: {case_data.get('failure_complaint', 'N/A')}
Failure Cause: {case_data.get('failure_cause', 'N/A')}

DECISION RATIONALE
------------------
"""
        rationales = case_data.get('decision_rationale', [])
        if rationales:
            for i, rationale in enumerate(rationales, 1):
                body += f"{i}. {rationale}\n"
        else:
            body += "Not specified\n"

        body += """
OPERATIONS PERFORMED
--------------------
"""
        operations = case_data.get('operations_performed', [])
        if operations:
            for op in operations:
                body += f"• {op}\n"
        else:
            body += "Not specified\n"

        body += """
PARTS REPLACED
--------------
"""
        parts = case_data.get('parts_replaced', [])
        if parts:
            for part in parts:
                if isinstance(part, dict):
                    body += f"• {part.get('partName', 'N/A')} - {part.get('description', '')}\n"
                else:
                    body += f"• {part}\n"
        else:
            body += "Not specified\n"

        body += f"""
REPAIR SUMMARY
--------------
{case_data.get('repair_process_summary', 'Not specified')}

---
This email was automatically sent by the IZE Case Resolver system.
For detailed information, please contact your system administrator.
"""
    
    return body


def generate_email_subject(case_data: dict, language: str = "tr") -> str:
    """E-posta konusu oluştur"""
    ize_no = case_data.get('ize_no', 'N/A')
    plate = case_data.get('plate', 'N/A')
    vin = case_data.get('vin', 'N/A')
    
    if language == "tr":
        return f"{ize_no} - {plate} - {vin} Yurtdışı IZE Dosyası Hk."
    else:
        return f"{ize_no} - {plate} - {vin} International IZE File"


async def send_analysis_email(
    to_email: str,
    case_data: dict,
    attachment_path: Optional[str] = None,
    attachment_bytes: Optional[bytes] = None,
    attachment_filename: Optional[str] = None,
    language: str = "tr"
) -> dict:
    """Analiz sonucunu e-posta ile gönder"""
    
    settings = await get_email_settings()
    
    if not settings.get("email_enabled", True):
        return {"success": False, "message": "E-posta gönderimi devre dışı"}
    
    if not settings.get("smtp_password"):
        return {"success": False, "message": "SMTP şifresi ayarlanmamış"}
    
    try:
        # E-posta oluştur
        msg = MIMEMultipart()
        msg['From'] = f"{settings.get('sender_name', 'IZE Case Resolver')} <{settings.get('sender_email', 'info@visupanel.com')}>"
        msg['To'] = to_email
        msg['Subject'] = generate_email_subject(case_data, language)
        
        # Gövde ekle
        body = generate_email_body(case_data, language)
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Ek dosya varsa ekle (IZE PDF)
        if attachment_bytes and attachment_filename:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment_bytes)
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename="{attachment_filename}"'
            )
            msg.attach(part)
        elif attachment_path:
            with open(attachment_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                filename = attachment_path.split('/')[-1]
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename="{filename}"'
                )
                msg.attach(part)
        
        # SMTP bağlantısı ve gönderim
        smtp_host = settings.get('smtp_host', 'smtp.visupanel.com')
        smtp_port = settings.get('smtp_port', 587)
        smtp_user = settings.get('smtp_user', 'info@visupanel.com')
        smtp_password = settings.get('smtp_password', '')
        
        # TLS ile bağlan
        context = ssl.create_default_context()
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(smtp_user, smtp_password)
            server.sendmail(
                settings.get('sender_email', smtp_user),
                to_email,
                msg.as_string()
            )
        
        logger.info(f"E-posta gönderildi: {to_email} - {case_data.get('ize_no', 'N/A')}")
        return {"success": True, "message": "E-posta başarıyla gönderildi"}
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP kimlik doğrulama hatası: {str(e)}")
        return {"success": False, "message": "SMTP kimlik doğrulama hatası. Kullanıcı adı veya şifre yanlış."}
    except smtplib.SMTPException as e:
        logger.error(f"SMTP hatası: {str(e)}")
        return {"success": False, "message": f"SMTP hatası: {str(e)}"}
    except Exception as e:
        logger.error(f"E-posta gönderim hatası: {str(e)}")
        return {"success": False, "message": f"E-posta gönderilemedi: {str(e)}"}


async def test_smtp_connection() -> dict:
    """SMTP bağlantısını test et"""
    settings = await get_email_settings()
    
    if not settings.get("smtp_password"):
        return {"success": False, "message": "SMTP şifresi ayarlanmamış"}
    
    try:
        smtp_host = settings.get('smtp_host', 'smtp.visupanel.com')
        smtp_port = settings.get('smtp_port', 587)
        smtp_user = settings.get('smtp_user', 'info@visupanel.com')
        smtp_password = settings.get('smtp_password', '')
        
        # SSL context - sertifika doğrulamasını gevşet
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(smtp_user, smtp_password)
        
        return {"success": True, "message": "SMTP bağlantısı başarılı"}
        
    except smtplib.SMTPAuthenticationError:
        return {"success": False, "message": "SMTP kimlik doğrulama hatası. Kullanıcı adı veya şifre yanlış."}
    except smtplib.SMTPException as e:
        return {"success": False, "message": f"SMTP hatası: {str(e)}"}
    except Exception as e:
        return {"success": False, "message": f"Bağlantı hatası: {str(e)}"}
