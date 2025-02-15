import re
from collections import defaultdict

#THE FOLLOWING CODE WAS FULLY WRITTEN BY DEEPSEEK R1
def separate_string(text):
    parsed_tags = defaultdict(list)
    parsed_text_segments = []
    current_pos = 0
    length = len(text)

    while current_pos < length:
        # Look for the next code block start or tag opening
        code_match = re.search(r'```', text[current_pos:], re.DOTALL)
        tag_match = re.search(r'<([a-zA-Z-]+)>', text[current_pos:])

        # Determine which comes first
        candidates = []
        if code_match:
            candidates.append((code_match.start(), 'code'))
        if tag_match:
            candidates.append((tag_match.start(), 'tag'))

        if not candidates:
            # No more code blocks or tags; append remaining text
            parsed_text_segments.append(text[current_pos:])
            break

        # Sort to find the nearest candidate
        candidates.sort()
        first_offset, first_type = candidates[0]

        # Append text from current_pos up to the first candidate
        if first_offset > 0:
            parsed_text_segments.append(text[current_pos:current_pos + first_offset])

        if first_type == 'code':
            # Process code block
            code_start = current_pos + first_offset
            code_end = text.find('```', code_start + 3)
            if code_end == -1:
                # No closing backticks; take the rest
                parsed_text_segments.append(text[code_start:])
                current_pos = length
            else:
                # Include the closing backticks
                parsed_text_segments.append(text[code_start:code_end + 3])
                current_pos = code_end + 3
        else:
            # Process tag
            tag_name = tag_match.group(1)
            tag_start = current_pos + tag_match.start()
            tag_full = tag_match.group(0)
            tag_end_abs = tag_start + len(tag_full)
            closing_tag = f'</{tag_name}>'
            closing_pos = text.find(closing_tag, tag_end_abs)

            if closing_pos == -1:
                # No closing tag; add the opening tag as text
                parsed_text_segments.append(tag_full)
                current_pos = tag_end_abs
            else:
                # Extract content and update parsed_tags
                content = text[tag_end_abs:closing_pos]
                if tag_name not in parsed_tags:
                    parsed_tags[tag_name] = []
                parsed_tags[tag_name].append(content)
                current_pos = closing_pos + len(closing_tag)

    # Combine all text segments
    parsed_text = ''.join(parsed_text_segments)
    return parsed_tags, parsed_text

from transformers import LlamaTokenizer
tokenizer: LlamaTokenizer = LlamaTokenizer.from_pretrained('openlm-research/open_llama_3b_v2', cache_dir="tokenizer")

def count_tokens(text: str):
    output = tokenizer.tokenize(text)
    return len(output)