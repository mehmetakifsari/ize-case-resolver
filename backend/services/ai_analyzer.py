import os
import json
import logging
from typing import Dict, List, Any
from fastapi import HTTPException
from openai import AsyncOpenAI, RateLimitError

logger = logging.getLogger(__name__)

MAX_PROMPT_CHARS = 12000
MAX_RULES_CHARS = 4000


def _estimate_tokens(text: str) -> int:
    """Kabaca token tahmini (Türkçe/İngilizce karışık metin için güvenli tarafta)"""
    if not text:
        return 0
    # 1 token ~= 3.2 karakter varsayımı (güvenli)
    return max(1, int(len(text) / 3.2))


def _trim_text(text: str, max_chars: int) -> str:
    """Metni limit içinde tutar ve kırpıldığını belirtir."""
    if len(text) <= max_chars:
        return text
    return (
        text[:max_chars]
        + "\n\n[... METİN UZUN OLDUĞU İÇİN DEVAMI KIRPILDI. SADECE GÖRÜNEN KISMA GÖRE ANALİZ ET ...]"
    )


def _prioritize_pdf_lines(pdf_text: str, max_chars: int = MAX_PROMPT_CHARS) -> str:
    """Uzun PDF metninden kritik satırları öne çıkarıp güvenli uzunlukta döndürür."""
    normalized_text = pdf_text.replace("\r", "")
    lines = [line.strip() for line in normalized_text.split("\n") if line.strip()]

    if not lines:
        return ""

    priority_keywords = [
        "ize",
        "vin",
        "plaka",
        "plate",
        "fahrgestell",
        "zul.",
        "delivery",
        "leistungsdatum",
        "werkstattrechnung",
        "rechnung",
        "complaint",
        "failure",
        "operation",
        "position",
        "rt",
        "km",
        "warranty",
    ]

    def score_line(line: str) -> int:
        lower_line = line.lower()
        score = sum(1 for keyword in priority_keywords if keyword in lower_line)
        if any(char.isdigit() for char in line):
            score += 1
        return score

    scored_lines = sorted(lines, key=score_line, reverse=True)

    selected: List[str] = []
    total_chars = 0
    # Önce yüksek skorlu satırları topla
    for line in scored_lines:
        line_len = len(line) + 1
        if total_chars + line_len > int(max_chars * 0.8):
            continue
        selected.append(line)
        total_chars += line_len

    # Ardından belge akışını korumak için baştan lineer ekleme yap
    for line in lines:
        line_len = len(line) + 1
        if total_chars + line_len > max_chars:
            break
        if line not in selected:
            selected.append(line)
            total_chars += line_len

    compact_text = "\n".join(selected)
    return _trim_text(compact_text, max_chars)


