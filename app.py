import streamlit as st
from pipeline import scrape_company, generate_brief, STAKEHOLDER_PERSONAS, SCRAPE_PATHS, MAX_CHARS_PER_PAGE, MAX_CHARS_SELLER

# --- Page config ---
st.set_page_config(
    page_title="Sales Intelligence Tool",
    page_icon=None,
    layout="wide"
)

# --- Header ---
st.title("Sales Intelligence Tool")
st.caption("Generate a tailored pre-call research brief for any prospect.")

st.divider()

# --- Inputs ---
col1, col2 = st.columns(2)

with col1:
    prospect_url = st.text_input(
        "Prospect URL",
        placeholder="https://targetcompany.com"
    )

with col2:
    selling_product = st.text_input(
        "Product You Are Selling",
        placeholder="e.g. Weights & Biases"
    )

col3, col4 = st.columns(2)

with col3:
    seller_url = st.text_input(
        "Your Product URL",
        placeholder="https://wandb.ai"
    )

with col4:
    stakeholder = st.selectbox(
        "Stakeholder",
        options=list(STAKEHOLDER_PERSONAS.keys()),
        index=1  # default to VP Engineering
    )

generate = st.button("Generate Brief", type="primary", use_container_width=True)

st.divider()

# --- Generation ---
if generate:
    if not prospect_url or not selling_product or not seller_url:
        st.warning("Please fill in all fields before generating.")
    else:
        with st.spinner("Scraping prospect..."):
            prospect_content = scrape_company(prospect_url, SCRAPE_PATHS, MAX_CHARS_PER_PAGE)

        if not prospect_content:
            st.error("Could not scrape the prospect URL. Check the URL and try again.")
            st.stop()

        with st.spinner(f"Scraping {selling_product}..."):
            seller_content = scrape_company(seller_url, ["", "/product"], MAX_CHARS_SELLER)

        with st.spinner("Generating brief..."):
            brief = generate_brief(
                prospect_url,
                prospect_content,
                seller_content,
                stakeholder,
                selling_product
            )

        # --- Store in session state so switching stakeholder doesn't wipe it ---
        st.session_state["brief"] = brief
        st.session_state["stakeholder"] = stakeholder
        st.session_state["selling_product"] = selling_product
        st.session_state["prospect_url"] = prospect_url

# --- Render brief if available ---
if "brief" in st.session_state:
    brief = st.session_state["brief"]

    st.subheader(f"Brief — {st.session_state['stakeholder']} | {st.session_state['selling_product']} → {st.session_state['prospect_url']}")

    # Parse and render sections
    sections = brief.split("## ")
    for section in sections:
        if section.strip():
            lines = section.strip().split("\n", 1)
            title = lines[0].strip()
            content = lines[1].strip() if len(lines) > 1 else ""
            with st.expander(title, expanded=True):
                st.markdown(content)

    st.divider()

    # --- Export options ---
    st.subheader("Export")
    ecol1, ecol2 = st.columns(2)

    with ecol1:
        st.download_button(
            label="Download as Markdown",
            data=brief,
            file_name=f"brief_{st.session_state['prospect_url'].replace('https://','').replace('/','_')}.md",
            mime="text/markdown",
            use_container_width=True
        )

    with ecol2:
        # Format as a concise Slack message
        slack_msg = f"""*Pre-call Brief: {st.session_state['prospect_url']}*
*Stakeholder:* {st.session_state['stakeholder']} | *Selling:* {st.session_state['selling_product']}

"""
        # Extract just Company Overview and Discovery Questions for Slack
        for section in brief.split("## "):
            if section.startswith("Company Overview"):
                lines = section.strip().split("\n", 1)
                slack_msg += f"*Company Overview*\n{lines[1].strip() if len(lines) > 1 else ''}\n\n"
            if section.startswith("Suggested Discovery Questions"):
                lines = section.strip().split("\n", 1)
                slack_msg += f"*Discovery Questions*\n{lines[1].strip() if len(lines) > 1 else ''}"

        st.download_button(
            label="Download as Slack Message",
            data=slack_msg,
            file_name=f"slack_{st.session_state['prospect_url'].replace('https://','').replace('/','_')}.txt",
            mime="text/plain",
            use_container_width=True
        )