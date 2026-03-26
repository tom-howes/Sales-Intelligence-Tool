# Sales Intelligence Tool

A pre-call research tool for enterprise sales engineers. Enter a prospect's URL and your product, and the tool generates a structured discovery brief tailored to the stakeholder you're meeting — CISO, VP Engineering, or CFO.

Live demo: [sales-intelligence-tool.streamlit.app](https://sales-intelligence-tool.streamlit.app)

---

## Background

Thorough pre-call research is one of the most time-intensive parts of enterprise sales engineering: reading a prospect's website, inferring their tech stack, mapping likely pain points to your product's value proposition, and preparing discovery questions tailored to the specific stakeholder you're meeting. Done properly, it takes significant time per account and becomes a bottleneck when managing a large pipeline.

This tool is designed to accelerate that process. Not replace the judgment of an experienced SE, but eliminate the manual groundwork so that preparation time can be spent on higher-value thinking.

The idea came directly from my time as an Account Executive at Panopto, where I ran the pre-sales motion on complex enterprise deals and built custom demo environments for IT and Security stakeholders. I wanted to see how much of that research process could be automated with an LLM pipeline.

---

## How It Works

1. Firecrawl scrapes the prospect's key pages (homepage, /about, /product, /customers)
2. Firecrawl separately scrapes the seller's product page to extract value proposition context
3. Both are injected into a structured prompt sent to the Claude API
4. The model returns a consistent brief with five sections, framed for the selected stakeholder persona

The stakeholder personas (CISO, VP Engineering, CFO) each have distinct tone, focus areas, and discovery question framing — the same prospect generates meaningfully different briefs depending on who you're meeting.

---

## Brief Structure

Each generated brief contains:

- **Company Overview**: what the prospect does, their market, and scale
- **Tech Stack Signals**: inferred technology choices from public-facing content
- **Likely Pain Points**: framed around the seller's value proposition and the stakeholder's priorities
- **Suggested Discovery Questions**: tailored to the stakeholder persona
- **Potential Objections**: likely pushback with suggested responses

---

## Tech Stack

- Python
- Streamlit — frontend and deployment
- Firecrawl — web scraping and content extraction
- Anthropic Claude API — brief generation
- python-dotenv — local environment management

---

## Running Locally

Clone the repo and install dependencies:

```bash
git clone https://github.com/tom-howes/Sales-Intelligence-Tool.git
cd Sales-Intelligence-Tool
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Add your API keys to a `.env` file in the project root:

```
ANTHROPIC_API_KEY=your_key_here
FIRECRAWL_API_KEY=your_key_here
```

Run the app:

```bash
streamlit run app.py
```

---

## Project Structure

```
Sales-Intelligence-Tool/
├── app.py              # Streamlit UI
├── pipeline.py         # Scraping and LLM pipeline
├── requirements.txt
├── .streamlit/
│   └── config.toml     # Dark theme configuration
└── .env                # Local API keys (not committed)
```

---

## Planned Improvements

- RAG support for internal documents — upload product one-pagers, battlecards, or architecture docs as seller context instead of relying solely on public website scraping
- React frontend for improved UI and mobile experience
- Caching scraped content to reduce API calls on repeated prospects