# HN Screening Room

Your own HackerTube: 6,427 YouTube videos that Hacker News commenters kept recommending to each
other between 2007 and 2026, with a For you feed, categories, search, the HN comments behind each
video, likes, Watch later, history and playlists. No accounts, no backend. Everything you do is
saved in your browser.

## Run it on your computer

The page loads its data with `fetch`, and YouTube's player needs a real web address, so serve the
folder instead of double-clicking `index.html`.

- **Mac:** double-click `start.command`. The first time, macOS may block it: right-click it, choose
  Open, then Open again. It opens http://localhost:8765
- **Windows:** double-click `start.bat` (needs Python from python.org or the Microsoft Store).
- **Anything else:** run `python3 -m http.server 8765` in this folder and open http://localhost:8765

Stop the server by closing the terminal window.

## Put it on the web

It's a static site, so any static host works. The quickest: drag this folder onto
https://app.netlify.com/drop, or push it to a GitHub repo and turn on GitHub Pages.

## What's in the folder

| file | what it is |
|---|---|
| `index.html` | the whole app: markup, styles and script |
| `data/catalog.json` | the videos, with summaries, why HN likes them, categories and recommendation counts |
| `data/graph.json` | similar videos (topic embeddings) and videos recommended by the same people |
| `data/c/*.json` | 39,834 labelled HN comments, sharded by video index modulo 48 |
| `data/emb.txt` | topic embeddings used by For you (base64 of an int8 matrix, 384 per video) |

## Credits and license

Data: [HackerTube](https://hackertube.org) by Andrej Karpathy, and the
[open-index/hacker-news](https://huggingface.co/datasets/open-index/hacker-news) dataset, under the
[ODC-By 1.0](https://opendatacommons.org/licenses/by/1-0/) license. Keep this credit if you share it.
Hacker News data is provided by Y Combinator; comments belong to their authors. Video titles and
channel names belong to their creators, and videos are hosted by YouTube. Not affiliated with
YouTube, Google, Hacker News or Y Combinator.

Not included: video durations, view counts and upload dates, because YouTube's API terms don't
allow redistributing them. A free YouTube Data API key can add them (see the HackerTube data guide).
