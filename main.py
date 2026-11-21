"""Set and print the Saturday, 21 November 2026 edition using offline materials."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache
import json
from os import environ
from pathlib import Path
from struct import pack
import zlib


PAGE = 1024
DOTS = 3
PITCH = PAGE * DOTS
MATERIALS = Path(__file__).resolve().parent / "materials"


def inflate(filename, expected=None):
    blob = zlib.decompress((MATERIALS / filename).read_bytes())
    if expected is not None and len(blob) != expected:
        raise ValueError(f"Incorrect dimensions in {filename}")
    return blob


@dataclass(frozen=True)
class Sort:
    """One unscaled piece of type, with a baseline-relative bearing."""

    step: int
    bearing_x: int
    bearing_y: int
    columns: int
    rows: int
    mask: bytes

    @classmethod
    def unpack(cls, record):
        step, x, y, columns, rows, hex_mask = record
        mask = bytes.fromhex(hex_mask)
        if len(mask) != rows * ((columns + 7) // 8):
            raise ValueError("Truncated type mask")
        return cls(step, x, y, columns, rows, mask)


class Foundry:
    def __init__(self):
        records = json.loads(inflate("glyphs.json.z"))
        self.faces = {
            face: {symbol: Sort.unpack(metrics) for symbol, metrics in alphabet.items()}
            for face, alphabet in records.items()
        }

    @lru_cache(maxsize=2048)
    def cast(self, face, symbol, sx, sy):
        """Scale a mask once per letter and size, preserving integer dot placement."""
        sort = self.faces[face][symbol]
        stride = (sort.columns + 7) >> 3
        columns = [min(sort.columns - 1, int(i / sx)) for i in range(round(sort.columns * sx))]
        rows = []
        for row_index in range(round(sort.rows * sy)):
            offset = min(sort.rows - 1, int(row_index / sy)) * stride
            row = tuple(i for i, col in enumerate(columns)
                        if sort.mask[offset + (col >> 3)] & (128 >> (col & 7)))
            rows.append(row)
        return round(sort.bearing_x * sx), round(sort.bearing_y * sy), rows


@dataclass(frozen=True)
class Line:
    face: str
    copy: str
    anchor: float
    baseline: int
    alignment: str
    sx: float
    sy: float
    space: int
    worn: bool
    color: int

    @classmethod
    def from_record(cls, row):
        sy = float(row["scale"])
        return cls(face=row["face"], copy=row["copy"], anchor=float(row["anchor_x"]),
                   baseline=round(float(row["baseline"]) * DOTS), alignment=row["alignment"],
                   sx=sy * float(row["stretch"]), sy=sy,
                   space=round(DOTS * float(row["letterspace"])), worn=row["worn"] == "1",
                   color=int(row["color"]))

    def positions(self, alphabet):
        widths = [round(alphabet[letter].step * self.sx) for letter in self.copy]
        line_length = sum(widths) + max(0, len(widths) - 1) * self.space
        fraction = {"left": 0, "right": 1, "center": 0.5}[self.alignment]
        cursor = round((self.anchor - fraction * (line_length / DOTS)) * DOTS)
        for letter, width in zip(self.copy, widths):
            yield cursor, letter
            cursor += width + self.space


def impression_number(column, row):
    """Deterministic inking variation in the source edition's coordinate system."""
    mask32 = (1 << 32) - 1
    coordinate = 20261121 + 1031 * row + column
    mixed = (coordinate * 2654435761) & mask32
    folded = (mixed ^ (mixed >> 15)) * 2246822519 & mask32
    return folded ^ (folded >> 13)


