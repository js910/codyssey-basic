import os

from google import genai
from google.genai import types


def create_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY 환경변수가 설정되지 않았습니다.\n"
            '예: export GEMINI_API_KEY="YOUR_API_KEY"'
        )

    return genai.Client(api_key=api_key)


def generate_text(
    prompt,
    model="gemini-3.5-flash-lite",
    temperature=0.3,
    max_tokens=500
):
    client = create_client()

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=True
                ),
            ),
        )

        if not response.text:
            raise RuntimeError("Gemini API가 빈 응답을 반환했습니다.")

        return response.text.strip()

    except Exception as e:
        raise RuntimeError(f"Gemini API 요청 실패: {e}")
