import re
from collections import defaultdict

#THE FOLLOWING CODE WAS FULLY WRITTEN BY DEEPSEEK R1
def separate_string(text: str) -> list[str | dict[str, str]]:
    output = []
    current_pos = 0
    length = len(text)

    while current_pos < length:
        code_match = re.search(r'```', text[current_pos:], re.DOTALL)
        tag_match = re.search(r'<([a-zA-Z-]+)>', text[current_pos:])  # Hyphen allowed in tag names

        candidates = []
        if code_match:
            code_start_rel = code_match.start()
            candidates.append((code_start_rel, 'code'))
        if tag_match:
            tag_start_rel = tag_match.start()
            candidates.append((tag_start_rel, 'tag'))

        if not candidates:
            remaining = text[current_pos:]
            if remaining:
                output.append(remaining)
            break

        candidates.sort()
        first_offset, first_type = candidates[0]

        # Add text before the first candidate
        if first_offset > 0:
            text_segment = text[current_pos:current_pos + first_offset]
            output.append(text_segment)
            current_pos += first_offset

        if first_type == 'code':
            # Handle code block
            code_end = text.find('```', current_pos + 3)
            if code_end == -1:
                code_content = text[current_pos:]
                output.append(code_content)
                current_pos = length
            else:
                code_content = text[current_pos:code_end + 3]
                output.append(code_content)
                current_pos = code_end + 3
        else:
            # Handle tag
            tag_name = tag_match.group(1)
            closing_tag = f'</{tag_name}>'
            closing_pos = text.find(closing_tag, current_pos + len(tag_match.group(0)))

            if closing_pos == -1:
                # No closing tag found, add the opening tag as text
                output.append(text[current_pos:current_pos + len(tag_match.group(0))])
                current_pos += len(tag_match.group(0))
            else:
                # Extract content and add tag dictionary
                content_start = current_pos + len(tag_match.group(0))
                content = text[content_start:closing_pos]
                output.append({'tag': tag_name, 'content': content})
                current_pos = closing_pos + len(closing_tag)
    return cleanup(output)

def cleanup(output: list[str|dict]):
    new_output = []
    last_str = False

    for entry in output:
        if (type(entry) is str):
            if last_str:
                new_output[-1] += entry
                continue
            if entry.split() == '':
                continue
            last_str = True
        else:
            last_str = False
        
        new_output.append(entry)

    return new_output

from transformers import LlamaTokenizer
tokenizer: LlamaTokenizer = LlamaTokenizer.from_pretrained('openlm-research/open_llama_3b_v2', cache_dir="tokenizer")

def count_tokens(text: str):
    output = tokenizer.tokenize(text)
    return len(output)