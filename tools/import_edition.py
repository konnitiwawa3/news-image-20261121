"""Extract reusable typesetting materials from the published first printing."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import zlib


FIRST_PRINT = "fe04930fd3bd3f8185915d654dfe51da068aded51b5ac942cabd967ce9434463"
DRAW_ORDER = ("masthead", "lead_stories", "news_desk", "markets", "news_briefs", "footer")


def artwork(module):
    drawing = module["Canvas"]()
    wear = module["Canvas"]()
    used = set()

    def record_type(x, y, text, style, color=1, **settings):
        used.add(style)
        if settings.get("distress"):
            wear.text(x, y, text, style, color, **settings)

    drawing.text = record_type
    for section in DRAW_ORDER:
        module[section](drawing)
    fonts = module["font_data"]()
    face_data = {name: fonts[name] for name in used}
    yield "glyphs.json.z", json.dumps(face_data, sort_keys=True, separators=(",", ":")).encode()
    yield "press-wear.z", wear.abrasion
    yield "engravings-and-rules.z", drawing.pixels


def stock_rows(module):
    pressure = module["print_field"](module["Random"](module["PRINT_SEED"] + 4), 11, 18)
    for paper, roller in zip(module["Newsprint"]().rows(), pressure, strict=True):
        row = bytearray()
        for (tone, seed), force in zip(paper, roller, strict=True):
            height = seed >> 27
            ink_bias = (height + force - 16) // 10
            wear = max(height + force // 3 - 24, 0) * 3
            row.extend((41 + tone, 128 + ink_bias, wear))
        yield row


def extract(original, output):
    if hashlib.sha256(original.read_bytes()).hexdigest() != FIRST_PRINT:
        raise ValueError("Input does not match the fixed first-print source")
    module = runpy.run_path(str(original))
    output.mkdir(exist_ok=True, parents=True)
    for name, raw in artwork(module):
        (output / name).write_bytes(zlib.compress(raw, 9))
    compressor = zlib.compressobj(9)
    encoded = bytearray()
    for row in stock_rows(module):
        encoded.extend(compressor.compress(row))
    encoded.extend(compressor.flush())
    (output / "paper-stock.z").write_bytes(encoded)
    tones = module["paper_colors"]()
    colors = {
        "stock": [list(tones[key]) for key in sorted(tones)],
        "ink": [list(rgb) for rgb in module["PALETTE"]],
    }
    (output / "swatches.json").write_text(json.dumps(colors) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    extract(args.original, args.output)
