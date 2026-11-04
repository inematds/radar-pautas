# radar-pautas

[![radar-pautas — today's 6 AI stories](guia/assets/banner-en.jpg)](https://inematds.github.io/radar-pautas/guia/en/)

**🇧🇷 [Português](README.md) · 🇺🇸 English · 🇪🇸 [Español](README.es.md)**

## What it is

radar-pautas is a script that reads about 20 artificial intelligence news sites at once (company blogs, press, Hacker News, Reddit, and the projects that gained the most stars on GitHub that week) and returns the 6 hottest topics from the past 24 hours. It is for people who create content and need to quickly decide what to cover today. It combines the same story from multiple sites, scores it, checks whether the link opens, warns you if you have already made something similar, and, if asked, suggests a headline, hook, and format in Portuguese. It requires Python 3; the GitHub CLI (`gh`) and Claude Code are optional.

## 📖 User guide

Full guide (landing + step by step): **https://inematds.github.io/radar-pautas/guia/en/**

## Use

```bash
git clone https://github.com/inematds/radar-pautas ~/projetos/radar-pautas
cd ~/projetos/radar-pautas
python3 radar.py --dry          # olhar as 6 pautas sem gravar
python3 radar.py --angulos      # gravar + manchete/gancho/formato em PT (Claude Code)
```

Open `~/projetos/output/radar-pautas/<data>/radar.html` in your browser.

| Option | Does |
|---|---|
| `--horas 48` | time window (default 24) |
| `--n 8` | number of topics (default 6) |
| `--angulos` | headline, why it matters, hook, format, and keyword, via `claude -p` (subscription) |
| `--sem-github` | exclude trending repositories |
| `--dry` | print only |

## The process, from start to finish

🧠 session with Nei · ⚙️ script/timer · 🤖 `claude -p` (subscription)

| # | Step | Command / what happens | Who |
|---|---|---|---|
| 1 | Collection | `radar.py` reads the feeds in `fontes.json` in parallel (and retries when a site asks it to wait) + `gh search repos` | ⚙️ |
| 2 | Groups and scores | the same story across multiple sites becomes one topic; score based on sources, recency, and official source | ⚙️ |
| 3 | Checks | opens each topic link (only 200 responses are included) and searches for similar content in `PRODUCOES-VIDEO.md` | ⚙️ |
| 4 | Angle | `--angulos`: headline in Portuguese, hook, format (r7ex/explicavideo/carrossel), and keyword | 🤖 |
| 5 | Selection | Nei chooses which topics become videos or carousels | 🧠 |
| 6 | Daily run (optional) | `systemd/radar-pautas.timer` at 07:30 — **disabled by default**; enable only with approval | ⚙️ |

## Sources

`fontes.json`: OpenAI, Google AI, Google DeepMind, Hugging Face, NVIDIA, Mistral, GitHub Blog, The Verge, TechCrunch, Ars Technica, Wired, The Decoder, MarkTechPost, MIT News, Simon Willison, Hacker News (150+ points), r/LocalLLaMA, Tecmundo, Canaltech, and Olhar Digital (the latter three filtered by AI-related keywords). Tested on 01/11/2026.

## Limitations

- Feeds occasionally go down (one per run is normal); the results show which ones were unavailable.
- Grouping is based on title keywords: sometimes it groups too little (two very different headlines about the same event).
- Angle suggestions use only the title and summary: always verify numbers and facts against the opened source.

License: MIT.