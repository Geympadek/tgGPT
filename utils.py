
def tag_content(src: str, tag: str):
    start = src.find(f"<{tag}>")
    if start == -1:
        return None
    
    start += len(tag) + 2
    
    end = src.find(f"</{tag}>", start)
    return src[start:end]
