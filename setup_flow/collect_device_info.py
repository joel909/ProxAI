from ..inputs import LoadingSpinner,create_tool_call_handler
from ..openAI_manager.info_collector_agent.build_input_messages import build_input_messages
from ..openAI_manager.info_collector_agent.info_collecter_agent_tools import info_collector_agent_tools
def collect_device_info(llm_manager, chat_history_manager):
    while True:
        spinner = LoadingSpinner()
        spinner.start()
        show_tool_call = create_tool_call_handler(spinner)
        try:
            prompt = "Please Begin the process"
            response = llm_manager.request_llm_reply(
                prompt,
                on_tool_call=show_tool_call,
                custom_build_input_messages_function=build_input_messages,
                custom_available_tools=info_collector_agent_tools,
            )
        except Exception as e:
            spinner.stop()
            print(f"Error collecting device info: {e}")
            return None
        finally:
            spinner.stop()


    return device_info
