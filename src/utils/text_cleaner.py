def clean_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\n", " ")
    text = text.replace("\t", " ")
    text = " ".join(text.split())
    return text