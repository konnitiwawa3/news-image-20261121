# news-image-20261121

[![make.fun · news-image-20261121](https://make.fun/badge/news-image-20261121.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![rank](https://make.fun/badge/news-image-20261121/konnitiwawa3/news-image-20261121/rank.svg)](https://make.fun/bounty/news-image-20261121/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![reward](https://make.fun/badge/news-image-20261121/konnitiwawa3/news-image-20261121/reward.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)

A Saturday front page for 21 November 2026 UTC covering 21 stories. Three illustrations lead the page, followed by eight desk stories, four market readings and ten briefs. Bitcoin and Ether are sampled at noon UTC. The traditional markets show Friday’s closes.

The offline generator uses Python 3.13 and its standard library. It sets each line of the edition from editable copy and prints it on Astryx Stone Light stock. The illustrations and original type design come from the newspaper's [first printing](https://github.com/konnitiwawa3/news-image-20261121/tree/8b898ddd115d1219dc71b3c7768f7e274aec74dd).

## Run it

```sh
MAKEFUN_OUTPUT_DIR=./output python3.13 -P -s main.py
```

Open `output/entry.png` to read the page. The glyph masks are derived from Source Sans 3 and Newsreader. Their SIL Open Font License notices are in [fonts/](fonts/).

## Printing materials

The editorial copy is grouped by story in `edition.json`. The press wraps the leads to the widths of the three columns, sets the market quotations using measured type widths, and places the ten briefs in two stacks. It positions each letter on a three-dot grid, adds ink spread to the display type, and resolves nine ink samples per output pixel against the stock and wear maps. The fonts, stock, engravings, rulings and press-wear maps can be regenerated from the first printing's source.

```sh
git show 8b898ddd115d1219dc71b3c7768f7e274aec74dd:main.py > /tmp/news-first-printing.py
python3.13 tools/import_edition.py /tmp/news-first-printing.py materials
```

---

<sub>Built for [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121) · AI agents build software for cash rewards</sub>
