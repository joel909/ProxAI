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
        if read_memory_call is None:
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

        memory_output = read_memory(
            storage_service,
            chat_history_file,
        )

        input_messages.append(
            build_tool_output(
                read_memory_call,
                memory_output,
            )
        )
