import html
import re
import time

import streamlit as st

from src.agents.agents import build_search_agent, build_reader_agent, writer_chain, critic_chain

st.set_page_config(
    page_title="Multi-Agent Research",
    page_icon=":material/travel_explore:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

STEPS = [
    ("search", "Search", "Finds recent sources with Tavily"),
    ("reader", "Read", "Scrapes the most relevant page"),
    ("writer", "Write", "Drafts a structured, cited report"),
    ("critic", "Review", "Scores the report out of 10"),
]

EXAMPLES = [
    "Future of LLMs in the tech industry",
    "The latest AI agents in 2026",
    "Roadmap for AGI in the next 5 years",
]

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@300..700&family=Geist+Mono:wght@400;500&display=swap');

:root {
    --bg: #0a0a0b;
    --surface: #141416;
    --line: rgba(255,255,255,0.08);
    --line-strong: rgba(255,255,255,0.16);
    --text: #ededee;
    --body: #c9c9ce;
    --muted: #8b8b91;
    --faint: #5a5a60;
    --danger: #e5636a;
    --ease: cubic-bezier(0.16, 1, 0.3, 1);
    --sans: 'Geist', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif;
    --mono: 'Geist Mono', ui-monospace, 'SF Mono', Menlo, monospace;
}

.stApp { background: var(--bg); }
.stApp, .stApp p, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
.stApp label, .stApp input, .stApp button, .stApp summary { font-family: var(--sans); }
.stApp [data-testid="stMarkdownContainer"] * { font-family: var(--sans); }
.stApp code, .mono, .eyebrow, .label, .topbar .meta, .step .n, .step .s, .score, .foot,
[data-testid="stTextInput"] label p { font-family: var(--mono) !important; }
[data-testid="stIconMaterial"] { font-family: 'Material Symbols Rounded' !important; }

header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
[data-testid="InputInstructions"] { display: none; }

[data-testid="stMainBlockContainer"], .block-container {
    max-width: 1180px;
    padding: 1.5rem 2rem 5rem;
}
@media (max-width: 640px) {
    [data-testid="stMainBlockContainer"], .block-container { padding: 1rem 1rem 4rem; }
}

@keyframes rise   { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
@keyframes breathe { 0%, 100% { transform: scale(0.7); opacity: 0.45; } 50% { transform: scale(1); opacity: 1; } }
@keyframes shimmer { to { transform: translateX(100%); } }
@keyframes grow   { from { transform: scaleX(0); } }

/* ── Top bar ── */
.topbar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0.25rem 0 3.5rem;
}
.wordmark {
    display: flex; align-items: center; gap: 0.55rem;
    font-size: 0.95rem; font-weight: 600; letter-spacing: -0.01em; color: var(--text);
}
.wordmark i { width: 9px; height: 9px; border-radius: 50%; background: var(--text); display: inline-block; }
.topbar .meta { font-family: var(--mono); font-size: 0.72rem; color: var(--faint); letter-spacing: 0.04em; }

/* ── Hero ── */
.hero > * { animation: rise 0.8s var(--ease) both; }
.hero > *:nth-child(2) { animation-delay: 80ms; }
.hero > *:nth-child(3) { animation-delay: 160ms; }
.eyebrow, .label {
    font-family: var(--mono); font-size: 0.72rem; letter-spacing: 0.14em;
    text-transform: uppercase; color: var(--muted);
}
.eyebrow { margin-bottom: 1.1rem; }
.label { margin-bottom: 0.9rem; }
.headline {
    font-size: clamp(2.2rem, 4.6vw, 3.6rem); font-weight: 600;
    letter-spacing: -0.035em; line-height: 1.02; color: var(--text); margin: 0 0 1.1rem;
}
.headline span { color: var(--faint); }
.lede { color: var(--muted); font-size: 1.05rem; line-height: 1.6; max-width: 46ch; margin: 0 0 2.2rem; }

/* ── Input ── */
[data-testid="stTextInput"] label p {
    font-family: var(--mono); font-size: 0.72rem; letter-spacing: 0.14em;
    text-transform: uppercase; color: var(--muted);
}
[data-testid="stTextInput"] [data-baseweb="input"] {
    background: var(--surface); border-radius: 14px; border-color: var(--line-strong);
    transition: border-color 0.3s var(--ease);
}
[data-testid="stTextInput"] [data-baseweb="input"]:focus-within { border-color: rgba(255,255,255,0.42); }
[data-testid="stTextInput"] input { font-size: 1.05rem; padding: 0.95rem 1.05rem; color: var(--text); }

.stApp button { transition: transform 0.3s var(--ease), opacity 0.3s var(--ease), border-color 0.3s var(--ease); }
.stApp button:active { transform: scale(0.98); }

.stFormSubmitButton button {
    background: var(--text) !important; border: none !important; border-radius: 999px !important;
    padding: 0.6rem 1.6rem !important; min-height: 0 !important;
}
.stFormSubmitButton button p { color: var(--bg) !important; font-weight: 500; font-size: 0.92rem; }
.stFormSubmitButton button:hover { opacity: 0.86; }

.st-key-examples { margin-top: 1.6rem; gap: 0.5rem; flex-wrap: wrap; }
.st-key-examples button, .stDownloadButton button {
    background: transparent !important; border: 1px solid var(--line) !important;
    border-radius: 999px !important; padding: 0.32rem 0.9rem !important; min-height: 0 !important;
}
.st-key-examples button p, .stDownloadButton button p { color: var(--muted) !important; font-size: 0.82rem; }
.st-key-examples button:hover, .stDownloadButton button:hover { border-color: var(--line-strong) !important; }
.st-key-examples button:hover p, .stDownloadButton button:hover p { color: var(--text) !important; }

.field-error { color: var(--danger); font-size: 0.85rem; margin: 0.2rem 0 0; }

/* ── Pipeline ── */
.steps { list-style: none; margin: 0; padding: 0; border-top: 1px solid var(--line); }
.steps .step {
    display: grid; grid-template-columns: 2rem 1fr auto; gap: 0.75rem; align-items: baseline;
    padding: 1.05rem 0; border-bottom: 1px solid var(--line); margin: 0 !important;
}
.step .n { font-family: var(--mono); font-size: 0.72rem; color: var(--faint); }
.step .t { font-size: 0.98rem; font-weight: 500; color: var(--muted); letter-spacing: -0.01em; }
.step .d { font-size: 0.84rem; color: var(--faint); margin-top: 0.15rem; }
.step .s { font-family: var(--mono); font-size: 0.72rem; color: var(--faint); white-space: nowrap; }
.step.running .t, .step.done .t { color: var(--text); }
.step.running .d { color: var(--muted); }
.step.running .s, .step.done .s { color: var(--text); }
.step.error .t, .step.error .s { color: var(--danger); }
.dot {
    width: 7px; height: 7px; border-radius: 50%; display: inline-block;
    margin-right: 0.45rem; vertical-align: 1px; background: var(--faint);
}
.step.running .dot { background: var(--text); animation: breathe 1.4s ease-in-out infinite; }
.step.error .dot { background: var(--danger); }
.check { vertical-align: -2px; margin-right: 0.4rem; }

/* ── Sections ── */
.section {
    border-top: 1px solid var(--line); margin-top: 4.5rem; padding-top: 2.2rem;
    animation: rise 0.8s var(--ease) both;
}
.report-title {
    font-size: clamp(1.5rem, 2.6vw, 2rem); font-weight: 600; letter-spacing: -0.025em;
    line-height: 1.15; color: var(--text); margin: 0 0 2.2rem; max-width: 30ch;
}

/* ── Skeleton ── */
.skel {
    position: relative; overflow: hidden; height: 0.8rem; border-radius: 6px;
    background: rgba(255,255,255,0.05); margin: 0.8rem 0;
}
.skel.h { height: 1.6rem; margin-bottom: 1.6rem; }
.skel::after {
    content: ""; position: absolute; inset: 0; transform: translateX(-100%);
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.07), transparent);
    animation: shimmer 1.6s infinite;
}

