from telegram import ReplyKeyboardMarkup

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
