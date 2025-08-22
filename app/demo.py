import uvicorn

try:
    # パッケージ実行時
    from .app_factory import create_app
except Exception:  # pragma: no cover - スクリプト実行時のフォールバック
    # スクリプト実行時 (python app/demo.py)
    from app.app_factory import create_app  # type: ignore


api = create_app()


if __name__ == "__main__":
    uvicorn.run(api, host="0.0.0.0", port=7860)