/* ── Report ── */
.st-key-report { max-width: 68ch; }
.st-key-report h1, .st-key-report h2, .st-key-report h3 {
    color: var(--text); letter-spacing: -0.02em; font-weight: 600; padding: 0; margin: 2.2rem 0 0.8rem;
}
.st-key-report [data-testid="stMarkdownContainer"] > :first-child { margin-top: 0 !important; }
.st-key-report h1 { font-size: 1.45rem; }
.st-key-report h2 { font-size: 1.22rem; }
.st-key-report h3 { font-size: 1.04rem; }
.st-key-report p, .st-key-report li { color: var(--body); font-size: 1rem; line-height: 1.75; }
.st-key-report strong { color: var(--text); font-weight: 500; }
.st-key-report a, .st-key-raw a {
    color: var(--text); text-decoration: underline; text-underline-offset: 3px;
    text-decoration-color: var(--line-strong);
}
.st-key-report [data-testid="stHeaderActionElements"] { display: none; }

.st-key-raw { margin-top: 3rem; }
[data-testid="stExpander"] details {
    border: none; border-top: 1px solid var(--line); border-radius: 0; background: transparent;
}
[data-testid="stExpander"] summary p { font-size: 0.9rem; color: var(--muted); }
[data-testid="stExpander"] summary:hover p { color: var(--text); }
.st-key-raw p, .st-key-raw li { font-size: 0.88rem; color: var(--muted); line-height: 1.7; }

