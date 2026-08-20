from inputs.terminal_ui import LoadingSpinner, create_tool_call_handler
from var_files import GITHUB_REPOS_DIR, set_active_repository_path
def create_docker_config_file(repo_path,llm_manager):
    active_path = set_active_repository_path(repo_path)
    spinner = LoadingSpinner("Generating DockerConfig for Repo... ")
    show_tool_call = create_tool_call_handler(spinner)
    return llm_manager.request_llm_reply(
                "Please repair the failed manifest generator.",
                on_tool_call=show_tool_call,
                custom_build_input_messages_function=build_input_messages,
                custom_available_tools=info_collector_agent_tools,
            )
    