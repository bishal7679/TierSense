from app.core.llms import gemini, gpt, claude, ollama, copilot

def generate_tiering_suggestions(llm_type: str, access_counts: dict) -> str:
    llm_type = llm_type.lower()

    if llm_type == "gemini":
        return gemini.generate(access_counts)
    elif llm_type == "gpt":
        return gpt.generate(access_counts)
    elif llm_type == "claude":
        return claude.generate(access_counts)
    elif llm_type == "ollama":
        return ollama.generate(access_counts)
    elif llm_type == "copilot":
        return copilot.generate(access_counts)
    else:
        raise ValueError(f"Unsupported LLM type: {llm_type}")
