# Python 3.10 / Gradio 5.43.1
import gradio as gr

def respond(message: str, history: list[dict]):
    # ここにLLM呼び出し等を入れてください（サンプルはエコー）
    return f"echo: {message}"

demo = gr.ChatInterface(
    fn=respond,
    type="messages",      # ChatGPT互換の messages 形式で履歴を扱う
    save_history=True,    # ← 履歴（擬似スレッド）をブラウザに保存＆左ペインで切替
    title="Simple Threads",   # 画面タイトル（任意）
)
demo.launch()

