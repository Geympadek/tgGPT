from transformers import LlamaTokenizer
from collections import defaultdict

def separate_string(string: str):
    """
    Splits string into dict of html tags and text without it.
    """
    data: dict[str, list] = defaultdict(list)
    messages = []
    
    start = 0
    try:
        while True:
            tag_start = string.find('<', start)

            message = string[start:tag_start].strip()
            if message != '':
                messages.append(message)

            tag_end = string.find('>', tag_start)

            if tag_start == -1 or tag_end == -1:
                break

            if string[tag_start + 1] == '/':
                print("What's wrong with you?")
                start = tag_end

            tag_name = string[tag_start + 1: tag_end]
            open_tag = f"<{tag_name}>"
            close_tag = f"</{tag_name}>"

            tag_shift = len(open_tag) + len(close_tag)

            end_idx = string.find(close_tag, tag_end)

            content = string[tag_end + 1 : end_idx]

            data[tag_name].append(content)

            start = tag_start + len(content) + tag_shift
    except IndexError:
        print("Out of range")

    return data, messages

tokenizer: LlamaTokenizer = LlamaTokenizer.from_pretrained('openlm-research/open_llama_3b_v2', cache_dir="tokenizer")

def count_tokens(text: str):
    output = tokenizer.tokenize(text)
    return len(output)