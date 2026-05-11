# LLM Data Extractor

A two-stage web scraping and intelligent link extraction pipeline that leverages Large Language Models (LLMs) to parse webpage content and extract structured download URLs with high accuracy.

Rather than relying on brittle CSS selectors or regex patterns, this tool converts raw HTML into clean Markdown and delegates the semantic extraction to an LLM — producing reliable, schema-validated results via [Pydantic](https://docs.pydantic.dev/) and the [Instructor](https://python.useinstructor.com/) library.

## 📑 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#%EF%B8%8F-configuration)
- [Usage](#-usage)
  - [Step 1 — Scrape a Webpage](#step-1--scrape-a-webpage)
  - [Step 2 — Extract Links (Cloud)](#step-2--extract-links-cloud)
  - [Step 2 (Alt) — Extract Links (Local/Offline)](#step-2-alt--extract-links-localoffline)
- [Project Structure](#-project-structure)
- [How It Works](#-how-it-works)
- [Technologies Used](#-technologies-used)
- [License](#-license)


## ✨ Features

- 🌐 **Headless Browser Scraping** — Uses [Playwright](https://playwright.dev/python/) to render JavaScript-heavy pages before extraction, ensuring no content is missed.
- 📝 **HTML → Markdown Conversion** — Strips away non-essential elements (scripts, styles, navigation, etc.) and converts the remaining HTML to clean Markdown for optimal LLM consumption.
- 🤖 **LLM-Powered Extraction** — Employs an LLM to semantically identify and extract download links from unstructured content — far more resilient than traditional regex or DOM-based approaches.
- 🔒 **Structured Output with Pydantic** — All extracted data is validated against strict Pydantic schemas, ensuring type-safe, well-formed results.
- ☁️ **Cloud & Offline Support** — Run extraction against a cloud-hosted LLM via [Groq](https://groq.com/) or use a locally hosted model through [Ollama](https://ollama.com/) — no internet dependency required for the offline variant.
- 📊 **Token Usage Reporting** — Displays prompt, completion, and total token counts after each extraction run for cost and performance monitoring.


## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────────┐      ┌──────────────────┐      ┌────────────┐
│  Target URL │ ───▶ │   scraper.py     │ ───▶ │  parser-*.py     │ ───▶ │  urls.txt  │
│  (webpage)  │      │  (Playwright +   │      │  (LLM via Groq   │      │ (extracted │
│             │      │   Markdownify)   │      │   or Ollama)     │      │   links)   │
└─────────────┘      └──────────────────┘      └──────────────────┘      └────────────┘
                          ▼                                                     ▼
                      data.md                                              test.py
                   (intermediate)                                     (verification)
```

## 📋 Prerequisites

- **Python** 3.10 or higher
- **Playwright browsers** installed (Chromium is used by default)
- **Groq API key** (for cloud-based extraction) _or_ **Ollama** running locally (for offline extraction)

## 🚀 Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/sadmanhsakib/llm-data-extractor.git
   cd llm-data-extractor
   ```

2. **Create and activate a virtual environment:**

   ```bash
   python -m venv .venv

   # Windows
   .venv\Scripts\activate

   # macOS / Linux
   source .venv/bin/activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers:**

   ```bash
   playwright install chromium
   ```

## ⚙️ Configuration

Create a `.env` file in the project root by copying the provided template:

```bash
cp example.env .env
```

Then populate the variables:

| Variable     | Description                                         | Required For        |
|-------------|-----------------------------------------------------|---------------------|
| `SITE_URL`  | The full URL of the webpage to scrape               | `scraper.py`        |
| `MODEL_NAME`| The LLM model identifier (e.g., `llama-3.3-70b-versatile`) | `parser-online.py`  |
| `API_KEY`   | Your Groq API key                                   | `parser-online.py`  |

> **Note:** The offline parser (`parser-offline.py`) connects to a local Ollama instance at `http://localhost:11434` and does not require any environment variables.

## 📖 Usage

The pipeline is executed in sequential steps:

### Step 1 — Scrape a Webpage

```bash
python scraper.py
```

This launches a headless Chromium browser, navigates to the configured `SITE_URL`, waits for the network to become idle, and exports the cleaned page content as **`data.md`**.

### Step 2 — Extract Links (Cloud)

```bash
python parser-online.py
```

Reads `data.md`, sends its contents to the configured Groq-hosted LLM, and writes the extracted download URLs to **`urls.txt`**. Token usage statistics are printed to the console upon completion.

### Step 2 (Alt) — Extract Links (Local/Offline)

```bash
python parser-offline.py
```

Functionally identical to the cloud variant, but routes all inference through a locally running Ollama instance (using the `deepseek-r1:32b` model by default). Ideal for environments with restricted internet access or when working with sensitive data.

## 📁 Project Structure

```
llm-data-extractor/
├── scraper.py           # Stage 1: Headless browser scraping & HTML-to-Markdown conversion
├── parser-online.py     # Stage 2: Cloud-based LLM link extraction (Groq)
├── parser-offline.py    # Stage 2: Local LLM link extraction (Ollama)
├── test.py              # Utility for verifying extracted URLs
├── data.md              # Intermediate Markdown output (generated)
├── urls.txt             # Final extracted URLs (generated)
├── requirements.txt     # Python dependencies
├── example.env          # Environment variable template
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

## 🔍 How It Works

1. **Scraping (`scraper.py`):**  
   Playwright launches a headless Chromium instance and fully renders the target page (including JavaScript-generated content). The raw HTML is then processed by [markdownify](https://github.com/matthewwithanm/python-markdownify), which strips non-essential elements (`<script>`, `<style>`, `<nav>`, `<footer>`, etc.) and converts the remainder into clean Markdown.

2. **Parsing (`parser-online.py` / `parser-offline.py`):**  
   The Markdown content is sent to an LLM as a user message, accompanied by a system prompt instructing the model to extract only download links. The [Instructor](https://python.useinstructor.com/) library wraps the LLM client to enforce structured JSON output conforming to a Pydantic `LinkCollection` schema — ensuring every extracted URL is validated as a proper `HttpUrl`.

## 🛠️ Technologies Used

| Technology                                                        | Purpose                                |
|------------------------------------------------------------------|----------------------------------------|
| [Playwright](https://playwright.dev/python/)                     | Headless browser automation            |
| [markdownify](https://github.com/matthewwithanm/python-markdownify) | HTML to Markdown conversion        |
| [Instructor](https://python.useinstructor.com/)                 | Structured LLM output enforcement      |
| [Pydantic](https://docs.pydantic.dev/)                          | Data validation and schema definition  |
| [Groq](https://groq.com/)                                       | Cloud LLM inference API                |
| [Ollama](https://ollama.com/)                                    | Local LLM inference server             |
| [tiktoken](https://github.com/openai/tiktoken)                  | Token count estimation                 |

## 📄 License

This project is provided as-is for educational and personal use.