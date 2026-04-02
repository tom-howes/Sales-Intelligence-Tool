import streamlit as st
import httpx

BACKEND_URL = "http://localhost:8000"

STAKEHOLDER_PERSONAS = ["CISO", "VP Engineering", "CFO"]

# --- Page config ---
st.set_page_config(
    page_title="Sales Intelligence Tool",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS ---
st.markdown("""
<style>
    /* Clean up default padding */
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }

    /* Header */
    h1 { font-size: 1.8rem; font-weight: 700; margin-bottom: 0; }

    /* Input labels */
    label { font-weight: 600; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; }

    /* Generate button */
    .stButton > button {
        background-color: #0f62fe;
        color: white;
        border: none;
        border-radius: 4px;
        font-weight: 600;
        height: 3rem;
        font-size: 0.95rem;
    }
    .stButton > button:hover { background-color: #0353e9; }

    /* Expander headers */
    .streamlit-expanderHeader {
        font-weight: 700;
        font-size: 0.95rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        background-color: transparent;
    }

    /* Brief subheader */
    .brief-meta {
        font-size: 0.85rem;
        color: #6b7280;
        margin-bottom: 1rem;
    }

    /* Divider spacing */
    hr { margin: 1.5rem 0; }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.title("Sales Intelligence Tool")
st.caption("Generate a tailored pre-call research brief for any prospect.")

st.divider()

# --- Inputs ---
col1, col2 = st.columns(2)
with col1:
    prospect_url = st.text_input("Prospect URL", placeholder="https://targetcompany.com")
with col2:
    selling_product = st.text_input("Product You Are Selling", placeholder="e.g. Weights & Biases")

col3, col4 = st.columns(2)
with col3:
    seller_url = st.text_input("Your Product URL", placeholder="https://wandb.ai")
with col4:
    stakeholder = st.selectbox(
        "Stakeholder",
        options=STAKEHOLDER_PERSONAS,
        index=1
    )

uploaded_file = st.file_uploader(
    "Upload internal seller documents (optional)",
    type=["pdf", "txt"],
    help="Upload battlecards, one-pagers, or architecture docs to enrich the brief."
)

if uploaded_file is not None:
    if uploaded_file.file_id not in st.session_state.get("uploaded_file_ids", set()):
        with st.spinner(f"Processing {uploaded_file.name}..."):
            try:
                response = httpx.post(
                    f"{BACKEND_URL}/upload",
                    files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)},
                    timeout=60,
                )
                response.raise_for_status()
                data = response.json()
                st.success(f"Uploaded **{data['filename']}** — {data['chunk_count']} chunks indexed.")
                uploaded_ids = st.session_state.get("uploaded_file_ids", set())
                uploaded_ids.add(uploaded_file.file_id)
                st.session_state["uploaded_file_ids"] = uploaded_ids
                st.session_state["docs_uploaded"] = True
            except httpx.HTTPStatusError as e:
                st.error(f"Upload failed: {e.response.json().get('detail', str(e))}")
            except Exception as e:
                st.error(f"Upload failed: {e}")

generate = st.button("Generate Brief", type="primary", use_container_width=True)

st.divider()

# --- Generation ---
if generate:
    if not prospect_url or not selling_product or not seller_url:
        st.warning("Please fill in all fields before generating.")
    else:
        with st.spinner("Scraping prospect and seller websites..."):
            try:
                scrape_response = httpx.post(
                    f"{BACKEND_URL}/scrape",
                    json={"prospect_url": prospect_url, "seller_url": seller_url},
                    timeout=120,
                )
                scrape_response.raise_for_status()
                scraped = scrape_response.json()
            except httpx.HTTPStatusError as e:
                st.error(f"Scraping failed: {e.response.json().get('detail', str(e))}")
                st.stop()
            except Exception as e:
                st.error(f"Scraping failed: {e}")
                st.stop()

        rag_context = None
        if st.session_state.get("docs_uploaded"):
            with st.spinner("Retrieving relevant context from uploaded documents..."):
                try:
                    retrieve_response = httpx.post(
                        f"{BACKEND_URL}/retrieve",
                        json={"query": prospect_url, "k": 3},
                        timeout=30,
                    )
                    retrieve_response.raise_for_status()
                    rag_context = retrieve_response.json().get("chunks") or None
                except Exception as e:
                    st.warning(f"Could not retrieve document context: {e}")

        with st.spinner("Generating brief..."):
            try:
                generate_response = httpx.post(
                    f"{BACKEND_URL}/generate",
                    json={
                        "prospect_url": prospect_url,
                        "prospect_content": scraped["prospect_content"],
                        "seller_content": scraped["seller_content"],
                        "stakeholder": stakeholder,
                        "selling_product": selling_product,
                        "rag_context": rag_context,
                    },
                    timeout=60,
                )
                generate_response.raise_for_status()
                brief = generate_response.json()["brief"]
            except httpx.HTTPStatusError as e:
                st.error(f"Brief generation failed: {e.response.json().get('detail', str(e))}")
                st.stop()
            except Exception as e:
                st.error(f"Brief generation failed: {e}")
                st.stop()

        st.session_state["brief"] = brief
        st.session_state["stakeholder"] = stakeholder
        st.session_state["selling_product"] = selling_product
        st.session_state["prospect_url"] = prospect_url

# --- Render brief ---
if "brief" in st.session_state:
    brief = st.session_state["brief"]

    st.markdown(
        f"<div class='brief-meta'>"
        f"Stakeholder: <strong>{st.session_state['stakeholder']}</strong> &nbsp;|&nbsp; "
        f"Selling: <strong>{st.session_state['selling_product']}</strong> &nbsp;|&nbsp; "
        f"Prospect: <strong>{st.session_state['prospect_url']}</strong>"
        f"</div>",
        unsafe_allow_html=True
    )

    # Section icons for visual interest
    icons = {
        "Company Overview": "01",
        "Tech Stack Signals": "02",
        "Likely Pain Points": "03",
        "Suggested Discovery Questions": "04",
        "Potential Objections": "05"
    }

    sections = brief.split("## ")
    for section in sections:
        if section.strip():
            lines = section.strip().split("\n", 1)
            title = lines[0].strip()
            content = lines[1].strip() if len(lines) > 1 else ""
            icon = icons.get(title, "")
            label = f"{icon}  {title}" if icon else title
            with st.expander(label, expanded=True):
                st.markdown(content)

    st.divider()

    # --- Export ---
    st.markdown("#### Export")
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
        slack_msg = (
            f"*Pre-call Brief: {st.session_state['prospect_url']}*\n"
            f"*Stakeholder:* {st.session_state['stakeholder']} | "
            f"*Selling:* {st.session_state['selling_product']}\n\n"
        )
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
