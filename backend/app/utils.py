def extract_text(content) -> str:
    """Extract string content from LLM response reliably.
    
    Handles both raw string responses and LangChain's list of content blocks
    that occurs with some models (e.g., Gemini).
    """
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        return "".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("text")
        )

    return str(content)
