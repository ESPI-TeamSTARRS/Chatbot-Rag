SEARCH_DOCS = "search_docs"
WRITE_REPORT = "write_report"

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": SEARCH_DOCS,
            "description": (
                "BM25 keyword search over the whole incident documentation, in a single call. Pass a "
                "short query made of the most distinctive keywords (error names, component names, "
                "symptoms); strip paths, line numbers and timestamps from stack traces. Returns the "
                "full content of the 5 best matching documents, most relevant first."
            ),
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Keywords to search for"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": WRITE_REPORT,
            "description": (
                "Write the incident report once you have the diagnosis. Provide only a short title "
                "and a summary; the error trace and tool calls are added automatically. The title "
                "becomes the file name: use the name given by the documentation's 'Report' section "
                "if there is one, otherwise choose it yourself."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Report name: from the documentation's Report section if any, else your own short title"},
                    "summary": {"type": "string", "description": "Diagnosis and recommended procedure"},
                },
                "required": ["title", "summary"],
            },
        },
    },
]
