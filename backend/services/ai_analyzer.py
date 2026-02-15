import os
import json
import logging
from typing import Dict, List, Any, Tuple
from fastapi import HTTPException
from openai import AsyncOpenAI, RateLimitError

logger = logging.getLogger(__name__)

# Sert limitler: TPM aşımını engellemek için düşük tutuldu
MAX_PROMPT_CHARS = 3500
MAX_RULES_CHARS = 900
MAX_RULE_COUNT = 3
MAX_RULE_SINGLE_CHARS = 300
MAX_INPUT_TOKENS_BUDGET = 3000
PRIMARY_MAX_COMPLETION_TOKENS = 700
FALLBACK_MAX_COMPLETION_TOKENS = 400


def _estimate_tokens(text: str) -> int:
    """Güvenli tarafta kalacak şekilde kaba token tahmini."""
    if not text:
        return 0
    # Daha konservatif yaklaşım: 1 token ~= 2.7 karakter
    return max(1, int(len(text) / 2.7))


def _trim_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n[... KIRPILDI ...]"


def _prioritize_pdf_lines(pdf_text: str, max_chars: int = MAX_PROMPT_CHARS) -> str:
    normalized_text = pdf_text.replace("\r", "")
    lines = [line.strip() for line in normalized_text.split("\n") if line.strip()]

    if not lines:
        return ""

    priority_keywords = [
        "ize", "vin", "plaka", "plate", "fahrgestell", "zul", "delivery", "leistungsdatum",
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
        if total_chars + line_len > max_chars:
            continue
        selected.append(line)
        selected_set.add(line)
        total_chars += line_len
        if total_chars >= int(max_chars * 0.85):
            break

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


def _select_relevant_rules(warranty_rules: List[Dict[str, Any]], pdf_text: str) -> List[Dict[str, Any]]:
    """Warranty binder gibi büyük kural setlerinde sadece ilgili küçük alt kümeyi seç."""
    if not warranty_rules:
        return []

    pdf_lower = pdf_text.lower()

    def score_rule(rule: Dict[str, Any]) -> int:
        score = 0
        for keyword in rule.get("keywords", []):
            kw = str(keyword).strip().lower()
            if kw and kw in pdf_lower:
                score += 2
        rule_text = str(rule.get("rule_text", "")).lower()
        for marker in ["mhdv", "powertrain", "lcv", "12 ay", "24 ay", "36 ay", "garanti"]:
            if marker in rule_text and marker in pdf_lower:
                score += 1
        return score

    ranked = sorted(warranty_rules, key=score_rule, reverse=True)
    selected = ranked[:MAX_RULE_COUNT]

    normalized = []
    for rule in selected:
        normalized.append({
            "rule_version": str(rule.get("rule_version", "N/A")),
            "rule_text": _trim_text(str(rule.get("rule_text", "")), MAX_RULE_SINGLE_CHARS),
            "keywords": [str(k) for k in rule.get("keywords", [])[:8]],
        })
    return normalized


def _build_messages(
    warranty_rules: List[Dict[str, Any]],
    pdf_text: str,
    rules_limit: int,
    pdf_limit: int,
) -> Tuple[str, str]:
    selected_rules = _select_relevant_rules(warranty_rules, pdf_text)
    rules_text = "\n\n".join([
        f"Versiyon: {rule['rule_version']}\nKural: {rule['rule_text']}\nAnahtar: {', '.join(rule['keywords'])}"
        for rule in selected_rules
    ])
    rules_text = _trim_text(rules_text, rules_limit)
    compact_pdf_text = _prioritize_pdf_lines(pdf_text, pdf_limit)

    system_message = (
        "Renault Trucks IZE analiz asistanısın. "
        "Sadece geçerli JSON döndür. "
        "Tarih formatı YYYY-MM-DD olsun. "
        "Garanti kararı yalnızca COVERED, OUT_OF_COVERAGE veya ADDITIONAL_INFO_REQUIRED olsun."
    )

    prompt = f"""
IZE ANALİZ

KURALLAR:
{rules_text}

PDF ÖZETİ:
{compact_pdf_text}

JSON şeması:
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

Sadece JSON ver.
"""

    return system_message, prompt


async def analyze_ize_with_ai(pdf_text: str, warranty_rules: List[Dict[str, Any]], db_settings: Dict[str, Any] = None) -> Dict[str, Any]:
    """OpenAI ile IZE dosyasını analiz eder."""
    try:
        api_key = db_settings.get("openai_key") if db_settings else None
        if not api_key:
            api_key = os.environ.get("OPENAI_API_KEY", "")

        if not api_key:
            raise HTTPException(status_code=500, detail="OpenAI API anahtarı bulunamadı")

        client = AsyncOpenAI(api_key=api_key)

        attempts = [
            (MAX_RULES_CHARS, MAX_PROMPT_CHARS, PRIMARY_MAX_COMPLETION_TOKENS),
            (500, 1800, FALLBACK_MAX_COMPLETION_TOKENS),
            (300, 1100, 250),
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
                # Sert kesme: token bütçesi aşılıyorsa promptu daha da kıs
                force_chars = max(600, int(len(prompt) * 0.55))
                prompt = _trim_text(prompt, force_chars)
                approx_input_tokens = _estimate_tokens(system_message) + _estimate_tokens(prompt)

            logger.info(
                "AI deneme=%s input_tokens~%s max_completion=%s rules_limit=%s pdf_limit=%s",
                idx,
                approx_input_tokens,
                completion_tokens,
                rules_limit,
                pdf_limit,
            )

            try:
                response = await client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=completion_tokens,
                )

                response_text = response.choices[0].message.content.strip()
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.startswith("```"):
                    response_text = response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]

                return json.loads(response_text.strip())

            except RateLimitError as e:
                last_rate_limit_error = e
                logger.warning("Rate limit deneme %s başarısız: %s", idx, str(e))
                continue

        logger.error("OpenAI rate limit (tüm denemeler başarısız): %s", str(last_rate_limit_error))
        raise HTTPException(
            status_code=429,
            detail="OpenAI token limiti aşıldı. Warranty kural seti ve PDF içeriği otomatik kısaltıldı fakat yine de limit aşıldı; lütfen tekrar deneyin."
        )

    except json.JSONDecodeError as e:
        logger.error("JSON parse hatası: %s", str(e))
        raise HTTPException(status_code=500, detail=f"AI yanıtı işlenemedi: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("AI analiz hatası: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Analiz hatası: {str(e)}")
