# llm_structured_scraper

A two-stage pipeline that uses a headless browser to render JavaScript-heavy webpages, converts the result to token-efficient Markdown, and delegates semantic URL extraction to an LLM — producing strictly schema-validated, structured output via [Pydantic](https://docs.pydantic.dev/) and [Instructor](https://python.useinstructor.com/).

Traditional scrapers break when DOM structure changes. This tool replaces brittle CSS selectors and regex with an LLM that understands *meaning*, making it robust to layout changes, obfuscated markup, and dynamically injected content.

---

## 📑 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [How It Works](#-how-it-works)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#%EF%B8%8F-configuration)
- [Usage](#-usage)
- [LLM Backend Selection](#-llm-backend-selection)
- [Token Budget & Chunking](#-token-budget--chunking)
- [Technologies](#-technologies)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

---

## ✨ Features

- 🌐 **Headless Browser Scraping** — Playwright renders JavaScript-heavy pages before extraction, ensuring content injected via XHR or client-side frameworks is captured.
- 📝 **HTML → Markdown Conversion** — Non-semantic elements (`<script>`, `<style>`, `<nav>`, `<footer>`, `<img>`, `<svg>`) are stripped before conversion, shrinking token usage while preserving structural meaning (headings, lists, links).
- 🧩 **Token-Aware Chunking** — Long pages are split into chunks respecting a configurable token ceiling. Splitting occurs at line boundaries to avoid breaking mid-sentence, preventing context window overflows.
- 🤖 **LLM-Powered Extraction** — An LLM semantically identifies and extracts URLs from unstructured prose, far more resilient than DOM traversal or pattern matching.
- 🔒 **Schema-Validated Output** — The [Instructor](https://python.useinstructor.com/) library enforces structured JSON output conforming to a Pydantic `LinkCollection` model, guaranteeing every returned value is a valid `HttpUrl` — no post-processing required.
- ☁️ **Cloud & Local Inference** — Switch between Groq (cloud, fast) and Ollama (local, private) via a single flag. Useful when working with sensitive page content or in air-gapped environments.
- 📊 **Token Usage Reporting** — Prompt, completion, and total token counts are printed per chunk for cost visibility and debugging.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              Entry Point                                │
│                           scripts/main.py                               │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │  calls parser.main(is_local=True/False)
          ┌──────────────────────┴──────────────────────┐
          │                                             │
          ▼                                             ▼
  ┌───────────────┐                           ┌─────────────────────┐
  │  scraper.py   │                           │     parser.py       │
  │               │                           │                     │
  │  Playwright   │   data/webpage.md         │  chunk_text()       │
  │  (Chromium)   │ ─────────────────────────▶│  → LLM (Groq /      │
  │  + markdownify│                           │    Ollama)          │
  └───────────────┘                           │  → Instructor       │
          ▲                                   │  → Pydantic         │
          │                                   └──────────┬──────────┘
    SITE_URL (.env)                                       │
                                                          ▼
                                                  data/urls.txt
                                               (one URL per line)
```

**Data flow:**

1. `scraper.py` launches a headless Chromium browser, navigates to `SITE_URL`, waits for network idle, then strips and converts the HTML to Markdown, writing `data/webpage.md`.
2. `parser.py` reads `data/webpage.md`, splits it into token-bounded chunks, and sends each chunk to the configured LLM. Responses are coerced into `LinkCollection` objects by Instructor and aggregated.
3. All extracted URLs are written to `data/urls.txt`, one per line.

---

## 🔍 How It Works

### Stage 1 — Scraping (`scraper.py`)

Playwright launches a headless Chromium instance and navigates to the target URL using `wait_until="networkidle"` — a deliberate choice over `"domcontentloaded"` because many modern pages inject their primary content (links, tables, download buttons) via deferred JavaScript after initial DOM load.

The raw HTML is passed to `markdownify` with an explicit strip list that removes non-textual elements. This has two compounding benefits:
- Reduces token count significantly (tested pages drop from 50k+ to <10k tokens).
- Removes noise (navigation menus, cookie banners, ad scripts) that would otherwise dilute the LLM's focus.

### Stage 2 — Parsing (`parser.py`)

The Markdown content is split into chunks using `chunk_text()`, which iterates line-by-line and flushes a chunk when the running token count would exceed the ceiling. Splitting at line boundaries (rather than character boundaries) avoids cutting mid-sentence or mid-URL, which would cause extraction failures.

Each chunk is sent to the LLM with:
- A strict system prompt that prohibits explanatory prose and mandates JSON-only output.
- `temperature=0.0` to maximize determinism and eliminate hallucinated URLs.
- `response_model=LinkCollection` passed to Instructor, which wraps the underlying API client and automatically retries if the response fails Pydantic validation (configurable via `max_retries`).

Results across all chunks are accumulated into a single `LinkCollection` and written to `data/urls.txt`.

---

## 📁 Project Structure

```
llm-data-extractor/
├── scripts/
│   ├── main.py          # Unified entry point — runs the full pipeline
│   ├── scraper.py       # Stage 1: Headless browser scraping & HTML→Markdown
│   └── parser.py        # Stage 2: LLM extraction with structured output
├── data/                # Runtime-generated output (gitignored)
│   ├── webpage.md       # Intermediate Markdown from scraper
│   └── urls.txt         # Final extracted URLs, one per line
├── example.env          # Environment variable template
├── requirements.txt     # Pinned Python dependencies
├── .gitignore
└── README.md
```

> `data/` is gitignored. It is created automatically at runtime.

---

## 📋 Prerequisites

- **Python** 3.10 or higher
- **Playwright Chromium** browser binaries (installed separately — see below)
- One of:
  - A **Groq API key** for cloud inference
  - **[Ollama](https://ollama.com/)** running locally with your chosen model pulled

---

## 🚀 Installation

**1. Clone the repository:**

```bash
git clone https://github.com/sadmanhsakib/llm_structured_scraper.git
cd llm_structured_scraper
```

**2. Create and activate a virtual environment:**

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

**3. Install Python dependencies:**

```bash
pip install -r requirements.txt
```

**4. Install Playwright browser binaries:**

```bash
playwright install chromium
```

---

## ⚙️ Configuration

Copy the environment template and populate it:

```bash
# Windows
copy example.env .env

# macOS / Linux
cp example.env .env
```

| Variable | Description | Required For |
|---|---|---|
| `SITE_URL` | Full URL of the page to scrape | `scraper.py` |
| `LOCAL_MODEL_NAME` | Ollama model identifier (e.g. `deepseek-r1:14b`) | Local inference |
| `REMOTE_MODEL_NAME` | Groq model identifier (e.g. `llama-3.3-70b-versatile`) | Cloud inference |
| `API_KEY` | Your Groq API key | Cloud inference |

> **Note:** `LOCAL_MODEL_NAME` and `REMOTE_MODEL_NAME` are distinct variables — you can configure both and switch between them without editing the `.env` file.

---

## 📖 Usage

The pipeline runs in two sequential stages. Each stage can be run independently if you already have the intermediate output from a previous run.

### Full Pipeline (recommended)

```bash
cd scripts
python main.py
```

By default, `main.py` runs the parser in **local mode** (`is_local=True`). To switch to cloud mode, edit line 7 of `main.py`:

```python
# Local (Ollama)
parser.main(is_local=True)

# Cloud (Groq)
parser.main(is_local=False)
```

### Run Stages Individually

**Stage 1 — Scrape and convert to Markdown:**
```bash
cd scripts
python scraper.py
```
Output: `data/webpage.md`

**Stage 2 — Extract URLs from Markdown:**
```bash
cd scripts

# Cloud inference (Groq)
python parser.py

# Local inference (Ollama) — edit is_local flag in __main__ block
python parser.py
```
Output: `data/urls.txt`

---

## 🤖 LLM Backend Selection

| | Groq (Cloud) | Ollama (Local) |
|---|---|---|
| **Speed** | Very fast (LPU inference) | Depends on hardware |
| **Privacy** | Data sent to Groq API | Fully local, no external calls |
| **Cost** | Token-based API pricing | Free (compute only) |
| **Setup** | API key required | Ollama + model pull required |
| **Chunk size** | 6,000 tokens | 1,500 tokens (conservative default) |
| **Internet required** | Yes | No |

The local chunk ceiling is deliberately conservative at 1,500 tokens to remain compatible with mid-range models (7B–14B parameters) that have tighter effective context windows despite higher advertised limits.

---

## 🧩 Token Budget & Chunking

Token counting uses `tiktoken` with the `cl100k_base` encoding (GPT-4/Groq-compatible). This is an approximation for non-OpenAI models, but it is accurate enough to prevent context overflows without requiring a per-model tokenizer download.

```
Local mode:  max_tokens = 1,500  per chunk
Remote mode: max_tokens = 6,000  per chunk
```

Each chunk's token count is printed to the console. If you see a single chunk consuming the full budget, your page is content-dense — consider tightening the strip list in `scraper.py` or reducing `max_tokens` further.

---

## 🛠️ Technologies

| Library | Version | Purpose |
|---|---|---|
| [Playwright](https://playwright.dev/python/) | 1.58 | Headless browser automation |
| [markdownify](https://github.com/matthewwithanm/python-markdownify) | 1.2 | HTML → Markdown conversion |
| [Instructor](https://python.useinstructor.com/) | 1.14 | Structured LLM output enforcement |
| [Pydantic](https://docs.pydantic.dev/) | 2.12 | Schema definition & URL validation |
| [Groq](https://groq.com/) | 1.1 | Cloud LLM inference (fast) |
| [Ollama](https://ollama.com/) | 0.6 | Local LLM inference server |
| [tiktoken](https://github.com/openai/tiktoken) | 0.12 | Token estimation for chunking |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | 1.2 | Environment variable loading |

---

## 🔧 Troubleshooting

**`❌ Input file not found: data/webpage.md`**  
Run `scraper.py` first to generate the intermediate file, or ensure you are running scripts from the `scripts/` directory where relative paths resolve correctly.

**`⚠️ Model name not configured.`**  
Check your `.env` file. For local mode, `LOCAL_MODEL_NAME` must be set. For cloud mode, both `REMOTE_MODEL_NAME` and `API_KEY` must be set.

**Playwright browser not found**  
Run `playwright install chromium` in your activated virtual environment.

**LLM returns empty `links` list**  
The page likely contains no URLs matching the extraction prompt, or the chunk is too small to contain complete link contexts. Try increasing `max_tokens` in `parser.py` or inspecting `data/webpage.md` manually to confirm links are present.

**Ollama connection refused**  
Ensure Ollama is running (`ollama serve`) and the model specified in `LOCAL_MODEL_NAME` has been pulled (`ollama pull <model>`).

**Timeout on `page.goto()`**  
Some pages do not reach a `networkidle` state (e.g., pages with long-polling or WebSocket connections). You can change the `wait_until` parameter in `scraper.py` to `"load"` or `"domcontentloaded"` as a fallback.

---

## 📄 License

This project is provided as-is for educational and personal use. No warranty is expressed or implied.