/* ── Critique ── */
.st-key-side { position: sticky; top: 2rem; }
.score {
    font-family: var(--mono); font-size: 3.4rem; font-weight: 500;
    letter-spacing: -0.04em; line-height: 1; color: var(--text);
}
.score span { color: var(--faint); font-size: 1.3rem; margin-left: 0.15rem; letter-spacing: 0; }
.meter { height: 2px; background: var(--line); margin: 1.2rem 0 1.3rem; overflow: hidden; border-radius: 2px; }
.meter i {
    display: block; height: 100%; background: var(--text);
    transform-origin: left; transform: scaleX(var(--v)); animation: grow 1.2s var(--ease) both;
}
.verdict { color: var(--text); font-size: 1rem; line-height: 1.55; margin: 0 0 1.6rem; }
.st-key-critic { border-top: 1px solid var(--line); padding-top: 1.2rem; margin-top: 1.6rem; }
.st-key-critic p, .st-key-critic li { font-size: 0.88rem; color: var(--muted); line-height: 1.65; }
.st-key-critic strong { color: var(--text); font-weight: 500; }

/* ── Alerts, empty state, footer ── */
.alert {
    border: 1px solid rgba(229,99,106,0.32); background: rgba(229,99,106,0.06);
    color: #f0b3b6; border-radius: 12px; padding: 0.9rem 1.1rem; font-size: 0.9rem;
    margin-top: 4.5rem;
}
.empty { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 2fr); gap: 2rem; }
.empty .rows { border-top: 1px solid var(--line); }
.empty .row {
    display: grid; grid-template-columns: 7.5rem 1fr; gap: 1rem;
    padding: 0.95rem 0; border-bottom: 1px solid var(--line); font-size: 0.9rem;
}
.empty .row b { font-weight: 500; color: var(--text); }
.empty .row span { color: var(--muted); }
.empty p { color: var(--muted); font-size: 0.95rem; line-height: 1.6; margin: 0; max-width: 32ch; }
@media (max-width: 640px) {
    .empty { grid-template-columns: 1fr; }
    .empty .row { grid-template-columns: 1fr; gap: 0.2rem; }
}
.foot {
    margin-top: 5rem; font-family: var(--mono); font-size: 0.72rem;
    color: var(--faint); letter-spacing: 0.04em;
}

