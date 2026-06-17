def notify_tool_calls(tool_calls, on_tool_call):
    if on_tool_call is None:
        return

    for tool_call in tool_calls:
        try:
            on_tool_call(tool_call.name, "started")
        except TypeError:
            on_tool_call(tool_call.name)
