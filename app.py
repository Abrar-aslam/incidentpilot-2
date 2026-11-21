import streamlit as st
from openai import OpenAI

from incidentpilot.config import get_settings
from incidentpilot.log_parser import parse_logs, summarize_logs
from incidentpilot.agent import investigate
from incidentpilot.redaction import redact_rows, redact_text


# --------------------------------------------------
# 1. Application configuration
# --------------------------------------------------

st.set_page_config(
    page_title="IncidentPilot",
    page_icon="🛠️",
    layout="wide",
)

st.title("🛠️ IncidentPilot")
st.caption(
    "Evidence-backed AI incident investigation · Powered by Qwen"
)


# --------------------------------------------------
# 2. Initialize session state
# --------------------------------------------------

if "log_text" not in st.session_state:
    st.session_state.log_text = ""

if "report" not in st.session_state:
    st.session_state.report = None

if "trace" not in st.session_state:
    st.session_state.trace = []

if "investigation_error" not in st.session_state:
    st.session_state.investigation_error = None


# --------------------------------------------------
# 3. Sidebar: Incident context
# --------------------------------------------------

with st.sidebar:
    st.header("Incident details")

    incident_context = st.text_area(
        "What is happening?",
        placeholder=(
            "Example: POST /api/orders started "
            "returning 500 errors around 10:42."
        ),
    )

    st.info(
        "MVP mode: Uploaded logs only. "
        "No production systems are modified."
    )

    st.warning(
        "Sensitive values are masked before logs and "
        "incident context are sent to the AI provider."
    )


# --------------------------------------------------
# 4. Upload application logs
# --------------------------------------------------

uploaded = st.file_uploader(
    "Upload application logs",
    type=["log", "txt"],
)

sample_button = st.button("Load sample incident")


if sample_button:
    try:
        with open(
            "sample_logs/incident.log",
            "r",
            encoding="utf-8",
        ) as file:
            st.session_state.log_text = file.read()

        st.session_state.report = None
        st.session_state.trace = []
        st.session_state.investigation_error = None

    except FileNotFoundError:
        st.error(
            "Sample incident file not found. "
            "Check the sample_logs directory."
        )


if uploaded is not None:
    raw = uploaded.getvalue()

    if len(raw) > 2_000_000:
        st.error("File exceeds the 2 MB MVP limit.")
        st.stop()

    st.session_state.log_text = raw.decode(
        "utf-8",
        errors="replace",
    )

    # Reset old investigation when a new file is uploaded.
    st.session_state.report = None
    st.session_state.trace = []
    st.session_state.investigation_error = None


# --------------------------------------------------
# 5. Display log content
# --------------------------------------------------

log_text = st.text_area(
    "Log content",
    value=st.session_state.log_text,
    height=220,
    help=(
        "Original uploaded logs are displayed locally. "
        "They are redacted before AI investigation."
    ),
)

