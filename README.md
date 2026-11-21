# IncidentPilot

An MVP AI SRE incident investigation assistant powered by a Qwen API. It parses uploaded application logs, gives Qwen a small set of read-only diagnostic tools, and produces an evidence-backed report.

## What it does

- Upload `.log` / `.txt` files (2 MB MVP limit)
- Parse timestamps, severity levels and request IDs
- Summarise errors and warnings
- Let Qwen call read-only tools to search logs, inspect summary statistics and review the timeline
- Generate a report with symptoms, hypotheses, evidence, suggested fixes and regression tests
- Download the report as Markdown

## Safety boundaries

This project does **not** connect to production, run shell commands, edit source files, restart services or deploy fixes. Qwen output is advisory. Logs are untrusted input and may contain prompt-injection text; the system prompt tells the model to treat log contents as data. For real deployment, add stronger isolation, authentication, audit storage, secrets management and deterministic output validation.

## Requirements

- Python 3.10+
- A Qwen API key
- The matching OpenAI-compatible base URL and model ID from your Qwen provider/account

## Setup

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set:

- `QWEN_API_KEY`
- `QWEN_BASE_URL`
- `QWEN_MODEL`

The API key and endpoint must belong to the same provider/region/workspace. Use a model enabled for your account that supports chat completions and tool/function calling. Do not commit `.env`.

## Run

```bash
streamlit run app.py
```

Click **Load sample incident**, optionally add incident context, then click **Investigate incident**.

## Tests

```bash
pytest -q
```

## Architecture

Streamlit UI -> log parser -> Qwen tool-calling loop -> read-only diagnostic tools -> evidence-based report.

## Weekend build plan

1. Get the app running with the sample incident.
2. Configure the Qwen API and verify one basic model call.
3. Verify tool calling with the selected model.
4. Improve the report and add a second sample incident.
5. Test malformed logs, empty files, tool errors and prompt-injection strings.
6. Rehearse the demo using only synthetic logs.

## Limitations

- This MVP uses simple regex-based log parsing, not a production-grade parser.
- The agent's root-cause conclusions are hypotheses, not proof.
- No repository/code inspection is implemented yet.
- Tool calling support and parameter formats vary by model/provider.
- The model may return unsupported tool calls; the app only executes its allowlisted tools.
