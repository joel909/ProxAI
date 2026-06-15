def get_function_calls(response_output):
    tool_calls = []

    for item in response_output:
        if item.type == "function_call":
            tool_calls.append(item)

    return tool_calls