if log_text:
    st.session_state.log_text = log_text

    # --------------------------------------------------
    # 6. Parse original logs
    # --------------------------------------------------

    try:
        rows = parse_logs(log_text)
        summary = summarize_logs(rows)

    except Exception as exc:
        st.error(f"Log parsing failed: {exc}")
        st.stop()

    # --------------------------------------------------
    # 7. Redact sensitive information
    # --------------------------------------------------

    # Original parsed rows remain unchanged.
    # The AI receives only the redacted copy.

    try:
        safe_rows, log_redaction_counts = redact_rows(rows)

        safe_incident_context, context_redaction_counts = (
            redact_text(incident_context or "")
        )

        # Combine counts from logs and incident context.
        total_redactions = {
            key: (
                log_redaction_counts.get(key, 0)
                + context_redaction_counts.get(key, 0)
            )
            for key in log_redaction_counts
        }

        total_redacted = sum(total_redactions.values())

    except Exception as exc:
        st.error(f"Sensitive-data redaction failed: {exc}")

        # Fail closed: never send original logs to the AI.
        st.stop()

    # --------------------------------------------------
    # 8. Dashboard metrics
    # --------------------------------------------------

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Log lines",
        summary["total_lines"],
    )

    c2.metric(
        "Errors",
        summary["error_count"],
    )

    c3.metric(
        "Warnings",
        summary["warning_count"],
    )

    c4.metric(
        "Request IDs",
        len(summary["request_ids"]),
    )

    # --------------------------------------------------
    # 9. Original parsed log preview
    # --------------------------------------------------

    with st.expander("Parsed log preview"):
        st.warning(
            "This preview contains original log values and is "
            "displayed locally. Do not share screenshots containing "
            "credentials or personal information."
        )

        st.dataframe(
            rows,
            use_container_width=True,
        )

    # --------------------------------------------------
    # 10. Sensitive-data redaction preview
    # --------------------------------------------------

    with st.expander(
        "🔐 Sensitive data redaction preview",
        expanded=True,
    ):

        st.write(
            "This is the redacted data prepared for AI investigation."
        )

        st.metric(
            "Sensitive values detected",
            total_redacted,
        )

        st.write("Redaction breakdown")

        st.json(total_redactions)

        if total_redacted > 0:
            st.success(
                f"{total_redacted} sensitive value(s) masked."
            )
        else:
            st.info(
                "No supported sensitive patterns were detected. "
                "This does not guarantee that the logs contain "
                "no sensitive information."
            )

        st.write("Redacted log preview")

        st.dataframe(
            safe_rows,
            use_container_width=True,
        )

        st.write("Redacted incident context")

        st.code(
            safe_incident_context or "No incident context provided.",
            language="text",
        )

    # --------------------------------------------------
    # 11. Investigate incident
    # --------------------------------------------------

    if st.button(
        "🔍 Investigate incident",
        type="primary",
    ):

        try:
            settings = get_settings()

            client = OpenAI(
                api_key=settings["api_key"],
                base_url=settings["base_url"],
            )

            with st.spinner(
                "IncidentPilot is collecting evidence and investigating..."
            ):

                # IMPORTANT:
                # Pass safe_rows, NOT original rows.
                # Pass safe_incident_context, NOT original context.

                report, trace = investigate(
                    client=client,
                    model=settings["model"],
                    rows=safe_rows,
                    incident_context=safe_incident_context,
                    max_steps=settings["max_agent_steps"],
                )

            st.session_state.report = report
            st.session_state.trace = trace
            st.session_state.investigation_error = None

            st.success("Incident investigation completed.")

        except Exception as exc:
            st.session_state.investigation_error = str(exc)
            st.session_state.report = None
            st.session_state.trace = []

    # --------------------------------------------------
    # 12. Display investigation errors
    # --------------------------------------------------

    if st.session_state.investigation_error:
        st.error(
            "Investigation failed: "
            + st.session_state.investigation_error
        )

    # --------------------------------------------------
    # 13. Display investigation report
    # --------------------------------------------------

    if st.session_state.report:

        st.divider()

        st.subheader("Incident investigation report")

        st.markdown(
            st.session_state.report
        )

        st.download_button(
            "📥 Download incident report",
            data=st.session_state.report,
            file_name="incidentpilot-report.md",
            mime="text/markdown",
        )

        # --------------------------------------------------
        # 14. Agent tool-call trace
        # --------------------------------------------------

        with st.expander("Agent tool-call trace"):

            if not st.session_state.trace:
                st.info(
                    "No diagnostic tool calls were recorded."
                )

            for item in st.session_state.trace:

                st.markdown(
                    f"**Tool:** `{item['tool']}`"
                )

                st.json(
                    item["arguments"]
                )

                st.code(
                    item["result"],
                    language="json",
                )

else:
    st.caption(
        "Upload logs or load the sample incident to begin."
    )