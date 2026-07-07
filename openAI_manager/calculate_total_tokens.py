import tiktoken


def calculate_total_tokens(message, model):
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        try:
            encoding = tiktoken.get_encoding("o200k_base")
        except Exception:
            return estimate_tokens_without_tokenizer(message)

    encoded_message = encoding.encode(message)
    total_tokens = len(encoded_message)
    return total_tokens


def estimate_tokens_without_tokenizer(message):
    return max(1, len(message) // 4)
