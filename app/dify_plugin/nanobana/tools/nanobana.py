import base64
import mimetypes
import time
import uuid
from collections.abc import Generator
from datetime import datetime
from typing import Any

import requests
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


class NanobanaTool(Tool):
    """
    gemini-3-pro-image-preview を呼び出して画像 BLOB を返すツール
    """

    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        # Provider YAML: credentials_for_provider.api_key と対応
        api_key = self.runtime.credentials["api_key"]

        prompt = tool_parameters["prompt"]
        aspect_ratio = tool_parameters.get("aspect_ratio", "1:1")
        image_size = tool_parameters.get("image_size", "1K")

        url = (
            "https://generativelanguage.googleapis.com/v1beta/"
            "models/gemini-3-pro-image-preview:generateContent"
        )
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        }
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"],
                "imageConfig": {
                    "aspectRatio": aspect_ratio,
                    "imageSize": image_size,
                },
            },
        }

        max_retries = 3
        backoff_seconds = 1.0
        resp = None
        for attempt_index in range(max_retries):
            try:
                resp = requests.post(
                    url, json=payload, headers=headers, timeout=120
                )
                resp.raise_for_status()
                break
            except requests.exceptions.HTTPError as exc:
                status_code = (
                    exc.response.status_code
                    if exc.response is not None
                    else None
                )
                # 5xx はリトライ、429/408 も一時的としてリトライ
                is_retryable = status_code in (408, 429) or (
                    status_code is not None and 500 <= status_code < 600
                )
                is_last_attempt = attempt_index == max_retries - 1
                if is_retryable and not is_last_attempt:
                    time.sleep(backoff_seconds)
                    backoff_seconds *= 2
                    continue
                # 詳細エラーをユーザーに返却
                error_detail = ""
                if exc.response is not None:
                    try:
                        err_json = exc.response.json()
                        # Generative Language API は {error:{message, status}} 形式
                        # で返ることが多い
                        error_detail = (
                            err_json.get("error", {}).get("message")
                            or err_json.get("message")
                            or str(err_json)
                        )
                    except Exception:
                        error_detail = exc.response.text or str(exc)
                else:
                    error_detail = str(exc)
                yield self.create_text_message(
                    "Gemini API 呼び出しでHTTPエラーが発生しました。"
                    f"status={status_code}, details={error_detail}"
                )
                return
            except (
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError,
            ) as exc:
                is_last_attempt = attempt_index == max_retries - 1
                if not is_last_attempt:
                    time.sleep(backoff_seconds)
                    backoff_seconds *= 2
                    continue
                yield self.create_text_message(
                    "Gemini API 呼び出しでネットワークエラーが発生しました: "
                    f"{exc}"
                )
                return

        if resp is None:
            yield self.create_text_message(
                "Gemini API の呼び出しに失敗しました（応答なし）。"
            )
            return

        data = resp.json()

        candidates = data.get("candidates", [])
        if not candidates:
            yield self.create_text_message(
                "Gemini から候補が返ってきませんでした。"
            )
            return

        parts = candidates[0].get("content", {}).get("parts", [])

        image_b64 = None
        mime_type = "image/png"
        for p in parts:
            if "inlineData" in p:
                image_b64 = p["inlineData"].get("data")
                mime_type = p["inlineData"].get("mimeType", mime_type)
                break
            if "inline_data" in p:
                image_b64 = p["inline_data"].get("data")
                mime_type = p["inline_data"].get("mime_type", mime_type)
                break

        if not image_b64:
            texts = [
                p.get("text", "")
                for p in parts
                if isinstance(p, dict) and p.get("text")
            ]
            text = (
                "\n\n".join(texts)
                or "画像ではなくテキストのみが返されました。"
            )
            yield self.create_text_message(text)
            return

        blob = base64.b64decode(image_b64)

        # ファイル名重複を避けるためにユニークなファイル名を生成
        extension_map = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/gif": ".gif",
            "image/webp": ".webp",
        }
        extension = (
            extension_map.get(mime_type)
            or mimetypes.guess_extension(mime_type)
            or ".bin"
        )
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_suffix = uuid.uuid4().hex[:8]
        filename = f"gemini_image_{timestamp}_{unique_suffix}{extension}"

        # Dify が内部ストレージに temp を作って /files/... に公開してくれる
        yield self.create_blob_message(
            blob=blob,
            meta={
                "mime_type": mime_type,
                "filename": filename,
            },
        )
