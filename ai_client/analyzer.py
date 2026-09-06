import aiohttp
import logging
from typing import Optional
from config.settings import settings

logger = logging.getLogger(__name__)


class AIAnalyzerError(Exception):
    pass


class AIAnalyzer:
    def __init__(self, api_url: str = None, api_key: str = None, model: str = None):
        self.api_url = api_url or settings.AI_API_URL
        self.api_key = api_key or settings.AI_API_KEY
        self.model = model or settings.AI_MODEL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def analyze_note(self, note: str, reaction: str) -> dict:
        prompt = (
            "Ты — HR-ассистент. Проанализируй заметку сотрудника/кандидата о своём настроении.\n"
            f"Реакция: {reaction}\n"
            f"Заметка: {note}\n\n"
            "Ответь строго в формате JSON без лишнего текста:\n"
            '{"zone": "green|orange|red", "recommendation": "текст рекомендации для HR", "reason": "краткое обоснование"}\n'
            "Зоны:\n"
            "- green: явно положительная заметка, нет поводов для беспокойства\n"
            "- orange: есть сомнения, нейтральная или смешанная тональность\n"
            "- red: более двух подозрительных слов или явно негативный/угрожающий характер\n"
            "Не добавляй никакого текста кроме JSON."
        )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    headers=self.headers,
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "Ты HR-аналитик. Отвечай только валидным JSON."},
                            {"role": "user", "content": prompt},
                        ],
                        "max_tokens": 300,
                        "temperature": 0.2,
                    },
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status != 200:
                        text = await response.text()
                        logger.error(f"AI API error {response.status}: {text}")
                        raise AIAnalyzerError(f"AI API error {response.status}")
                    data = await response.json()
                    content = data["choices"][0]["message"]["content"].strip()
                    if content.startswith("```"):
                        content = content.strip("```")
                        if content.startswith("json"):
                            content = content[4:]
                    import json
                    result = json.loads(content)
                    if "zone" not in result:
                        raise AIAnalyzerError("Invalid AI response format")
                    return result
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return {"zone": "green", "recommendation": "Автоматический анализ не удался, требуется ручная проверка.", "reason": str(e)}
