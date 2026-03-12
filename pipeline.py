import os
from dotenv import load_dotenv
from firecrawl import FirecrawlApp
import anthropic

load_dotenv()

firecrawl = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SCRAPE_PATHS = ["", "/about", "/product", "/customers"]
MAX_CHARS_PER_PAGE = 3000
MAX_CHARS_SELLER = 2000  # lighter scrape for seller — just homepage and product

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


def scrape_company(base_url: str, paths: list, max_chars: int) -> str:
    base_url = base_url.rstrip("/")
    combined = []

    for path in paths:
        url = base_url + path
        try:
            result = firecrawl.scrape(url, formats=["markdown"])
            markdown = result.markdown if result else None
            if markdown:
                combined.append(f"### Page: {url}\n{markdown[:max_chars]}")
                print(f"Scraped {url}")
            else:
                print(f"No content at {url}")
        except Exception as e:
            print(f"Failed to scrape {url}: {e}")

    return "\n\n".join(combined)


def generate_brief(
    prospect_url: str,
    prospect_content: str,
    seller_content: str,
    stakeholder: str = "VP Engineering",
    selling_product: str = ""
) -> str:
    persona = STAKEHOLDER_PERSONAS[stakeholder]

    prompt = f"""You are a sales engineer at {selling_product} preparing for an enterprise discovery call with a {stakeholder} at a prospect company.

Below is scraped content describing YOUR product ({selling_product}) and the PROSPECT company separately.
Your job is to use your understanding of {selling_product}'s capabilities to identify where it addresses the prospect's challenges.
Always frame pain points, discovery questions, and objections around {selling_product}'s specific value — not the prospect's own products or generic industry problems.

<seller_content>
{seller_content}
</seller_content>

<prospect_content>
{prospect_content}
</prospect_content>

Your brief should be tailored for a {stakeholder} audience, with a {persona['tone']} tone.
Focus on: {persona['focus']}

Return your response using EXACTLY this structure with EXACTLY these section headers. Do not add, remove, or rename any sections.

## Company Overview
3-4 sentences. What the prospect company does, their market, and their scale. No bullet points.

## Tech Stack Signals
Exactly 5 bullet points. Each bullet is one concise sentence. No sub-bullets. No inline annotations.

## Likely Pain Points
Exactly 5 bullet points. Each bullet is one concise sentence framed for a {stakeholder} and connected to how {selling_product} addresses it. No sub-bullets. No inline annotations.

## Suggested Discovery Questions
Exactly 5 numbered questions relevant to how {selling_product} solves problems for a {stakeholder}. Each question is one sentence only. No explanatory notes or annotations after the question.

## Potential Objections
Exactly 3 objections a {stakeholder} might raise against adopting {selling_product}. Format each as:
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


def run(prospect_url: str, seller_url: str, stakeholder: str = "VP Engineering", selling_product: str = ""):
    print(f"\nScraping prospect: {prospect_url}...\n")
    prospect_content = scrape_company(prospect_url, SCRAPE_PATHS, MAX_CHARS_PER_PAGE)

    if not prospect_content:
        print("No prospect content scraped. Check the URL and try again.")
        return

    print(f"\nScraping seller: {seller_url}...\n")
    seller_content = scrape_company(seller_url, ["", "/product"], MAX_CHARS_SELLER)

    if not seller_content:
        print("Warning: no seller content scraped. Brief will be less product-specific.")

    print(f"\nGenerating brief for {stakeholder}...\n")
    brief = generate_brief(prospect_url, prospect_content, seller_content, stakeholder, selling_product)

    print("\n" + "=" * 60)
    print(brief)
    print("=" * 60)


if __name__ == "__main__":
    prospect_url = input("Enter prospect URL (e.g. https://targetcompany.com): ").strip()
    selling_product = input("What product are you selling? (e.g. Weights & Biases): ").strip()
    seller_url = input(f"Enter {selling_product} website URL: ").strip()
    print(f"\nStakeholder options: {', '.join(STAKEHOLDER_PERSONAS.keys())}")
    stakeholder = input("Select stakeholder (default: VP Engineering): ").strip() or "VP Engineering"
    run(prospect_url, seller_url, stakeholder, selling_product)