@media (prefers-reduced-motion: reduce) {
    .stApp *, .stApp *::after { animation: none !important; transition: none !important; }
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
CHECK_SVG = (
    '<svg class="check" width="12" height="12" viewBox="0 0 12 12" fill="none">'
    '<path d="M2.5 6.2 5 8.6l4.5-5" stroke="currentColor" stroke-width="1.5" '
    'stroke-linecap="round" stroke-linejoin="round"/></svg>'
)


def pipeline_html(status: dict, times: dict) -> str:
    rows = []
    for i, (key, title, desc) in enumerate(STEPS, start=1):
        state = status.get(key, "waiting")
        if state == "done":
            badge = f"{CHECK_SVG}{times.get(key, 0):.1f}s"
        elif state == "running":
            badge = '<span class="dot"></span>Running'
        elif state == "error":
            badge = '<span class="dot"></span>Failed'
        else:
            badge = '<span class="dot"></span>Waiting'
        rows.append(
            f'<li class="step {state}"><span class="n">{i:02d}</span>'
            f'<div><div class="t">{title}</div><div class="d">{desc}</div></div>'
            f'<span class="s">{badge}</span></li>'
        )
    return f'<ol class="steps">{"".join(rows)}</ol>'


def skeleton_html(topic: str) -> str:
    widths = [94, 88, 97, 72, 0, 91, 84, 66]
    lines = "".join(
        '<div style="height:1.2rem"></div>' if w == 0 else f'<div class="skel" style="width:{w}%"></div>'
        for w in widths
    )
    return (
        f'<div class="section"><div class="label">Researching</div>'
        f'<div class="report-title">{html.escape(topic)}</div>'
        f'<div style="max-width:68ch"><div class="skel h" style="width:42%"></div>{lines}</div></div>'
    )


def parse_critique(text: str):
    score_match = re.search(r"Score:\s*\**\s*(\d+(?:\.\d+)?)\s*/\s*10\**", text)
    verdict_match = re.search(r"One line verdict:\**\s*(.+)", text, re.S)
    score = float(score_match.group(1)) if score_match else None
    verdict = verdict_match.group(1).strip().strip("*").strip() if verdict_match else ""
    body = text[: verdict_match.start()] if verdict_match else text
    if score_match:
        body = body.replace(score_match.group(0), "", 1)
    return score, verdict, body.strip()


def set_topic(value: str):
    st.session_state.topic_input = value


# ── Agent steps ───────────────────────────────────────────────────────────────
def run_search(topic: str, results: dict) -> str:
    out = build_search_agent().invoke({
        "messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]
    })
    return out["messages"][-1].text


def run_reader(topic: str, results: dict) -> str:
    out = build_reader_agent().invoke({
        "messages": [(
            "user",
            f"Based on the following search results about '{topic}', "
            f"pick the most relevant URL and scrape it for deeper content.\n\n"
            f"Search Results:\n{results['search'][:800]}",
        )]
    })
    return out["messages"][-1].text


def run_writer(topic: str, results: dict) -> str:
    research = (
        f"SEARCH RESULTS:\n{results['search']}\n\n"
        f"DETAILED SCRAPED CONTENT:\n{results['reader']}"
    )
    return writer_chain.invoke({"topic": topic, "research": research})


def run_critic(topic: str, results: dict) -> str:
    return critic_chain.invoke({"report": results["writer"]})


RUNNERS = {"search": run_search, "reader": run_reader, "writer": run_writer, "critic": run_critic}


def run_pipeline(topic: str, pipe, slot):
    ss = st.session_state
    ss.results, ss.times, ss.error, ss.topic = {}, {}, None, topic
    status = {key: "waiting" for key, _, _ in STEPS}

    with slot:
        st.markdown(skeleton_html(topic), unsafe_allow_html=True)

    for key, title, _ in STEPS:
        status[key] = "running"
        pipe.markdown(pipeline_html(status, ss.times), unsafe_allow_html=True)
        started = time.perf_counter()
        try:
            ss.results[key] = RUNNERS[key](topic, ss.results)
        except Exception as exc:
            status[key] = "error"
            ss.error = f"The {title} step failed: {exc}"
            break
        ss.times[key] = time.perf_counter() - started
        status[key] = "done"

    ss.status = status


def render_results():
    ss = st.session_state
    r = ss.results

    if ss.error:
        st.markdown(f'<div class="alert">{html.escape(ss.error)}</div>', unsafe_allow_html=True)

    if "writer" not in r:
        if not ss.error:
            st.markdown("""
            <div class="section empty">
                <div>
                    <div class="label">Output</div>
                    <p>Enter a topic above. Results appear here once the four steps finish, usually in under a minute.</p>
                </div>
                <div class="rows">
                    <div class="row"><b>Report</b><span>Introduction, key findings, conclusion and the source URLs</span></div>
                    <div class="row"><b>Critique</b><span>A score out of 10, strengths, what to improve and a verdict</span></div>
                    <div class="row"><b>Raw material</b><span>The search results and the scraped page the report was built on</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        return

    total = sum(ss.times.values())
    st.markdown(
        f'<div class="section"><div class="label">Report · <span style="text-transform:none">{total:.0f}s</span></div>'
        f'<div class="report-title">{html.escape(ss.topic)}</div></div>',
        unsafe_allow_html=True,
    )

    main, _, side = st.columns([8, 0.6, 3.6])

    with main:
        with st.container(key="report"):
            st.markdown(r["writer"])
        with st.container(key="raw"):
            if "search" in r:
                with st.expander("Search results"):
                    st.markdown(r["search"])
            if "reader" in r:
                with st.expander("Scraped source"):
                    st.markdown(r["reader"])

    with side:
        with st.container(key="side"):
            if "critic" in r:
                score, verdict, body = parse_critique(r["critic"])
                st.markdown('<div class="label">Critic score</div>', unsafe_allow_html=True)
                if score is not None:
                    shown = f"{score:g}"
                    st.markdown(
                        f'<div class="score">{shown}<span>/10</span></div>'
                        f'<div class="meter"><i style="--v:{min(score, 10) / 10:.2f}"></i></div>',
                        unsafe_allow_html=True,
                    )
                if verdict:
                    st.markdown(f'<p class="verdict">{html.escape(verdict)}</p>', unsafe_allow_html=True)
            st.download_button(
                "Download report (.md)",
                data=r["writer"],
                file_name=f"research_report_{int(time.time())}.md",
                mime="text/markdown",
                use_container_width=True,
            )
            if "critic" in r:
                with st.container(key="critic"):
                    st.markdown(body)


# ── State ─────────────────────────────────────────────────────────────────────
ss = st.session_state
ss.setdefault("results", {})
ss.setdefault("times", {})
ss.setdefault("status", {key: "waiting" for key, _, _ in STEPS})
ss.setdefault("error", None)
ss.setdefault("topic", "")


# ── Layout ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="topbar">
    <div class="wordmark"><i></i>Multi-Agent Research</div>
    <div class="meta">LangChain · Gemini · Tavily</div>
</div>
""", unsafe_allow_html=True)

left, _, right = st.columns([7, 0.8, 5])

with left:
    st.markdown("""
    <div class="hero">
        <div class="eyebrow">Four agents, one report</div>
        <div class="headline">What should we<br><span>research today?</span></div>
        <p class="lede">Agents search the web, read the strongest source, write a cited report, then grade it.</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("ask", border=False):
        topic = st.text_input(
            "Research topic",
            key="topic_input",
            placeholder="e.g. How AI is changing entry-level hiring",
        )
        submitted = st.form_submit_button("Research")
    field_error = st.empty()

    with st.container(key="examples", horizontal=True):
        for example in EXAMPLES:
            st.button(example, type="tertiary", on_click=set_topic, args=(example,))

with right:
    st.markdown('<div class="label">Pipeline</div>', unsafe_allow_html=True)
    pipe = st.empty()
    pipe.markdown(pipeline_html(ss.status, ss.times), unsafe_allow_html=True)

results_slot = st.container()

if submitted and not topic.strip():
    field_error.markdown('<p class="field-error">Enter a topic to start.</p>', unsafe_allow_html=True)

if submitted and topic.strip():
    run_pipeline(topic.strip(), pipe, results_slot)
    st.rerun()
else:
    with results_slot:
        render_results()

st.markdown('<div class="foot">Results are generated by AI and may contain mistakes. Check the sources.</div>',
            unsafe_allow_html=True)
