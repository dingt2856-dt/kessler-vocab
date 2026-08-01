#!/usr/bin/env python3
"""Generate simple, legible PWA icons without external assets."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "app" / "icons"


def font(size: int):
    candidates = [
        Path("C:/Windows/Fonts/georgiab.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def make_icon(size: int) -> None:
    image = Image.new("RGB", (size, size), "#062b52")
    draw = ImageDraw.Draw(image)
    for y in range(size):
        ratio = y / max(1, size - 1)
        color = (
            int(6 + (11 - 6) * ratio),
            int(43 + (130 - 43) * ratio),
            int(82 + (126 - 82) * ratio),
        )
        draw.line((0, y, size, y), fill=color)
    margin = int(size * 0.12)
    draw.rounded_rectangle(
        (margin, margin, size - margin, size - margin),
        radius=int(size * 0.18),
        outline=(117, 224, 213),
        width=max(3, int(size * 0.018)),
    )
    letter_font = font(int(size * 0.48))
    text = "K"
    box = draw.textbbox((0, 0), text, font=letter_font)
    x = (size - (box[2] - box[0])) / 2
    y = (size - (box[3] - box[1])) / 2 - box[1] - size * 0.025
    draw.text((x, y), text, font=letter_font, fill="white")
    dot = int(size * 0.026)
    baseline = int(size * 0.79)
    for idx, height in enumerate((1, 2, 4, 2, 1)):
        cx = int(size * (0.38 + idx * 0.06))
        draw.rounded_rectangle(
            (cx - dot, baseline - dot * height, cx + dot, baseline + dot * height),
            radius=dot,
            fill=(117, 224, 213),
        )
    image.save(OUT / f"icon-{size}.png", optimize=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    make_icon(192)
    make_icon(512)


if __name__ == "__main__":
    main()
