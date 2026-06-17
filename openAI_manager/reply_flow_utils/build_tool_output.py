import json
def build_tool_output(tool_call, output):
    if not isinstance(output, str):
        output = json.dumps(output, default=str)

    return {
        "type": "function_call_output",
        "call_id": tool_call.call_id,
        "output": output,
    }
