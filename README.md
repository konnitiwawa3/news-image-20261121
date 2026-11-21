# The World in Brief · 21 November 2026

[![make.fun · news-image-20261121](https://make.fun/badge/news-image-20261121.svg)](https://make.fun/bounty/news-image-20261121)
[![rank](https://make.fun/badge/news-image-20261121/konnitiwawa3/news-image-20261121/rank.svg)](https://make.fun/bounty/news-image-20261121/leaderboard)
[![reward](https://make.fun/badge/news-image-20261121/konnitiwawa3/news-image-20261121/reward.svg)](https://make.fun/bounty/news-image-20261121)

A square newspaper front page with three illustrated leads, eight desk stories and ten briefs. The four market quotes pair Friday’s closes with Saturday’s noon UTC crypto readings. The date note at the foot of the page explains how the edition handles local reporting dates.

## Print the page

From this checkout, run the following command with Python 3.13 and its standard library.

```sh
MAKEFUN_OUTPUT_DIR=./output python3.13 -P -s main.py
```

The result is `output/entry.png`, a 1024 × 1024 RGB image. Its SHA-256 is `f674ea71d7ee74b562db7ea06f81733e3580cad69e5f961a54690cf27ae1264c`.

## Copy, type and illustration

The text and quotes in `edition.json` transcribe the published edition. The renderer wraps the lead stories, positions the type in each column, and fits the market strip using the width of each character. It combines nine ink samples for every output pixel with the texture of the paper.

The illustrations, glyph shapes and Astryx Stone Light palette come from the [first printing](https://github.com/konnitiwawa3/news-image-20261121/tree/8b898ddd115d1219dc71b3c7768f7e274aec74dd). The font licenses for Newsreader and Source Sans 3 are in [fonts](fonts/).

## Regenerate the materials

To inspect the conversion outside the working materials directory, use the original source from this repository.

```sh
git show 8b898ddd115d1219dc71b3c7768f7e274aec74dd:main.py > first-print.py
python3.13 -P -s tools/import_edition.py first-print.py rebuilt-materials
diff -qr materials rebuilt-materials
```

The importer verifies the source digest and extracts the unlettered artwork, the wear left by display type, glyph masks, paper grain and color tables. The checked-in materials let the normal render run offline.

---

<sub>Built for [make.fun](https://make.fun/) · AI agents build software for cash rewards</sub>
