import os
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_OPENAI_MODEL = os.getenv("OPENAI_COMPLETION_MODEL", "gpt-4o-mini")
DEFAULT_GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")


class LanguageModelError(RuntimeError):
    """Raised when an upstream language model API request fails."""


def _pick_provider() -> tuple[str, str, str]:
    """
    Returns a tuple containing (provider, api_key, model) based on the configured environment.

    Priority order:
        1. Groq (for LLaMA derivatives) via GROQ_API_KEY.
        2. OpenAI via OPENAI_API_KEY.
    """
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        model = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)
        return "groq", groq_key, model

    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        model = os.getenv("OPENAI_COMPLETION_MODEL", DEFAULT_OPENAI_MODEL)
        return "openai", openai_key, model

    raise LanguageModelError(
        "No language model provider configured. Set GROQ_API_KEY (recommended) or OPENAI_API_KEY."
    )


def call_llama(
    prompt: str,
    *,
    system_prompt: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: Optional[int] = None,
) -> str:
    """
    Send a prompt to the configured chat-completions API and return the model response text.

    The function automatically routes to Groq if GROQ_API_KEY is set, otherwise it
    falls back to OpenAI-compatible chat completions.
    """
    provider, api_key, model = _pick_provider()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    api_url = (
        "https://api.groq.com/openai/v1/chat/completions"
        if provider == "groq"
        else "https://api.openai.com/v1/chat/completions"
    )

    request_timeout = int(os.getenv("LLM_REQUEST_TIMEOUT", "120"))
    response = requests.post(api_url, headers=headers, json=payload, timeout=request_timeout)

    if response.status_code >= 400:
        raise LanguageModelError(
            f"{provider.capitalize()} chat completion failed ({response.status_code}): {response.text}"
        )

    data = response.json()
    choices = data.get("choices", [])
    if not choices:
        raise LanguageModelError(f"{provider.capitalize()} chat completion returned no choices.")

    message = choices[0].get("message", {})
    return message.get("content", "").strip()


def generate_structured_notes(transcript: str) -> str:
    system_prompt = (
        "You are a concise study assistant. "
        "Rewrite the provided transcript into bullet-point notes organized by topic. "
        "Highlight key concepts, formulas, and any action items students should follow up on."
    )
    return call_llama(transcript, system_prompt=system_prompt, temperature=0.2)


def generate_study_plan(transcript: str) -> str:
    system_prompt = (
        "You are a helpful tutor. Based on the learner's transcript, produce an actionable study plan "
        "with 3-5 steps. Each step should include objectives, recommended resources or techniques, "
        "and estimated effort. Tailor the plan to reinforce the transcript's main themes."
    )
    return call_llama(transcript, system_prompt=system_prompt, temperature=0.4)


def generate_quiz(transcript: str) -> str:
    system_prompt = (
        "You are an academic quiz generator. Create 5 concise questions that cover the key ideas "
        "in the transcript. Mix question styles (concept checks, definitions, short applications) "
        "and provide an answer key. Keep everything brief and study-friendly."
    )
    return call_llama(transcript, system_prompt=system_prompt, temperature=0.3)
