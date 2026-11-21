"""Render the November 21 front page from its copy and unlettered print layers."""

from functools import lru_cache
import json
import os
from pathlib import Path
import struct
import zlib


ROOT = Path(__file__).resolve().parent
MATERIAL = ROOT / "materials"
SIDE = 1024
SCALE = 3
WIDTH = SIDE * SCALE


def unpack(name, size=None):
    data = zlib.decompress((MATERIAL / name).read_bytes())
    if size is not None and len(data) != size:
        raise ValueError(f"Wrong layer dimensions: {name}")
    return data


def ink_seed(position, index, baseline, character):
    coordinate = 20261121 + (baseline + ord(character)) * 1031 + position + index * 29
    value = (2654435761 * coordinate) & 0xffffffff
    value = ((value ^ (value >> 15)) * 2246822519) & 0xffffffff
    return value ^ (value >> 13)


class Typesetter:
    def __init__(self):
        self.plate = bytearray(unpack("engravings-and-rules.z", WIDTH * WIDTH))
        self.fonts = json.loads(unpack("glyphs.json.z"))

    @lru_cache(maxsize=2048)
    def stencil(self, face, character, horizontal, vertical):
        _, bearing, top, w, h, packed = self.fonts[face][character]
        bits = bytes.fromhex(packed)
        stride = (w + 7) // 8
        if len(bits) != h * stride:
            raise ValueError(f"Bad stencil for {face}")
        # Cache dot offsets relative to the baseline, in printing order.
        points = []
        for j in range(round(h * vertical)):
            row = stride * min(h - 1, int(j / vertical))
            for i in range(round(w * horizontal)):
                column = min(w - 1, int(i / horizontal))
                if bits[row + column // 8] & (128 >> (column % 8)):
                    points.append((round(bearing * horizontal) + i, round(top * vertical) + j))
        return points

    def advances(self, text, face, horizontal):
        alphabet = self.fonts[face]
        return [round(alphabet[c][0] * horizontal) for c in text]

    def length(self, text, face, size=1):
        return sum(self.advances(text, face, size)) / SCALE

    def line(self, text, face, x, y, size=1, stretch=1, align=0, distressed=False):
        horizontal = size * stretch
        steps = self.advances(text, face, horizontal)
        cursor = round((x - align * (sum(steps) / SCALE)) * SCALE)
        baseline = round(y * SCALE)
        for index, (character, step) in enumerate(zip(text, steps)):
            seed = ink_seed(cursor, index, baseline, character)
            color = 8 + seed % 5 if distressed else 5 + seed % 3
            for dx, dy in self.stencil(face, character, horizontal, size):
                col, row = cursor + dx, baseline + dy
                if 0 <= col < WIDTH and 0 <= row < WIDTH:
                    self.plate[row * WIDTH + col] = color
                    if distressed and (seed + col // 4 + row // 5) % 13 < 8:
                        smear_x = col + (2 if seed & 8 else -2)
                        smear_y = row + 2 + (seed & 1)
                        if 0 <= smear_x < WIDTH and smear_y < WIDTH:
                            spot = smear_y * WIDTH + smear_x
                            if not self.plate[spot]:
                                self.plate[spot] = 13
            cursor += step

    def wrap(self, text, width):
        current = ""
        for word in text.split():
            extended = f"{current} {word}" if current else word
            if current and self.length(extended, "news14") > width:
                yield current
                current = word
            else:
                current = extended
        if current:
            yield current


def lead_section(page, leads):
    specs = [
        (32, 176, 47, "display55", .94, .74, 249, 423, 17, 283),
        (488, 345, 29, "display27", 1.01, .84, 398, 226, 15, 457),
        (752, 345, 29, "display27", 1.01, .86, 398, 237, 15, 458),
    ]
    for lead, spec in zip(leads, specs, strict=True):
        x, top, gap, face, size, stretch, first, width, leading, bottom = spec
        for i, title in enumerate(lead["title"]):
            page.line(title, face, x, top + i * gap, size, stretch, distressed=True)
        for i, body in enumerate(page.wrap(lead["body"], width)):
            y = first + i * leading
            if y >= bottom:
                raise ValueError("Lead exceeds its column")
            page.line(body, "news14", x, y)
        page.line(lead["byline"], "news12", x, bottom)
    page.line("OIL TRAFFIC  /  STRAIT OF HORMUZ", "news12", 36, 456)
    page.line("THE CRITICAL LINE", "news12", 875, 140, align=.5)
    page.line("Real part of a zeta zero", "news12", 875, 312, align=.5)
    for i, label in enumerate(("0", "1/2", "1")):
        page.line(label, "news12", 802 + 69 * i, 293, align=.5)
    for value in (14.13, 21.02, 25.01):
        page.line(str(value), "news12", 882, 281 - 4.5 * value)


def news_desk(page, stories):
    page.line("The News Desk", "display22", 32, 489, .78)
    positions = [(32, 527), (32, 630), (349, 521), (349, 591),
                 (349, 656), (668, 521), (668, 579), (668, 659)]
    for (titles, body), (x, y) in zip(stories, positions, strict=True):
        face, gap = ("display27", 29) if x == 32 else ("display22", 23)
        for title in titles:
            page.line(title, face, x, y, 1.04)
            y += gap
        y += 21 - gap
        for line in body:
            page.line(line, "news14", x, y, 1.15)
            y += 18


def market_line(page, quotes):
    page.line("Markets  /  Friday closes    ·    Crypto  /  Saturday noon UTC",
              "display22", 32, 724, .64)
    x = 32
    for index, (asset, price) in enumerate(quotes):
        if index:
            page.line("·", "display22", x + 7, 746)
            x += 22
        page.line(asset, "news14", x, 747, 1.12)
        x += 7 + page.length(asset, "news14", 1.12)
        page.line(price, "display27", x, 748, 1.14)
        x += page.length(price, "display27", 1.14)
    if x > SIDE - 32:
        raise ValueError("Market line extends into margin")


def lay_out(copy):
    if [len(copy[k]) for k in ("leads", "desk", "briefs", "quotes")] != [3, 8, 10, 4]:
        raise ValueError("Unexpected number of stories or quotes")
    page = Typesetter()
    paper, date, folio = copy["masthead"]
    page.line(paper, "display22", 32, 19, .66)
    page.line(folio, "display22", 992, 19, .66, align=1)
    page.line(date, "display55", 512, 89, 1.32, .88, .5, True)
    lead_section(page, copy["leads"])
    news_desk(page, copy["desk"])
    market_line(page, copy["quotes"])
    page.line("In Brief", "display22", 512, 771, .82, align=.5)
    for index, (headline, body) in enumerate(copy["briefs"]):
        column, row = divmod(index, 5)
        x, y = 32 + column * 498, 796 + row * 40
        page.line(headline, "display22", x, y, .96)
        page.line(body, "news14", x, y + 18, 1.22)
    note, sources = copy["footer"]
    page.line("DATE CHECK", "display22", 32, 999, .73)
    page.line(note, "news12", 147, 999, 1.05)
    page.line(sources, "news12", 32, 1015, stretch=.91)
    return page.plate


def scanlines(plate):
    colors = json.loads((MATERIAL / "swatches.json").read_bytes())
    stock = list(map(bytes, colors["stock"]))
    ink = colors["ink"]
    texture = unpack("paper-stock.z", SIDE * SIDE * 3)
    abrasion = unpack("press-wear.z", SIDE * SIDE)
    for row in range(SIDE):
        rgb = bytearray()
        strips = [plate[(row * SCALE + j) * WIDTH:(row * SCALE + j + 1) * WIDTH]
                  for j in range(SCALE)]
        for col in range(SIDE):
            pixel = row * SIDE + col
            tone, bias, damage = texture[pixel * 3:pixel * 3 + 3]
            ground = stock[tone]
            x = SCALE * col
            sample = strips[0][x:x+3] + strips[1][x:x+3] + strips[2][x:x+3]
            marks = [ink[k] for k in sample if k]
            if marks:
                loss = max(damage, abrasion[pixel]) if max(sample) >= 8 else 0
                for base, channels in zip(ground, zip(*marks)):
                    total = sum(channels) + len(marks) * (bias - 128)
                    channel = (total + (9 - len(marks)) * base + 4) // 9
                    rgb.append(channel + ((base - channel) * loss + 50) // 100)
            else:
                rgb.extend(ground)
        yield rgb


def chunk(kind, body):
    length = struct.pack(">I", len(body))
    checksum = struct.pack(">I", zlib.crc32(body, zlib.crc32(kind)))
    return length + kind + body + checksum


def render():
    plate = lay_out(json.loads((ROOT / "edition.json").read_bytes()))
    stream = zlib.compressobj(9)
    data = bytearray()
    for row in scanlines(plate):
        # PNG Sub filtering uses the same color channel in the preceding pixel.
        filtered = bytearray([1]) + row[:3]
        filtered.extend((b - a) % 256 for a, b in zip(row, row[3:]))
        data.extend(stream.compress(filtered))
    data.extend(stream.flush())
    info = struct.pack(">IIBBBBB", SIDE, SIDE, 8, 2, 0, 0, 0)
    target = Path(os.getenv("MAKEFUN_OUTPUT_DIR", "/output"))
    target.mkdir(parents=True, exist_ok=True)
    (target / "entry.png").write_bytes(
        b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", info) + chunk(b"IDAT", data) + chunk(b"IEND", b"")
    )


if __name__ == "__main__":
    render()
