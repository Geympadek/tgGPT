from transformers import LlamaTokenizer
from collections import defaultdict

def parse_string(string: str):
    result: dict[str, list] = defaultdict(list)
    
    start = 0
    try:
        while True:
            tag_start = string.find('<', start)
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

            result[tag_name].append(content)

            start = tag_start + len(content) + tag_shift
    except IndexError:
        print("Out of range")

    return result

def tag_content(src: str, tag: str):
    result = []

    open_tag = f"<{tag}>"
    close_tag = f"</{tag}>"

    tag_shift = len(open_tag) + len(close_tag)

    start = 0
    while True:
        start = src.find(open_tag, start)
        if start == -1:
            break
        
        end = src.find(close_tag, start)
        result.append(src[start + len(open_tag):end])

        start += len(result[-1]) + tag_shift
    return result

tokenizer: LlamaTokenizer = LlamaTokenizer.from_pretrained('openlm-research/open_llama_3b_v2', cache_dir="tokenizer")

def count_tokens(text: str):
    output = tokenizer.tokenize(text)
    return len(output)
