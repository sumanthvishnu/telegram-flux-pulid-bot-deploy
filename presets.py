"""FLUX Kontext sensual/raunchy adult presets. Input image locks identity."""

# Kontext already sees the face — reinforce identity so it does not drift.
_IDENTITY = (
    "same person as in the input photo, preserve exact face identity, "
    "same facial features, same ethnicity, same age, same skin tone, "
    "same gender, do not replace the face"
)

_PHOTO = (
    f"{_IDENTITY}, photorealistic photograph, natural skin texture, "
    "visible pores, realistic lighting, candid adult lifestyle, "
    "no cartoon, no anime, no illustration, no CGI, no plastic skin"
)

PRESETS = {
    "custom": {
        "title": "Custom prompt",
        "prompt": _PHOTO,
    },
    "lingerie": {
        "title": "Lingerie",
        "prompt": (
            f"{_PHOTO}. The same adult in sheer lingerie, bedroom soft light, "
            "seductive pose, lace details, intimate editorial, warm tones, "
            "desire in the eyes, tasteful but sensual"
        ),
    },
    "wetshirt": {
        "title": "Wet shirt",
        "prompt": (
            f"{_PHOTO}. The same adult in a soaked white shirt clinging to skin, "
            "wet hair, droplets, bathroom or pool edge, steamy atmosphere, "
            "raunchy candid, hard light highlights on wet fabric"
        ),
    },
    "mirror": {
        "title": "Mirror selfie",
        "prompt": (
            f"{_PHOTO}. The same adult taking a mirror selfie, phone in hand, "
            "bedroom or hotel bathroom, lingerie or towel, flirtatious, "
            "phone flash mixed with warm lamps, social-media thirst trap"
        ),
    },
    "afterdark": {
        "title": "After dark",
        "prompt": (
            f"{_PHOTO}. The same adult after dark in dim neon and tungsten, "
            "undressed shoulders, intense eye contact, moody club-afterparty vibe, "
            "cinematic grain, sensual and raw"
        ),
    },
    "silksheets": {
        "title": "Silk sheets",
        "prompt": (
            f"{_PHOTO}. The same adult tangled in silk sheets, morning window light, "
            "bare skin, sleepy smile, intimate bedroom, soft shadows, "
            "raunchy lifestyle photograph"
        ),
    },
    "boudoir": {
        "title": "Boudoir",
        "prompt": (
            f"{_PHOTO}. Classic boudoir portrait of the same adult, lace and velvet, "
            "posed on a chaise, soft key light, glamorous sensual editorial, "
            "adult allure, sharp eyes"
        ),
    },
    "shower": {
        "title": "Shower steam",
        "prompt": (
            f"{_PHOTO}. The same adult in a steamy shower, water on skin, "
            "fogged glass, wet hair, intimate candid, soft backlight through steam, "
            "sensual and photoreal"
        ),
    },
    "closeup": {
        "title": "Close-up desire",
        "prompt": (
            f"{_PHOTO}. Tight close-up of the same adult's face and shoulders, "
            "parted lips, heavy-lidded eyes, soft skin sheen, intimate desire, "
            "shallow depth of field, bedroom bokeh"
        ),
    },
    "clubbath": {
        "title": "Club bathroom",
        "prompt": (
            f"{_PHOTO}. The same adult in a club bathroom stall or mirror, "
            "harsh fluorescent and phone light, smudged makeup optional, "
            "messy hair, afterparty raunchy candid, nightlife heat"
        ),
    },
}
