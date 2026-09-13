"""Personal Telegram bot — Jork-like Single / Batch / Combine → RunPod Flux+PuLID."""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from io import BytesIO
from typing import Literal

from dotenv import load_dotenv
from telegram import InputMediaPhoto, Message, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.request import HTTPXRequest

from keyboard import (
    BTN_BATCH,
    BTN_CANCEL,
    BTN_COMBINE,
    BTN_SINGLE,
    MAIN_KEYBOARD,
    preset_keyboard,
)
from presets import PRESETS
from runpod_client import RunPodError, generate_one
from safety import blocks_minors

load_dotenv()

# Telegram bot tokens in URLs look like: api.telegram.org/bot<token>/method
_TOKEN_IN_URL = re.compile(
    r"(https?://api\.telegram\.org/bot)([^/\s]+)(/)",
    re.IGNORECASE,
)
# Also catch bare bot<digits:secret> patterns if logged outside full URLs
_BARE_BOT_TOKEN = re.compile(r"\b(\d{6,}:[A-Za-z0-9_-]{20,})\b")


class _RedactTelegramTokenFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
        except Exception:
            return True
        redacted = _TOKEN_IN_URL.sub(r"\1[REDACTED]\3", msg)
        redacted = _BARE_BOT_TOKEN.sub("[REDACTED]", redacted)
        if redacted != msg:
            record.msg = redacted
            record.args = ()
        return True


def _configure_logging() -> None:
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(message)s",
        )
    redact = _RedactTelegramTokenFilter()
    for handler in logging.root.handlers:
        handler.addFilter(redact)
    # httpx logs full request URLs at INFO by default
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


_configure_logging()
log = logging.getLogger("bot")

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
ALLOWED = os.environ.get("ALLOWED_USER_ID", "").strip()
MAX_BATCH = 10

Mode = Literal["idle", "single", "batch", "combine"]


@dataclass
class Session:
    mode: Mode = "idle"
    photos: list[bytes] = field(default_factory=list)
    prompt: str | None = None
    awaiting_custom: bool = False


def _sessions(context: ContextTypes.DEFAULT_TYPE) -> dict[int, Session]:
    return context.application.bot_data.setdefault("sessions", {})


