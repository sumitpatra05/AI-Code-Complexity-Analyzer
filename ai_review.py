"""Gemini-powered AI code review with safe retries and complete output."""

import os
import time
import re
import json
from dotenv import load_dotenv

load_dotenv()

TRANSIENT_STATUS_CODES = {408, 429, 500, 502, 503, 504}


def get_status_code(exc):
    for attr in ("status_code", "code"):
        value = getattr(exc, attr, None)
        if isinstance(value, int):
            return value

    response = getattr(exc, "response", None)
    value = getattr(response, "status_code", None)

    if isinstance(value, int):
        return value

    match = re.search(
        r"\b(408|429|500|502|503|504)\b",
        str(exc)
    )

    return int(match.group(1)) if match else None


def ai_review(source: str, report: dict,
              language: str = "python") -> str:

    key = os.getenv("GEMINI_API_KEY")

    if not key:
        return "AI review unavailable: GEMINI_API_KEY is missing."

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=key)

        model = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.8-flash"
        )

        prompt = f"""
You are a senior software engineer and code reviewer.

Analyze the following {language.upper()} program carefully.

STATIC ANALYSIS REPORT:
{json.dumps(report, indent=2, default=str)}

SOURCE CODE:
{source}

Write a COMPLETE review using exactly these sections:

# Code Review

## 1. Code Quality
- Explain code quality.
- Identify code smells and coding issues.

## 2. Time Complexity
- Give function-wise Big-O complexity.
- Explain the reason.
- Mention when an estimate is uncertain.

## 3. Space Complexity
- Explain auxiliary space.
- Mention recursion stack and dynamic memory if applicable.

## 4. Performance Bottlenecks
- Identify inefficient loops, recursion or operations.
- Explain their impact.

## 5. Optimization Suggestions
- Give exactly three practical improvements.
- Include corrected code snippets where useful.

## 6. Final Verdict
- Summarize strengths and weaknesses.
- Mention the most important improvement.

IMPORTANT:
- Review the actual source code.
- Do not invent benchmark results.
- Do not blindly trust static-analysis estimates.
- Explain complexity accurately.
- Complete every section.
- Keep the response concise but informative.
"""

        max_attempts = 3

        for attempt in range(max_attempts):

            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        max_output_tokens=4000,
                        temperature=0.3
                    )
                )

                result = response.text

                if result and result.strip():
                    return result.strip()

                return "Gemini returned an empty review."

            except Exception as exc:

                status = get_status_code(exc)

                if status not in TRANSIENT_STATUS_CODES:
                    return (
                        f"Gemini API Error: "
                        f"{type(exc).__name__}: {exc}"
                    )

                if attempt == max_attempts - 1:
                    return (
                        f"Gemini temporarily unavailable "
                        f"(HTTP {status}). "
                        "Local code analysis is still available. "
                        "Please try again later."
                    )

                time.sleep(2 ** (attempt + 1))

    except Exception as exc:
        return (
            f"Gemini setup error: "
            f"{type(exc).__name__}: {exc}"
        )