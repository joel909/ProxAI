def build_tool_output(tool_call, output):
    return {
        "type": "function_call_output",
        "call_id": tool_call.call_id,
        "output": output,
    }
