import uvicorn

from app.app_factory import create_app

api = create_app()


if __name__ == "__main__":
    uvicorn.run(api, host="0.0.0.0", port=7860)