class Forme:
    """The press bed, in dots. The engravings and rulings arrive without text."""

    def __init__(self, foundry):
        self.type = foundry
        self.dots = bytearray(inflate("engravings-and-rules.z", PITCH ** 2))

    def set_line(self, line):
        alphabet = self.type.faces[line.face]
        for index, (cursor, letter) in enumerate(line.positions(alphabet)):
            pattern = impression_number(cursor + 29 * index, line.baseline + ord(letter))
            color = line.color
            if color == 1:
                if line.worn:
                    color = 8 + pattern % 5
                else:
                    color = 5 + pattern % 3
            dx, dy, rows = self.type.cast(line.face, letter, line.sx, line.sy)
            left = cursor + dx
            for offset, filled in enumerate(rows):
                y = line.baseline + dy + offset
                if not 0 <= y < PITCH:
                    continue
                start = y * PITCH
                for relative in filled:
                    x = left + relative
                    if 0 <= x < PITCH:
                        self.dots[start + x] = color
                        if line.worn:
                            self.spread(x, y, pattern)

    def spread(self, x, y, pattern):
        if (pattern + x // 4 + y // 5) % 13 >= 8:
            return
        horizontal = x + (2 if pattern & 8 else -2)
        vertical = y + 2 + (pattern & 1)
        if 0 <= horizontal < PITCH and vertical < PITCH:
            at = vertical * PITCH + horizontal
            if self.dots[at] == 0:
                self.dots[at] = 13

    def compose(self):
        with (MATERIALS / "composition.tsv").open(encoding="utf8", newline="") as table:
            for record in csv.DictReader(table, dialect="excel-tab"):
                self.set_line(Line.from_record(record))


class Press:
    def __init__(self):
        colors = json.loads((MATERIALS / "swatches.json").read_bytes())
        self.stock = list(map(bytes, colors["stock"]))
        self.ink = colors["ink"]
        self.texture = inflate("paper-stock.z", PAGE * PAGE * 3)
        self.scratch = inflate("press-wear.z", PAGE * PAGE)

    def develop(self, dots, paper, shift, loss):
        deposited = [index for index in dots if index]
        if not deposited:
            return paper
        covered = len(deposited)
        tint = shift * covered
        channels = []
        for channel, ground in enumerate(paper):
            total = sum(self.ink[index][channel] for index in deposited)
            total += ground * (9 - covered)
            level = (total + tint + 4) // 9
            if loss and max(deposited) >= 8:
                level += ((ground - level) * loss + 50) // 100
            channels.append(level)
        return bytes(channels)

    def rows(self, forme):
        for y in range(PAGE):
            start = y * DOTS * PITCH
            bands = [forme.dots[start + i * PITCH:start + (i + 1) * PITCH] for i in range(DOTS)]
            line = bytearray()
            for x in range(PAGE):
                pixel = y * PAGE + x
                sample = DOTS * x
                dots = b"".join(band[sample:sample + DOTS] for band in bands)
                shade, signed, wear = self.texture[3 * pixel:3 * pixel + 3]
                paper = self.stock[shade]
                loss = max(wear, self.scratch[pixel])
                line.extend(self.develop(dots, paper, signed - 128, loss))
            yield line


def png_block(tag, payload):
    typed = tag + payload
    return pack(">I", len(payload)) + typed + pack(">I", zlib.crc32(typed))


def encode_image(rows):
    """Feed complete RGB scanlines to a single zlib stream as they are printed."""
    compressor = zlib.compressobj(level=9)
    compressed = bytearray()
    count = 0
    for rgb in rows:
        if len(rgb) != PAGE * 3 or count >= PAGE:
            raise ValueError("Unexpected scanline dimensions")
        filtered = bytearray([1])
        filtered.extend(rgb[:3])
        filtered.extend((current - previous) & 255
                        for previous, current in zip(rgb, rgb[3:]))
        compressed.extend(compressor.compress(filtered))
        count += 1
    if count != PAGE:
        raise ValueError(f"Expected {PAGE} rows of print, received {count}")
    compressed.extend(compressor.flush())
    dimensions = pack(">2I5B", PAGE, PAGE, 8, 2, 0, 0, 0)
    return (bytes.fromhex("89504e470d0a1a0a") + png_block(b"IHDR", dimensions)
            + png_block(b"IDAT", compressed) + png_block(b"IEND", b""))


def print_edition():
    sheet = Forme(Foundry())
    sheet.compose()
    png = encode_image(Press().rows(sheet))
    destination = Path(environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    destination.mkdir(exist_ok=True, parents=True)
    destination.joinpath("entry.png").write_bytes(png)


if __name__ == "__main__":
    print_edition()
