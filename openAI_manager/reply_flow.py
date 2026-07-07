from tools.search_tools import FireCrawlTool
from tools.use_desktop_tools import DesktopTools
import json
from .request_llm_reply import build_input_messages, request_reply
from .reply_flow_utils import (
    add_response_output,
    build_tool_output,
    get_function_calls,
    notify_tool_calls,
    read_memory,
    record_final_response,
)


def request_reply_with_tool_loop(
    prompt,
    client,
    model,
    chat_history_manager,
    on_tool_call=None,
):
    search_tool = FireCrawlTool()
    desktop_tool = DesktopTools()
    input_messages = build_input_messages(prompt)

    while True:
        response_output, response_text = request_reply(
            input_messages,
            client,
            model,
        )

        # Pull out only the function/tool call items from the model response.
        # Normal text output is ignored here because only tool calls need routing.
        tool_calls = get_function_calls(response_output)

        # Notify the CLI/UI that the model requested a tool.
        # This only reports the tool name for display; it does not run the tool.
        notify_tool_calls(tool_calls, on_tool_call)

        if not tool_calls:
            record_final_response(
                chat_history_manager,
                prompt,
                response_text,
            )
            return response_text

        input_messages = add_response_output(
            input_messages,
            response_output,
        )

        for tool_call in tool_calls:
            tool_output = run_tool_call(
                tool_call,
                search_tool,
                desktop_tool,
                chat_history_manager,
            )
            chat_history_manager.store_tool_call_history(tool_call.name, tool_call.call_id, tool_output, "tool_response")
            input_messages.append(build_tool_output(tool_call, tool_output))
            notify_tool_finished(on_tool_call, tool_call.name)


def run_tool_call(tool_call, search_tool, desktop_tool,  chat_history_manager):
    try:
        if tool_call.name == "search_web":
            arguments = parse_tool_arguments(tool_call)
            return search_tool.search(arguments["queries"])

        if tool_call.name == "read_memory":
            arguments = parse_tool_arguments(tool_call)
            return read_memory(chat_history_manager, include_tool_outputs=arguments["include_tool_outputs"])
        

        if tool_call.name == "read_website":
            arguments = parse_tool_arguments(tool_call)
            return search_tool.crawl(arguments["websites"])

        if tool_call.name == "write_to_file":
            arguments = parse_tool_arguments(tool_call)
            return desktop_tool.write_to_file(
                arguments["filePath"],
                arguments["content"],
                arguments["filename"],
            )

        if tool_call.name == "read_file":
            arguments = parse_tool_arguments(tool_call)
            return desktop_tool.read_file(arguments["filePath"])
        if tool_call.name == "run_command":
            arguments = parse_tool_arguments(tool_call)
            return desktop_tool.check_and_run_shell_command(arguments["command"])

        return {"error": f"Unsupported tool call: {tool_call.name}"}
    except Exception as e:
        return {"error": f"{tool_call.name} failed: {e}"}


def parse_tool_arguments(tool_call):
    if not tool_call.arguments:
        return {}

    return json.loads(tool_call.arguments)


def notify_tool_finished(on_tool_call, tool_name):
    if on_tool_call is None:
        return

    try:
        on_tool_call(tool_name, "finished")
    except TypeError:
        pass
