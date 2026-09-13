"""FLUX Kontext lifestyle presets. Input image locks identity; prompts restyle scene."""

# Kontext already sees the face — reinforce identity so it does not drift.
_IDENTITY = (
    "same person as in the input photo, preserve exact face identity, "
    "same facial features, same ethnicity, same age, same skin tone, "
    "same gender, do not replace the face"
)

_PHOTO = (
    f"{_IDENTITY}, photorealistic photograph, natural skin texture, "
    "visible pores, realistic lighting, candid, no cartoon, no anime, "
    "no illustration, no CGI, no plastic skin"
)

PRESETS = {
    "custom": {
        "title": "Custom prompt",
        "prompt": _PHOTO,
    },
    "golden": {
        "title": "Golden hour",
        "prompt": (
            f"{_PHOTO}. Outdoor golden-hour portrait of the same adult, warm sunlight, "
            "soft rim light, shallow depth of field, casual summer clothes, "
            "city rooftop or park, Kodak portra colors"
        ),
    },
    "studio": {
        "title": "Studio",
        "prompt": (
            f"{_PHOTO}. Clean studio portrait of the same adult, softbox key light, "
            "subtle hair light, seamless grey backdrop, fashion lookbook, "
            "tailored outfit, sharp eyes"
        ),
    },
    "street": {
        "title": "Street night",
        "prompt": (
            f"{_PHOTO}. Night street photograph of the same adult, neon and tungsten "
            "mixed lighting, wet pavement reflections, cinematic, "
            "leather jacket, handheld documentary feel"
        ),
    },
    "hotel": {
        "title": "Hotel window",
        "prompt": (
            f"{_PHOTO}. The same adult in a luxury hotel room at night, city lights "
            "through the window, warm practical lamps, silk slip dress or open shirt, "
            "editorial lifestyle, intimate but classy"
        ),
    },
    "beach": {
        "title": "Beach",
        "prompt": (
            f"{_PHOTO}. The same adult on a beach at late afternoon, salty air, "
            "wind in hair, swimwear, wet skin highlights, hard sun and fill, "
            "film still, ocean bokeh"
        ),
    },
    "pool": {
        "title": "Pool night",
        "prompt": (
            f"{_PHOTO}. The same adult by a hotel pool at night, underwater lights, "
            "turquoise reflections, swimsuit, wet hair, candid, "
            "expensive vacation editorial"
        ),
    },
    "bedroom": {
        "title": "Bedroom",
        "prompt": (
            f"{_PHOTO}. The same adult in a dim bedroom, morning window light, "
            "linen sheets, oversized shirt, sleepy candid, natural, "
            "lifestyle photograph"
        ),
    },
    "rain": {
        "title": "Rain",
        "prompt": (
            f"{_PHOTO}. The same adult in heavy rain at night, soaked clothes, "
            "streetlights, droplets on skin and hair, cinematic still, "
            "moody, high contrast"
        ),
    },
    "gym": {
        "title": "Gym",
        "prompt": (
            f"{_PHOTO}. The same adult in a gym, athletic wear, sweat, "
            "overhead industrial lights, documentary sports photo, "
            "realistic muscle and skin"
        ),
    },
}
