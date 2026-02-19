import smtplib
import ssl
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List
from database import db
import logging

logger = logging.getLogger(__name__)


def _extract_turkish_text(text: str) -> str:
    """"Original: ... | TR: ..." formatından yalnızca TR kısmını döndürür."""
    if not text:
        return ""

    normalized = str(text).strip()
    tr_marker = "| TR:"
    if tr_marker in normalized:
        return normalized.split(tr_marker, 1)[1].strip()

    if normalized.startswith("TR:"):
        return normalized[3:].strip()

    return normalized


def _normalize_operations_for_tr(operations: List[str]) -> str:
    """Operasyon listesini Türkçe, akıcı cümlede kullanılacak biçime getirir."""
    cleaned_ops = [_extract_turkish_text(op) for op in operations if str(op).strip()]
    cleaned_ops = [op for op in cleaned_ops if op]

    if not cleaned_ops:
        return "kontrol ve diagnostik işlemleri"

    if len(cleaned_ops) == 1:
        return cleaned_ops[0]

    return ", ".join(cleaned_ops[:-1]) + " ve " + cleaned_ops[-1]


def _normalize_company_name(company: str) -> str:
    """Firma adını e-posta başlığı için sadeleştirir (ilk kelime)."""
    if not company:
        return "N/A"
    return company.strip().split()[0]


def _format_date_for_email(date_text: Optional[str]) -> str:
    """YYYY-MM-DD tarihlerini DD.MM.YYYY formatına çevirir."""
    if not date_text:
        return "belirtilen"
    try:
        return datetime.strptime(date_text, "%Y-%m-%d").strftime("%d.%m.%Y")
    except ValueError:
        return date_text


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
        ize_no = case_data.get('ize_no', 'N/A')
        repair_date = _format_date_for_email(case_data.get('repair_date'))
        warranty_start_date = _format_date_for_email(case_data.get('warranty_start_date'))
        warranty_out_text = "dışında" if not case_data.get("is_within_2_year_warranty") else "içinde"

        operations = case_data.get('operations_performed', [])
        operations_text = (", ".join([str(op).strip() for op in operations if str(op).strip()])
        if operations else "kontrol ve diagnostik işlemleri")

        parts = case_data.get('parts_replaced', [])
        if parts:
            parts_summary = "Onarım sürecinde parça değişimi gerçekleştirilmiş olup işlemler ilgili parçalar üzerinden tamamlanmıştır."
        else:
            parts_summary = "Onarım sürecinde herhangi bir parça değişimi yapılmamış, işlemler kontrol, diagnostik ve yazılım güncelleme kapsamında gerçekleştirilmiştir."

        repair_summary = case_data.get('repair_process_summary', '').strip()
        repair_summary_block = f"\n\n\nDeğerlendirme özeti: {repair_summary}" if repair_summary else ""

        body = f"""Merhaba,



Aracınıza ait {ize_no} numaralı yurtdışı IZE dosyası incelenmiş olup yapılan değerlendirme aşağıda bilgilerinize sunulmaktadır.



İlgili aracın {warranty_start_date} tarihli teslim bilgisi ve {repair_date} tarihli onarım kaydı doğrultusunda, onarımın garanti süresi {warranty_out_text} kaldığı değerlendirilmiştir.



Araç için gerçekleştirilen inceleme kapsamında {operations_text} uygulanmıştır.



{parts_summary}



İlgili IZE dosyasına ait fatura tarafınıza ayrıca iletilecektir.{repair_summary_block}



Bilgilerinize sunarız."""
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
    company = _normalize_company_name(case_data.get('company', 'N/A'))
    
    if language == "tr":
        return f"{ize_no} - {vin} - {plate} - {company} - Yurtdışı Dosyası Hk."
    else:
        return f"{ize_no} - {vin} - {plate} - {company} - International IZE File"


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
        
        # TLS ile bağlan - SSL sertifika doğrulamasını gevşet
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
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



async def send_verification_email(to_email: str, full_name: str, verification_token: str) -> dict:
    """E-posta doğrulama linki gönder"""
    
    settings = await get_email_settings()
    
    if not settings.get("email_enabled", True):
        return {"success": False, "message": "E-posta gönderimi devre dışı"}
    
    if not settings.get("smtp_password"):
        return {"success": False, "message": "SMTP şifresi ayarlanmamış"}
    
    # Site ayarlarından domain al
    site_settings = await db.site_settings.find_one({"id": "site_settings"}, {"_id": 0})
    base_url = "https://ize.visupanel.com"  # Varsayılan
    if site_settings and site_settings.get("canonical_url"):
        base_url = site_settings["canonical_url"].rstrip("/")
    
    verification_link = f"{base_url}/verify-email/{verification_token}"
    
    try:
        msg = MIMEMultipart()
        msg['From'] = f"{settings.get('sender_name', 'IZE Case Resolver')} <{settings.get('sender_email', 'info@visupanel.com')}>"
        msg['To'] = to_email
        msg['Subject'] = "E-posta Adresinizi Doğrulayın - IZE Case Resolver"
        
        body = f"""Sayın {full_name},

IZE Case Resolver'a hoş geldiniz!

Hesabınızı aktif hale getirmek için aşağıdaki linke tıklayarak e-posta adresinizi doğrulayın:

{verification_link}

Bu link 24 saat geçerlidir.

Eğer bu hesabı siz oluşturmadıysanız, bu e-postayı görmezden gelebilirsiniz.

---
IZE Case Resolver
Renault Trucks Yetkili Servisleri için Garanti Analiz Sistemi
"""
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # SMTP bağlantısı ve gönderim
        smtp_host = settings.get('smtp_host', 'smtp.visupanel.com')
        smtp_port = settings.get('smtp_port', 587)
        smtp_user = settings.get('smtp_user', 'info@visupanel.com')
        smtp_password = settings.get('smtp_password', '')
        
        # TLS ile bağlan
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
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
        
        logger.info(f"Doğrulama e-postası gönderildi: {to_email}")
        return {"success": True, "message": "Doğrulama e-postası gönderildi"}
        
    except Exception as e:
        logger.error(f"Doğrulama e-postası gönderim hatası: {str(e)}")
        return {"success": False, "message": f"E-posta gönderilemedi: {str(e)}"}
