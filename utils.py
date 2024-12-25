from transformers import LlamaTokenizer

def tag_content(src: str, tag: str):
    """
    """
    result = []

    open_tag = f"<{tag}>"
    close_tag = f"</{tag}>"

    start = 0
    while True:
        start = src.find(open_tag, start)
        if start == -1:
            break
        
        end = src.find(close_tag, start)
        result.append(src[start + len(open_tag):end])

        start = end + len(close_tag)
    return result

tokenizer: LlamaTokenizer = LlamaTokenizer.from_pretrained('openlm-research/open_llama_3b_v2', cache_dir="tokenizer")

def count_tokens(text: str):
    output = tokenizer.tokenize(text)
    return len(output)

if __name__ == "__main__":
    text = "Please pay the invoice above to subscribe to Telegram Premium Features."

    exp_count = len(text) / 4
    act_count = count_tokens(text)

    print(f"{exp_count = }, {act_count = }")