async def analyze_ize_with_ai(pdf_text: str, warranty_rules: List[Dict[str, Any]], db_settings: Dict[str, Any] = None) -> Dict[str, Any]:
    """OpenAI ile IZE dosyasını analiz eder"""
    try:
        # Garanti kurallarını birleştir
        rules_text = "\n\n".join([
            f"Kural Versiyonu: {rule['rule_version']}\n{rule['rule_text']}\nAnahtar Kelimeler: {', '.join(rule['keywords'])}"
            for rule in warranty_rules
        ])
        rules_text = _trim_text(rules_text, MAX_RULES_CHARS)
        compact_pdf_text = _prioritize_pdf_lines(pdf_text, MAX_PROMPT_CHARS)
        
        # API Key öncelik sırası: 
        # 1. Panel'deki OpenAI key
        # 2. Environment'taki OPENAI_API_KEY
        api_key = None
        if db_settings:
            api_key = db_settings.get('openai_key')
        if not api_key:
            api_key = os.environ.get('OPENAI_API_KEY', '')
        
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenAI API anahtarı bulunamadı")
        
        client = AsyncOpenAI(api_key=api_key)
        
        system_message = """Sen Renault Trucks için yurtdışı garanti IZE dosyalarını analiz eden uzman bir sistemsin.
            
GÖREVİN: PDF'deki tüm teknik detayları dikkatle okuyup yapılandırılmış JSON formatında çıkartmak.

ÖNEMLİ TALIMATLAR:
1. Parça isimlerini ve işlemleri Almanca veya İngilizce orijinal hallerinde de belirt
2. Tüm tarihleri YYYY-MM-DD formatına çevir (ör: 22.12.2023 → 2023-12-22)
3. Araç yaşını teslimat tarihi ile işlem tarihi arasındaki fark olarak hesapla
4. Yapılan tüm işlemleri madde madde listele (eksik bırakma)
5. Değiştirilen her parçayı ayrı ayrı belirt
6. Garanti değerlendirmesini kurallara göre yap (MHDV: 12 ay, Powertrain: +12 ay)
7. Email metnini profesyonel, kibar ve Türkçe yaz

ÇIKTI FORMATI (SADECE JSON):
{
    "ize_no": "IZE numarası (ör: IZE26006539)",
    "company": "Müşteri firma adı tam hali",
    "plate": "Plaka numarası",
    "vin": "VIN/Şasi numarası tam hali",
    "warranty_start_date": "YYYY-MM-DD (Teslimat/Zul. Datum)",
    "repair_date": "YYYY-MM-DD (İşlem tarihi)",
    "vehicle_age_months": araç_yaşı_ay_cinsinden_sayı,
    "repair_km": kilometre_sayısı,
    "request_type": "WARRANTY SUPPORT veya BREAKDOWN ASSISTANCE",
    "is_within_2_year_warranty": true/false (24 ay içinde mi?),
    "warranty_decision": "COVERED veya OUT_OF_COVERAGE veya ADDITIONAL_INFO_REQUIRED",
    "decision_rationale": [
        "Garanti kararının detaylı gerekçeleri",
        "Araç yaşı, parça türü, kapsam durumu"
    ],
    "failure_complaint": "Müşteri şikayeti veya arıza belirtisi (varsa)",
    "failure_cause": "Teknik arıza nedeni (hangi parça/sistem arızalandı)",
    "operations_performed": [
        "İşlem 1: Tam açıklama (ör: Tachometer Geber auswechseln - Takometre sensörü değişimi)",
        "İşlem 2: Tam açıklama (ör: Tachoprüfung Digital nach § 57b - Dijital takograf testi)",
        "... tüm işlemler"
    ],
    "parts_replaced": [
        {
            "partName": "Parça adı (orijinal + Türkçe)",
            "description": "Parçanın fonksiyonu ve neden değiştirildiği",
            "qty": 1
        }
    ],
    "repair_process_summary": "Yapılan işlemlerin kronolojik özeti: Ne yapıldı, hangi parçalar değişti, sonuç nedir",
    "email_subject": "Yurtdışı IZE Dosyası Hk. - IZE NO - PLAKA - ŞASİ",
    "email_body": "Sayın İlgili,\\n\\nYurtdışı [Firma] firmasından gelen IZE NO: [numara] numaralı dosya incelenmiştir...\\n\\nDetaylı ve kibar email metni"
}

SADECE JSON ÇIKTISI VER, BAŞKA AÇIKLAMA EKLEME!"""
        
        # Analiz mesajı oluştur
        prompt = f"""
IZE DOSYASI ANALİZ TALEBİ

--- RENAULT TRUCKS GARANTİ KURALLARI ---
{rules_text}

--- IZE DOSYASI HAM İÇERİK (TÜM SAYFALAR) ---
{compact_pdf_text}

--- ANALİZ TALİMATLARI ---
1. Yukarıdaki IZE dosyasındaki TÜM bilgileri dikkatle oku (özellikle WERKSTATTRECHNUNG ve fatura sayfalarını)
2. Araç bilgilerini çıkar (IZE no, firma, plaka, VIN, tarihler, km)
3. WERKSTATTRECHNUNG (atölye faturası) bölümünü bul ve yapılan TÜM işlemleri detaylıca listele
4. Her işlemin kod numarasını, Almanca ismini ve Türkçe açıklamasını belirt
5. Değiştirilen TÜM parçaları belirt (RT ile başlayan parça kodları, orijinal isim + Türkçe)
6. Teslimat tarihi (Zul. Datum veya Delivery Date) ile işlem tarihi (Leistungsdatum) arasındaki farkı hesapla
7. Garanti kurallarına göre değerlendirme yap:
   - MHDV: 12 ay temel garanti
   - Powertrain bileşenleri (motor, şanzıman, aks): +12 ay (toplam 24 ay)
   - LCV: 36 ay
   - Garanti dışı parçalar: Batarya, fren, debriyaj, cam, lastik, kayış, burç
8. Profesyonel ve kibar bir email metni oluştur (Türkçe)

ÖNEMLİ: İşlemler ve parçalar bölümünü boş bırakma! WERKSTATTRECHNUNG bölümündeki her satırı oku!

SADECE JSON formatında çıktı ver. Başka hiçbir metin ekleme!
"""
        
        approx_input_tokens = _estimate_tokens(system_message) + _estimate_tokens(prompt)
        logger.info(f"AI istek tahmini token: {approx_input_tokens}")

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=4000
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # JSON parse et
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        analysis_result = json.loads(response_text.strip())
        return analysis_result
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI yanıtı işlenemedi: {str(e)}")
    except RateLimitError as e:
        logger.error(f"OpenAI rate limit hatası: {str(e)}")
        raise HTTPException(
            status_code=429,
            detail="PDF içeriği çok uzun olduğu için analiz limiti aşıldı. Daha kısa belge yükleyin veya belgeyi parçalara bölün."
        )
    except Exception as e:
        logger.error(f"AI analiz hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analiz hatası: {str(e)}")
