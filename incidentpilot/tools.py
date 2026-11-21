import json
from .log_parser import search_logs, summarize_logs, get_timeline

def build_tool_specs():
    return [
        {
            "type": "function",
            "function": {
                "name": "get_log_summary",
                "description": "Return counts of log levels, errors, warnings, request IDs and time range.",
                "parameters": {"type": "object", "properties": {}, "additionalProperties": False}
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_logs",
                "description": "Search uploaded log lines. All words in query must appear in a matching line.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Words or request ID to search for"},
                        "limit": {"type": "integer", "minimum": 1, "maximum": 50}
                    },
                    "required": ["query"],
                    "additionalProperties": False
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_timeline",
                "description": "Return the first log lines in chronological file order.",
                "parameters": {
                    "type": "object",
                    "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 100}},
                    "additionalProperties": False
                }
            }
        }
    ]

def execute_tool(name, arguments, rows):
    if name == "get_log_summary":
        result = summarize_logs(rows)
    elif name == "search_logs":
        result = search_logs(rows, arguments.get("query", ""), arguments.get("limit", 20))
    elif name == "get_timeline":
        result = get_timeline(rows, arguments.get("limit", 30))
    else:
        result = {"error": f"Tool not allowed: {name}"}
    return json.dumps(result, ensure_ascii=False)
