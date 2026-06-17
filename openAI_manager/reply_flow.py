from tools.search_tools import FireCrawlTool
import json
from .request_llm_reply import build_input_messages, request_reply
from .reply_flow_utils import (
    add_response_output,
    build_tool_output,
    find_tool_call,
    get_function_calls,
    notify_tool_calls,
    read_memory,
    record_final_response,
)


def request_reply_with_tool_loop(
    prompt,
    client,
    model,
    storage_service,
    chat_history_file,
    on_tool_call=None,
):
    search_tool = FireCrawlTool()
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

        # Check whether the model asked for the read_memory tool.
        # If found, this gives us the tool call object, including its call_id.
        read_memory_call = find_tool_call(tool_calls, "read_memory")
        search_web = find_tool_call(tool_calls, "search_web")
        if read_memory_call is None and search_web is None:
            record_final_response(
                storage_service,
                chat_history_file,
                prompt,
                response_text,
            )
            return response_text

        input_messages = add_response_output(
            input_messages,
            response_output,
        )

        if search_web is not None:
            # Handle search_web tool call
            try:
                # print("search_web.arguments", json.loads(search_web.arguments))
                search_output = search_tool.search(json.loads(search_web.arguments)["queries"])
                # print("search_output", search_output)
                input_messages.append(
                    build_tool_output(
                        search_web,
                        search_output,
                    )
                )
                notify_tool_finished(on_tool_call, search_web.name)
            except Exception as e:
                print(f"Error occurred while searching: {e}")
                break
        if read_memory_call is not None:
            # Handle read_memory tool call
            try:
                memory_output = read_memory(storage_service,chat_history_file,)
                input_messages.append(
                    build_tool_output(
                        read_memory_call,
                        memory_output,
                    )
                )
                notify_tool_finished(on_tool_call, read_memory_call.name)
            except Exception as e:
                print(f"Error occurred while reading memory: {e}")
                break


def notify_tool_finished(on_tool_call, tool_name):
    if on_tool_call is None:
        return

    try:
        on_tool_call(tool_name, "finished")
    except TypeError:
        pass
