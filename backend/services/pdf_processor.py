import io
import logging
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
from fastapi import HTTPException

logger = logging.getLogger(__name__)

MIN_PAGE_TEXT_LEN = 50
MIN_OCR_TEXT_LEN = 20
OCR_DPI = 200
MAX_OCR_PAGES = 3
MAX_ANALYZE_PAGES = 20


def extract_text_from_pdf(pdf_file: bytes) -> str:
    """PDF'den metin çıkarır - OCR destekli geliştirilmiş versiyon"""
    try:
        text_chunks = []
        ocr_used_pages = 0
        
        # Önce pdfplumber ile dene
        with pdfplumber.open(io.BytesIO(pdf_file)) as pdf:
            total_pages = len(pdf.pages)
            logger.info(f"PDF toplam {total_pages} sayfa içeriyor")

            pages_to_process = min(total_pages, MAX_ANALYZE_PAGES)
            if total_pages > MAX_ANALYZE_PAGES:
                logger.warning(
                    f"PDF çok uzun ({total_pages} sayfa). Performans için ilk {MAX_ANALYZE_PAGES} sayfa işlenecek"
                )
            
            for page_num, page in enumerate(pdf.pages[:pages_to_process], 1):
                page_text = page.extract_text()
                
                if page_text and len(page_text.strip()) > MIN_PAGE_TEXT_LEN:
                    # Normal metin çıkarma başarılı
                    text_chunks.append(f"\n\n--- SAYFA {page_num} ---\n{page_text}")
                    logger.info(f"Sayfa {page_num} işlendi (normal): {len(page_text)} karakter")
                else:
                    if ocr_used_pages >= MAX_OCR_PAGES:
                        logger.info(
                            f"Sayfa {page_num} için OCR atlandı (OCR limitine ulaşıldı: {MAX_OCR_PAGES})"
                        )
                        continue

                    # Sayfa boş veya çok az metin - OCR dene
                    logger.warning(f"Sayfa {page_num} boş/az metin, OCR ile deneniyor...")
                    try:
                        # PDF sayfasını görüntüye çevir
                        images = convert_from_bytes(
                            pdf_file, 
                            first_page=page_num, 
                            last_page=page_num,
                            dpi=OCR_DPI,
                            thread_count=1
                        )
                        
                        if images:
                            ocr_used_pages += 1
                            # OCR uygula (Almanca ve Türkçe dil desteği)
                            ocr_text = pytesseract.image_to_string(
                                images[0], 
                                lang='deu+tur+eng',
                                config='--psm 6'
                            )
                            
                            if ocr_text and len(ocr_text.strip()) > MIN_OCR_TEXT_LEN:
                                text_chunks.append(f"\n\n--- SAYFA {page_num} (OCR) ---\n{ocr_text}")
                                logger.info(f"Sayfa {page_num} OCR ile işlendi: {len(ocr_text)} karakter")
                            else:
                                logger.warning(f"Sayfa {page_num} OCR sonuç vermedi")
                    except Exception as ocr_error:
                        logger.error(f"Sayfa {page_num} OCR hatası: {str(ocr_error)}")

        text = "".join(text_chunks)
        
        if not text or len(text) < 100:
            logger.error("PDF'den yeterli metin çıkarılamadı")
            raise HTTPException(status_code=400, detail="PDF'den yeterli metin çıkarılamadı")
        
        logger.info(f"Toplam çıkarılan metin: {len(text)} karakter")
        return text.strip()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF okuma hatası: {str(e)}")
        raise HTTPException(status_code=400, detail=f"PDF okunamadı: {str(e)}")
