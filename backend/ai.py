import json
import requests
from rapidfuzz import fuzz
from config import OPENAI_API_KEY, OPENAI_MODEL
from normalizer import SERVICE_CATALOG, SYMPTOM_SUGGESTIONS, clean, suggestions

SERVICE_NAMES = [name for name, _category, _synonyms in SERVICE_CATALOG]

def local_recommendation(message: str, limit: int = 6):
    q = clean(message)
    picked = []
    for symptom, services in SYMPTOM_SUGGESTIONS.items():
        if symptom in q or fuzz.partial_ratio(q, clean(symptom)) >= 72:
            picked.extend(services)
    picked.extend(suggestions(message, limit=limit))
    unique = []
    for item in picked:
        if item in SERVICE_NAMES and item not in unique:
            unique.append(item)
    return unique[:limit] or SERVICE_NAMES[:4]

def ask_ai(message: str):
    fallback_services = local_recommendation(message)
    if not OPENAI_API_KEY:
        return {
            "mode": "local_fallback",
            "reply": "Я могу подсказать возможные услуги по описанию, но это не диагноз. Для точного решения лучше обратиться к врачу.",
            "recommended_services": fallback_services,
        }

    service_list = "\n".join(f"- {name}" for name in SERVICE_NAMES)
    system = (
        "You are a medical service navigation assistant for Kazakhstan. "
        "You do not diagnose and do not prescribe treatment. "
        "Given a user's symptoms, choose only relevant service names from the provided catalog. "
        "Return strict JSON with keys: reply, recommended_services. "
        "recommended_services must be an array of 3-7 exact names from catalog. "
        "The reply must be brief, in the user's language, and include a safety note for urgent symptoms."
    )
    user = f"Catalog:\n{service_list}\n\nUser message:\n{message}"
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": OPENAI_MODEL,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
            },
            timeout=25,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        data = json.loads(content)
        chosen = [x for x in data.get("recommended_services", []) if x in SERVICE_NAMES]
        if not chosen:
            chosen = fallback_services
        return {"mode": "openai", "reply": data.get("reply") or "Вот возможные услуги для проверки.", "recommended_services": chosen[:7]}
    except Exception as exc:
        return {
            "mode": "local_fallback_after_error",
            "reply": f"ИИ временно недоступен, поэтому я использовал локальные правила. Это не диагноз. Ошибка: {str(exc)[:120]}",
            "recommended_services": fallback_services,
        }
