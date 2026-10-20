SEARCH_DOCS = "search_docs"

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
]
