"""Set and print the Saturday, 21 November 2026 edition using offline materials."""

from __future__ import annotations

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
    worn: bool

    def positions(self, alphabet):
        widths = [round(alphabet[letter].step * self.sx) for letter in self.copy]
        line_length = sum(widths)
        fraction = {"left": 0, "right": 1, "center": 0.5}[self.alignment]
        cursor = round((self.anchor - fraction * (line_length / DOTS)) * DOTS)
        for letter, width in zip(self.copy, widths):
            yield cursor, letter
            cursor += width


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
            color = 8 + pattern % 5 if line.worn else 5 + pattern % 3
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

    def put(self, words, face, x, y, size=1, fit=1, align="left", worn=False):
        self.set_line(Line(face, words, x, round(y * DOTS), align, size * fit, size, worn))

    def measure(self, text, face, size=1):
        alphabet = self.type.faces[face]
        return sum(round(alphabet[c].step * size) for c in text) / DOTS

    def paragraph(self, text, x, y, measure, step, max_lines):
        words = text.split()
        composed = []
        current = []
        for word in words:
            attempt = " ".join([*current, word])
            if current and self.measure(attempt, "news14") > measure:
                composed.append(" ".join(current))
                current = []
            current.append(word)
        if current:
            composed.append(" ".join(current))
        if len(composed) > max_lines:
            raise ValueError(f"Overflow in lead at column {x}")
        for i, copy in enumerate(composed):
            self.put(copy, "news14", x, y + step * i)

    def leads(self, stories):
        # Anchor points follow the three engravings on the unlettered plate.
        columns = (
            (32, 176, 249, 283, 423, 47, 17, "display55", .94, .74, 2),
            (488, 345, 398, 457, 226, 29, 15, "display27", 1.01, .84, 4),
            (752, 345, 398, 458, 237, 29, 15, "display27", 1.01, .86, 4),
        )
        for story, spec in zip(stories, columns, strict=True):
            x, head_y, body_y, credit_y, width, head_step, step, face, size, fit, limit = spec
            for row, copy in enumerate(story["headline"]):
                self.put(copy, face, x, head_y + row * head_step, size, fit, worn=True)
            self.paragraph(story["story"], x, body_y, width, step, limit)
            self.put(story["credit"], "news12", x, credit_y)
        self.put("OIL TRAFFIC  /  STRAIT OF HORMUZ", "news12", 36, 456)
        self.put("THE CRITICAL LINE", "news12", 875, 140, align="center")
        self.put("Real part of a zeta zero", "news12", 875, 312, align="center")
        for x, tick in zip((802, 871, 940), ("0", "1/2", "1")):
            self.put(tick, "news12", x, 293, align="center")
        for zero in (14.13, 21.02, 25.01):
            self.put(str(zero), "news12", 882, 281 - zero * 4.5)

    def news_columns(self, stories):
        self.put("The News Desk", "display22", 32, 489, .78)
        slots = ((32, 527), (32, 630), (349, 521), (349, 591),
                 (349, 656), (668, 521), (668, 579), (668, 659))
        for (x, y), story in zip(slots, stories, strict=True):
            wide_type = x == 32
            face = "display27" if wide_type else "display22"
            leading = 29 if wide_type else 23
            for i, title in enumerate(story["heading"]):
                self.put(title, face, x, y + i * leading, 1.04)
            baseline = y + (len(story["heading"]) - 1) * leading + 21
            for i, detail in enumerate(story["lines"]):
                self.put(detail, "news14", x, baseline + i * 18, 1.15)

    def market_strip(self, quotes):
        label = "Markets  /  Friday closes    ·    Crypto  /  Saturday noon UTC"
        self.put(label, "display22", 32, 724, .64)
        cursor = 32
        for i, item in enumerate(quotes):
            if i > 0:
                self.put("·", "display22", cursor + 7, 746)
                cursor += 22
            self.put(item["asset"], "news14", cursor, 747, 1.12)
            cursor += self.measure(item["asset"], "news14", 1.12) + 7
            self.put(item["quote"], "display27", cursor, 748, 1.14)
            cursor += self.measure(item["quote"], "display27", 1.14)
        if cursor > PAGE - 32:
            raise ValueError("Quotes exceed the width of the edition")

    def short_reports(self, reports):
        self.put("In Brief", "display22", PAGE / 2, 771, .82, align="center")
        for i, item in enumerate(reports):
            x = 32 if i < 5 else 530
            y = 796 + (i % 5) * 40
            self.put(item["title"], "display22", x, y, .96)
            self.put(item["detail"], "news14", x, y + 18, 1.22)

    def compose(self):
        articles = json.loads((MATERIALS.parent / "edition.json").read_bytes())
        self.put(articles["paper"], "display22", 32, 19, .66)
        self.put(articles["folio"], "display22", PAGE - 32, 19, .66, align="right")
        self.put(articles["edition"], "display55", PAGE / 2, 89, 1.32, .88, "center", True)
        self.leads(articles["leads"])
        self.news_columns(articles["desk"])
        self.market_strip(articles["markets"])
        self.short_reports(articles["briefs"])
        self.put("DATE CHECK", "display22", 32, 999, .73)
        self.put(articles["date_note"], "news12", 147, 999, 1.05)
        self.put(articles["sources"], "news12", 32, 1015, fit=.91)


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
