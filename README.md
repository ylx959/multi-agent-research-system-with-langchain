# Multi-Agent Research System

A research assistant built with LangChain where four AI workers hand off to each other to turn a topic into a reviewed research report. Give it a topic like *"The impact of AI on the job market in 2026"*, and it runs a fixed four-step pipeline:

1. A **Search Agent** uses **Tavily Search** to find recent, reliable sources on the topic
2. A **Reader Agent** picks the most relevant URL and scrapes the full article text
3. A **Writer** combines the search results and scraped content into a structured report (Introduction, Key Findings, Conclusion, Sources)
4. A **Critic** reviews the report and returns a score out of 10, strengths, areas to improve and a one-line verdict

All four steps are powered by **Google Gemini**. The project ships with two entry points: a CLI (`main.py`) that researches a built-in example topic, and a Streamlit web UI (`app.py`) where you enter your own topic and download the finished report as Markdown.

## Highlights

- **Multi-agent pipeline** — four specialised roles (search, read, write, critique), each with one job, instead of a single do-everything prompt
- **LangChain 1.x tool-calling agents** — the Search and Reader agents are built with the new `create_agent` API and decide for themselves when to call their tools
- **Self-review loop** — a Critic grades every report out of 10 and lists strengths, areas to improve and a one-line verdict
- **Live web research** — Tavily Search pulls recent sources, so reports aren't limited to the model's training data
- **Resilient scraping** — `scrape_url` falls back through Trafilatura → Readability → BeautifulSoup, so most pages still return clean text
- **Cited, structured reports** — every report has an Introduction, Key Findings, Conclusion and a Sources list of the URLs used
- **Google Gemini powered** — one Gemini model drives all four steps
- **Two ways to run** — a one-command CLI and a Streamlit web UI with Markdown report download
- **Modern Python tooling** — managed with uv, with a lockfile for reproducible installs

## Built With

- Python 3.12
- uv
- LangChain
- Google Gemini
- Tavily Search
- Trafilatura, Readability and BeautifulSoup
- Streamlit

## Architecture

```text
┌──────────────────────────────────────────────────────┐
│       Streamlit UI (app.py)  ·  CLI (main.py)        │
│             User enters a research topic             │
└──────────────────────────┬───────────────────────────┘
                           │ topic
┌──────────────────────────▼───────────────────────────┐
│           Research Pipeline (pipeline.py)            │
│    Runs 4 steps in order, sharing one state dict     │
└──────────────────────────┬───────────────────────────┘
     ┌──────────────┬──────┴───────┬──────────────┐
     │ 1            │ 2            │ 3            │ 4
┌────▼────┐    ┌────▼────┐    ┌────▼────┐    ┌────▼────┐
│  Search │───▶│  Reader │───▶│  Writer │───▶│  Critic │
│  Agent  │    │  Agent  │    │  Chain  │    │  Chain  │
└────┬────┘    └────┬────┘    └─────────┘    └────┬────┘
     │              │                             │
┌────▼──────────────▼────┐               ┌────────▼────────┐
│ Tools Layer (tools.py) │               │   Final output  │
│      • web_search      │               │  Report + score │
│      • scrape_url      │               │    & feedback   │
└────┬──────────────┬────┘               └─────────────────┘
     │              │
┌────▼─────┐ ┌──────▼──────┐
│  Tavily  │ │   Web page  │
│Search API│ │  (scraped)  │
└──────────┘ └─────────────┘

All four steps are powered by Google Gemini (agents.py)
```

The pipeline passes a shared `state` dict from step to step:

| Step | Component | Type | Input | Output |
| --- | --- | --- | --- | --- |
| 1 | Search Agent | Tool-calling agent (`create_agent`) | Topic | Titles, URLs and snippets from Tavily (top 5) |
| 2 | Reader Agent | Tool-calling agent (`create_agent`) | Search results | Clean text of the most relevant page |
| 3 | Writer Chain | Prompt → LLM → string chain | Topic + search results + scraped text | Structured research report |
| 4 | Critic Chain | Prompt → LLM → string chain | Report | Score, strengths, improvements, verdict |

The two agents decide for themselves when to call their tool; the writer and critic are plain chains that make a single LLM call. `scrape_url` tries three extraction strategies in order (Trafilatura, then Readability, then a full-page BeautifulSoup fallback) and caps the result at 5,000 characters.

The code is split into three layers under `src/`: `tools/` (the `web_search` and `scrape_url` tools), `agents/` (the Gemini model, both agents and both chains) and `pipelines/` (the step-by-step orchestration).

## Getting Started

**1. Install uv**

```bash
brew install uv
```

**2. Install dependencies**

```bash
uv sync
```

**3. Add API keys** — get them from [Google Gemini](https://aistudio.google.com/apikey) and [Tavily](https://app.tavily.com)

```bash
cp .env.example .env
```

```dotenv
GOOGLE_API_KEY=your-google-api-key
TAVILY_API_KEY=your-tavily-api-key
```

**4. Run**

```bash
uv run main.py                # CLI: researches the built-in example topic
uv run streamlit run app.py   # Web UI: opens http://localhost:8501
```

## Project Structure

```text
multi-agent-research-system/
├── README.md              ← You are here
├── app.py                 # Streamlit web UI for the research pipeline
├── main.py                # Command-line demo of the research pipeline
├── src/
│   ├── tools/
│   │   └── tools.py       # web_search (Tavily) and scrape_url tools
│   ├── agents/
│   │   └── agents.py      # Gemini model, Search/Reader agents, Writer/Critic chains
│   └── pipelines/
│       └── pipeline.py    # Runs the four steps in order and returns the state
├── pyproject.toml         # Project metadata and dependencies (uv)
├── uv.lock                # Locked dependency versions
├── LICENSE                # Apache License 2.0
├── .env.example           # Template for the required API keys
├── .env                   # Your real API keys (git-ignored)
└── .gitignore
```

## Copyright

© 2026 ylx. Released under the [Apache License 2.0](LICENSE).
