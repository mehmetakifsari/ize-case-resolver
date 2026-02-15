import os
import json
import logging
from typing import Dict, List, Any, Tuple
from fastapi import HTTPException
from openai import AsyncOpenAI, RateLimitError

logger = logging.getLogger(__name__)

MAX_PROMPT_CHARS = 10000
MAX_RULES_CHARS = 2500
MAX_INPUT_TOKENS_BUDGET = 7000
PRIMARY_MAX_COMPLETION_TOKENS = 1500
FALLBACK_MAX_COMPLETION_TOKENS = 800


def _estimate_tokens(text: str) -> int:
    """Kabaca token tahmini (güvenli tarafta kalacak şekilde)."""
    if not text:
        return 0
    return max(1, int(len(text) / 3.2))


def _trim_text(text: str, max_chars: int) -> str:
    """Metni karakter limitine göre kırpar."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[... METİN UZUN OLDUĞU İÇİN KIRPILDI ...]"


def _prioritize_pdf_lines(pdf_text: str, max_chars: int = MAX_PROMPT_CHARS) -> str:
    """Uzun PDF metninden kritik satırları öne çıkarıp güvenli uzunlukta döndürür."""
    normalized_text = pdf_text.replace("\r", "")
    lines = [line.strip() for line in normalized_text.split("\n") if line.strip()]

    if not lines:
        return ""

    priority_keywords = [
        "ize", "vin", "plaka", "plate", "fahrgestell", "zul.", "delivery", "leistungsdatum",
        "werkstattrechnung", "rechnung", "complaint", "failure", "operation", "position", "rt", "km", "warranty"
    ]

    def score_line(line: str) -> int:
        lower_line = line.lower()
        score = sum(1 for keyword in priority_keywords if keyword in lower_line)
        if any(char.isdigit() for char in line):
            score += 1
        return score

    scored_lines = sorted(lines, key=score_line, reverse=True)

    selected: List[str] = []
    selected_set = set()
    total_chars = 0

    for line in scored_lines:
        line_len = len(line) + 1
        if total_chars + line_len > int(max_chars * 0.8):
            continue
        selected.append(line)
        selected_set.add(line)
        total_chars += line_len

    for line in lines:
        line_len = len(line) + 1
        if total_chars + line_len > max_chars:
            break
        if line not in selected_set:
            selected.append(line)
            selected_set.add(line)
            total_chars += line_len

    compact_text = "\n".join(selected)
    return _trim_text(compact_text, max_chars)


def _build_messages(
    warranty_rules: List[Dict[str, Any]],
    pdf_text: str,
    rules_limit: int,
    pdf_limit: int,
) -> Tuple[str, str]:
    rules_text = "\n\n".join([
        f"Kural Versiyonu: {rule['rule_version']}\n{rule['rule_text']}\nAnahtar Kelimeler: {', '.join(rule['keywords'])}"
        for rule in warranty_rules
    ])
    rules_text = _trim_text(rules_text, rules_limit)
    compact_pdf_text = _prioritize_pdf_lines(pdf_text, pdf_limit)

    system_message = """Sen Renault Trucks için yurtdışı garanti IZE dosyalarını analiz eden bir asistansın.
Sadece geçerli JSON döndür.
Tarihleri YYYY-MM-DD formatına çevir.
Garanti kararını COVERED, OUT_OF_COVERAGE veya ADDITIONAL_INFO_REQUIRED olarak ver.
İşlemler ve değişen parçalar listelerini olabildiğince doldur."""

    prompt = f"""
IZE DOSYASI ANALİZ TALEBİ

--- GARANTİ KURALLARI ---
{rules_text}

--- IZE DOSYA METNİ ---
{compact_pdf_text}

Aşağıdaki JSON şemasına göre cevap ver:
{{
  "ize_no": "",
  "company": "",
  "plate": "",
  "vin": "",
  "warranty_start_date": "YYYY-MM-DD veya null",
  "repair_date": "YYYY-MM-DD veya null",
  "vehicle_age_months": 0,
  "repair_km": 0,
  "request_type": "WARRANTY SUPPORT veya BREAKDOWN ASSISTANCE",
  "is_within_2_year_warranty": false,
  "warranty_decision": "COVERED|OUT_OF_COVERAGE|ADDITIONAL_INFO_REQUIRED",
  "decision_rationale": [""],
  "failure_complaint": "",
  "failure_cause": "",
  "operations_performed": [""],
  "parts_replaced": [{{"partName":"", "description":"", "qty":1}}],
  "repair_process_summary": "",
  "email_subject": "",
  "email_body": ""
}}

Yalnızca JSON döndür.
"""

    return system_message, prompt


async def analyze_ize_with_ai(pdf_text: str, warranty_rules: List[Dict[str, Any]], db_settings: Dict[str, Any] = None) -> Dict[str, Any]:
    """OpenAI ile IZE dosyasını analiz eder"""
    try:
        api_key = None
        if db_settings:
            api_key = db_settings.get('openai_key')
        if not api_key:
            api_key = os.environ.get('OPENAI_API_KEY', '')

        if not api_key:
            raise HTTPException(status_code=500, detail="OpenAI API anahtarı bulunamadı")

        client = AsyncOpenAI(api_key=api_key)

        attempts = [
            (MAX_RULES_CHARS, MAX_PROMPT_CHARS, PRIMARY_MAX_COMPLETION_TOKENS),
            (1200, 3500, FALLBACK_MAX_COMPLETION_TOKENS),
        ]

        last_rate_limit_error = None

        for idx, (rules_limit, pdf_limit, completion_tokens) in enumerate(attempts, 1):
            system_message, prompt = _build_messages(
                warranty_rules=warranty_rules,
                pdf_text=pdf_text,
                rules_limit=rules_limit,
                pdf_limit=pdf_limit,
            )

            approx_input_tokens = _estimate_tokens(system_message) + _estimate_tokens(prompt)

            if approx_input_tokens > MAX_INPUT_TOKENS_BUDGET:
                logger.warning(
                    f"AI giriş token tahmini yüksek ({approx_input_tokens}). "
                    f"Deneme={idx}, rules_limit={rules_limit}, pdf_limit={pdf_limit}"
                )

            logger.info(
                f"AI istek denemesi={idx}, yaklaşık input token={approx_input_tokens}, "
                f"max_completion={completion_tokens}"
            )

            try:
                response = await client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=completion_tokens
                )

                response_text = response.choices[0].message.content.strip()

                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.startswith("```"):
                    response_text = response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]

                analysis_result = json.loads(response_text.strip())
                return analysis_result
            except RateLimitError as e:
                last_rate_limit_error = e
                logger.warning(f"Rate limit deneme {idx} başarısız: {str(e)}")
                continue

        logger.error(f"OpenAI rate limit hatası (tüm denemeler başarısız): {str(last_rate_limit_error)}")
        raise HTTPException(
            status_code=429,
            detail="OpenAI token limiti aşıldı. Dosya özeti çok büyük olabilir; lütfen daha kısa PDF veya daha az sayfa içeren dosya yükleyin."
        )

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI yanıtı işlenemedi: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI analiz hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analiz hatası: {str(e)}")
