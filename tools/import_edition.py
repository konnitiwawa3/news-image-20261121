"""Recover editable type and print materials from the 21 November source edition.

Use the main.py from the commit identified in the README as the input.
The program is executed only after its digest is checked. No finished image
is read. The resulting plate contains engravings and rules, without type.
"""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import runpy
import zlib


SOURCE_DIGEST = "fe04930fd3bd3f8185915d654dfe51da068aded51b5ac942cabd967ce9434463"
SECTIONS = (
    ("folio", "masthead"),
    ("leads", "lead_stories"),
    ("desk", "news_desk"),
    ("quotes", "markets"),
    ("briefs", "news_briefs"),
    ("credits", "footer"),
)


def compressed(directory, name, data):
    (directory / name).write_bytes(zlib.compress(data, level=9))


def separate_type(source, directory):
    plate = source["Canvas"]()
    proofs = source["Canvas"]()
    faces = set()
    def separate(x, baseline, words, face, color=1, **options):
        faces.add(face)
        if options.get("distress"):
            # Only the loss-of-ink mask is retained from these impressions.
            proofs.text(x, baseline, words, face, color, **options)

    plate.text = separate
    for _, draw in SECTIONS:
        source[draw](plate)
    compressed(directory, "engravings-and-rules.z", plate.pixels)
    compressed(directory, "press-wear.z", proofs.abrasion)
    return faces


def export_faces(source, directory, faces):
    collection = source["font_data"]()
    selected = {key: collection[key] for key in sorted(faces)}
    payload = json.dumps(selected, sort_keys=True, separators=(",", ":")).encode()
    compressed(directory, "glyphs.json.z", payload)


def export_stock(source, directory):
    # The three channels describe an unprinted sheet. They carry the paper
    # color index, the local change in ink density, and the fine surface wear.
    width = source["SIZE"]
    channels = bytearray(width * width * 3)
    grain = source["Newsprint"]().rows()
    roller = source["Random"](source["PRINT_SEED"] + 4)
    pressure = source["print_field"](roller, 11, 18)
    offset = 0
    for sheet_row, pressure_row in zip(grain, pressure, strict=True):
        for (shade, point), density in zip(sheet_row, pressure_row, strict=True):
            height = point >> 27
            channels[offset] = shade + 41
            channels[offset + 1] = 128 + (density + height - 16) // 10
            channels[offset + 2] = 3 * max(0, height + density // 3 - 24)
            offset += 3
    if offset != len(channels):
        raise ValueError("The imported paper does not cover the sheet")
    compressed(directory, "paper-stock.z", channels)
    stock = source["paper_colors"]()
    swatches = {
        "stock": [list(stock[index]) for index in sorted(stock)],
        "ink": [list(color) for color in source["PALETTE"]],
    }
    (directory / "swatches.json").write_text(json.dumps(swatches) + "\n", encoding="utf8")


def import_edition():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("directory", type=Path)
    options = parser.parse_args()
    if sha256(options.source.read_bytes()).hexdigest() != SOURCE_DIGEST:
        parser.error("The file does not match the published 21 November source")
    source = runpy.run_path(str(options.source))
    options.directory.mkdir(parents=True, exist_ok=True)
    faces = separate_type(source, options.directory)
    export_faces(source, options.directory, faces)
    export_stock(source, options.directory)


if __name__ == "__main__":
    import_edition()
