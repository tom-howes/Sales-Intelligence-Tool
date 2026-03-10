import os
from dotenv import load_dotenv
from firecrawl import FirecrawlApp
import anthropic

load_dotenv()

firecrawl = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SCRAPE_PATHS = ["", "/about", "/product", "/customers"]
MAX_CHARS_PER_PAGE = 3000

STAKEHOLDER_PERSONAS = {
    "CISO": {
        "focus": "security architecture, compliance requirements, data governance, risk exposure, and regulatory obligations (SOC2, GDPR, HIPAA etc.)",
        "tone": "technical and risk-aware",
        "questions_focus": "security posture, data handling, compliance gaps, and incident response"
    },
    "VP Engineering": {
        "focus": "system architecture, API integrations, developer experience, scalability, and technical debt",
        "tone": "technical and pragmatic",
        "questions_focus": "current stack, integration complexity, engineering bandwidth, and build vs buy decisions"
    },
    "CFO": {
        "focus": "cost reduction, ROI, operational efficiency, budget cycles, and risk mitigation in financial terms",
        "tone": "commercially focused and concise",
        "questions_focus": "current spend, expected ROI, payback period, and budget approval process"
    }
}


def scrape_company(base_url: str) -> str:
    base_url = base_url.rstrip("/")
    combined = []

    for path in SCRAPE_PATHS:
        url = base_url + path
        try:
            result = firecrawl.scrape(url, formats=["markdown"])
            markdown = result.markdown if result else None
            if markdown:
                combined.append(f"### Page: {url}\n{markdown[:MAX_CHARS_PER_PAGE]}")
                print(f"Scraped {url}")
            else:
                print(f"No content at {url}")
        except Exception as e:
            print(f"Failed to scrape {url}: {e}")

    return "\n\n".join(combined)


def generate_brief(company_url: str, scraped_content: str, stakeholder: str = "VP Engineering") -> str:
    persona = STAKEHOLDER_PERSONAS[stakeholder]

    prompt = f"""You are an expert sales engineer preparing for an enterprise discovery call with a {stakeholder}.

Your brief should be tailored specifically for this audience, with a {persona['tone']} tone.
Focus on: {persona['focus']}

Based on the following scraped content from {company_url}, generate a structured pre-call research brief.

<scraped_content>
{scraped_content}
</scraped_content>

Return your response using EXACTLY this structure with EXACTLY these section headers. Do not add, remove, or rename any sections.

## Company Overview
3-4 sentences. What the company does, their market, and their scale. No bullet points.

## Tech Stack Signals
Exactly 5 bullet points. Each bullet is one concise sentence. No sub-bullets. No inline annotations.

## Likely Pain Points
Exactly 5 bullet points. Each bullet is one concise sentence framed for a {stakeholder}. No sub-bullets. No inline annotations.

## Suggested Discovery Questions
Exactly 5 numbered questions. Each question is one sentence only. No explanatory notes or annotations after the question.

## Potential Objections
Exactly 3 objections. Format each as:
**[Objection in quotes]**
Response: [One sentence on how to address it.]

If the scraped content is insufficient to populate a section with confidence, use what signals are available and note briefly at the end of that section only: "Note: Limited data available for this section."
"""

    message = claude.messages.create(
        model="claude-haiku-4-5-20251001",  # swap to claude-sonnet-4-6 for production
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text


def run(company_url: str, stakeholder: str = "VP Engineering"):
    print(f"\nScraping {company_url}...\n")
    scraped = scrape_company(company_url)

    if not scraped:
        print("No content scraped. Check the URL and try again.")
        return

    print(f"\nGenerating brief for {stakeholder}...\n")
    brief = generate_brief(company_url, scraped, stakeholder)

    print("\n" + "=" * 60)
    print(brief)
    print("=" * 60)


if __name__ == "__main__":
    url = input("Enter company URL (e.g. https://targetcompany.com): ").strip()
    print(f"\nStakeholder options: {', '.join(STAKEHOLDER_PERSONAS.keys())}")
    stakeholder = input("Select stakeholder (default: VP Engineering): ").strip() or "VP Engineering"
    run(url, stakeholder)