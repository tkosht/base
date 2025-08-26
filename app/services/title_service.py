from __future__ import annotations

"""Title suggestion service (LLM stub).

将来、LLM連携に差し替える前提のスタブ実装。
初期実装ではユーザー入力の先頭 N 文字をタイトル案として返す。
"""

from dataclasses import dataclass


DEFAULT_TITLE_MAX = 40


@dataclass
class TitleService:
    max_length: int = DEFAULT_TITLE_MAX

    def suggest_title_via_llm(self, prompt_text: str) -> str:
        text = (prompt_text or "").strip()
        if not text:
            return "(新規)"
        if len(text) > self.max_length:
            return text[: self.max_length] + "…"
        return text
