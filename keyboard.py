from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

from presets import PRESETS

BTN_SINGLE = "🖼 Single Image"
BTN_BATCH = "📋 Batch Image"
BTN_COMBINE = "🔀 Combine Images"
BTN_CANCEL = "❌ Cancel"

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        [BTN_SINGLE, BTN_BATCH],
        [BTN_COMBINE, BTN_CANCEL],
    ],
    resize_keyboard=True,
)


def preset_keyboard() -> InlineKeyboardMarkup:
    """Inline presets + Custom prompt (Jork-like)."""
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton("✨ Custom prompt", callback_data="p:custom")]
    ]
    row: list[InlineKeyboardButton] = []
    for key, spec in PRESETS.items():
        if key == "custom":
            continue
        row.append(InlineKeyboardButton(spec["title"], callback_data=f"p:{key}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)
