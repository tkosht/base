from __future__ import annotations

from app.utils.svg import write_emoji_svg


def prepare_avatars() -> tuple[str, str]:
    user = write_emoji_svg(
        "💻",
        "/tmp/gradio_user_avatar.svg",
        bg="#DBEAFE",
        pad=6,
        emoji_scale=0.82,
        dy_em=0.02,
    )
    bot = write_emoji_svg("🦜", "/tmp/gradio_bot_avatar.svg", bg="#E5E7EB")
    return user, bot


