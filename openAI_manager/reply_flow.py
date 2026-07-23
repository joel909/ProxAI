from openAI_manager.check_for_tool_calling import check_for_tool_calling
from tools.search_tools import FireCrawlTool
from tools.use_desktop_tools import DesktopTools
from .request_llm_reply import build_input_messages, request_reply
from .reply_flow_utils import (
    add_response_output,
    build_tool_output,
    get_function_calls,
    notify_tool_calls,
    record_final_response,
)




def request_reply_with_tool_loop(
    prompt,
    client,
    model,
    system_configuration,
    chat_history_manager,
    warning_token_limit=None,
    on_tool_call=None,
    build_input_messages_function=build_input_messages,
    custom_available_tools=None,
):
    search_tool = FireCrawlTool()
    desktop_tool = DesktopTools()
    input_messages = build_input_messages_function(prompt,system_configuration)

    while True:
        response_output, response_text = request_reply(
            input_messages,
            client,
            model,
            warning_token_limit,
            custom_available_tools=custom_available_tools,
        )

        if response_text is None:
            return None

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
            tool_output = check_for_tool_calling(
                tool_call,
                search_tool,
                desktop_tool,
                chat_history_manager,
            )
            chat_history_manager.store_tool_call_history(tool_call.name, tool_call.call_id, tool_output, "tool_response")
            input_messages.append(build_tool_output(tool_call, tool_output))
            notify_tool_finished(on_tool_call, tool_call.name)


def notify_tool_finished(on_tool_call, tool_name):
    if on_tool_call is None:
        return

    try:
        on_tool_call(tool_name, "finished")
    except TypeError:
        pass
