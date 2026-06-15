def find_tool_call(tool_calls, tool_name):
    for tool_call in tool_calls:
        if tool_call.name == tool_name:
            return tool_call

    return None