def _session(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> Session:
    store = _sessions(context)
    if user_id not in store:
        store[user_id] = Session()
    return store[user_id]


def _allowed(user_id: int) -> bool:
    if not ALLOWED:
        return False
    return str(user_id) == ALLOWED


def _reset(sess: Session, mode: Mode = "idle") -> None:
    sess.mode = mode
    sess.photos = []
    sess.prompt = None
    sess.awaiting_custom = False


def _preset_prompt_text(n: int, mode: Mode) -> str:
    if mode == "single":
        return (
            f"Got {n} photo. Pick a preset, or Custom prompt.\n"
            "Optional: caption a photo to run immediately."
        )
    return (
        f"Got {n} photo(s). Send more, pick a preset, or Custom prompt.\n"
        "Optional: caption a photo to run immediately."
    )


async def _show_presets(msg: Message, sess: Session) -> None:
    await msg.reply_text(
        _preset_prompt_text(len(sess.photos), sess.mode),
        reply_markup=preset_keyboard(),
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or not _allowed(user.id):
        await update.message.reply_text("Not authorized.")
        return
    _reset(_session(context, user.id))
    await update.message.reply_text(
        "Hey — send photos after picking a mode.\n"
        "• Single: 1 photo → preset or prompt\n"
        "• Batch: up to 10 photos → one preset/prompt (1 out each)\n"
        "• Combine: several refs → one image\n\n"
        "Adult OK. Minors hard-blocked.",
        reply_markup=MAIN_KEYBOARD,
    )


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    msg = update.message
    if not user or not msg or not msg.text:
        return
    if not _allowed(user.id):
        await msg.reply_text("Not authorized.")
        return

    text = msg.text.strip()
    sess = _session(context, user.id)

    if text == BTN_SINGLE:
        _reset(sess, "single")
        await msg.reply_text(
            "Single mode — send 1 photo, then pick a preset or type a prompt."
        )
        return
    if text == BTN_BATCH:
        _reset(sess, "batch")
        await msg.reply_text(
            "Batch mode — send up to 10 photos (album OK), then a preset or prompt."
        )
        return
    if text == BTN_COMBINE:
        _reset(sess, "combine")
        await msg.reply_text(
            "Combine mode — send 2–10 refs, then a preset or prompt."
        )
        return
    if text == BTN_CANCEL:
        _reset(sess)
        await msg.reply_text("Cancelled.", reply_markup=MAIN_KEYBOARD)
        return

    if sess.mode == "idle":
        await msg.reply_text("Pick Single / Batch / Combine first.", reply_markup=MAIN_KEYBOARD)
        return

    reason = blocks_minors(text)
    if reason:
        await msg.reply_text(reason)
        return

    if not sess.photos:
        await msg.reply_text("Send photo(s) first, then a preset or prompt.")
        return

    sess.awaiting_custom = False
    # Custom / typed prompts still get the identity/photoreal prefix.
    sess.prompt = f"{PRESETS['custom']['prompt']}. {text}"
    await _run(msg, sess)


async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    msg = update.message
    if not user or not msg or not msg.photo:
        return
    if not _allowed(user.id):
        await msg.reply_text("Not authorized.")
        return

    sess = _session(context, user.id)
    if sess.mode == "idle":
        await msg.reply_text("Pick Single / Batch / Combine first.", reply_markup=MAIN_KEYBOARD)
        return

    if sess.mode == "single" and len(sess.photos) >= 1:
        await msg.reply_text(
            "Single mode already has a photo. Pick a preset, type a prompt, or Cancel."
        )
        return
    if len(sess.photos) >= MAX_BATCH:
        await msg.reply_text(
            f"Max {MAX_BATCH} photos. Pick a preset, type a prompt, or Cancel."
        )
        return

    photo = msg.photo[-1]
    tg_file = await context.bot.get_file(photo.file_id)
    buf = BytesIO()
    await tg_file.download_to_memory(buf)
    sess.photos.append(buf.getvalue())
    sess.awaiting_custom = False

    caption = (msg.caption or "").strip()
    if caption:
        reason = blocks_minors(caption)
        if reason:
            await msg.reply_text(reason)
            return
        sess.prompt = f"{PRESETS['custom']['prompt']}. {caption}"
        await _run(msg, sess)
        return

    await _show_presets(msg, sess)


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = update.effective_user
    if not query or not user:
        return
    if not _allowed(user.id):
        await query.answer("Not authorized.", show_alert=True)
        return

    raw = query.data or ""
    if not raw.startswith("p:"):
        await query.answer()
        return

    key = raw.split(":", 1)[1]
    if key not in PRESETS:
        await query.answer("Unknown preset.", show_alert=True)
        return

    sess = _session(context, user.id)
    if sess.mode == "idle" or not sess.photos:
        await query.answer("Send photo(s) in a mode first.", show_alert=True)
        return

    await query.answer()

    if key == "custom":
        sess.awaiting_custom = True
        sess.prompt = None
        try:
            await query.edit_message_text(
                "Type your custom prompt as a text message. "
                "Minors are still hard-blocked."
            )
        except Exception:
            if query.message:
                await query.message.reply_text(
                    "Type your custom prompt as a text message. "
                    "Minors are still hard-blocked."
                )
        return

    sess.awaiting_custom = False
    sess.prompt = PRESETS[key]["prompt"]
    msg = query.message
    if not msg:
        return
    try:
        await query.edit_message_text(f"Running preset: {PRESETS[key]['title']}…")
    except Exception:
        pass
    await _run(msg, sess)


async def _run(msg: Message, sess: Session) -> None:
    assert sess.prompt

    photos = list(sess.photos)
    prompt = sess.prompt
    mode = sess.mode
    _reset(sess)

    await msg.reply_text(
        f"Running {mode}: {len(photos)} in → "
        f"{'1' if mode == 'combine' else len(photos)} out. GPU may cold-start…",
        reply_markup=MAIN_KEYBOARD,
    )

    try:
        if mode == "combine":
            # v1: use first image as identity ref; prompt can mention the others later
            out = await generate_one(image_bytes=photos[0], prompt=prompt)
            await msg.reply_photo(photo=BytesIO(out), caption="Combine result")
            return

        outputs: list[bytes] = []
        for i, img in enumerate(photos, 1):
            await msg.reply_text(f"Generating {i}/{len(photos)}…")
            outputs.append(await generate_one(image_bytes=img, prompt=prompt))

        if len(outputs) == 1:
            await msg.reply_photo(photo=BytesIO(outputs[0]))
        else:
            media = [
                InputMediaPhoto(media=BytesIO(b), caption=prompt if i == 0 else None)
                for i, b in enumerate(outputs)
            ]
            await msg.reply_media_group(media=media)
    except RunPodError as e:
        log.exception("RunPod failed")
        await msg.reply_text(f"Generation failed: {e}")
    except Exception as e:
        log.exception("Unexpected failure")
        await msg.reply_text(f"Unexpected error: {e}")


def main() -> None:
    missing = [k for k, v in {
        "TELEGRAM_BOT_TOKEN": TOKEN,
        "ALLOWED_USER_ID": ALLOWED,
        "RUNPOD_API_KEY": os.environ.get("RUNPOD_API_KEY", ""),
        "RUNPOD_ENDPOINT_ID": os.environ.get("RUNPOD_ENDPOINT_ID", ""),
    }.items() if not v]
    if missing:
        raise SystemExit(f"Missing env: {', '.join(missing)}")

    req = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=120.0,
        write_timeout=120.0,
        pool_timeout=30.0,
    )
    app = (
        Application.builder()
        .token(TOKEN)
        .request(req)
        .get_updates_request(
            HTTPXRequest(
                connect_timeout=30.0,
                read_timeout=60.0,
                write_timeout=30.0,
            )
        )
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, on_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_handler(CallbackQueryHandler(on_callback))
    log.info("Bot starting (allowlist user %s)", ALLOWED)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
