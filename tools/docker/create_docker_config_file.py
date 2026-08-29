from inputs.terminal_ui import LoadingSpinner, create_tool_call_handler
from tools.github.explore_repository import explore_repository

from .build_input_messages_docker_config_generation import build_input_messages


DOCKER_AGENT_TOOL_NAMES = {
    "read_memory",
    "search_web",
    "read_website",
    "write_to_file",
    "run_command",
    "read_file",
    "list_docker_containers",
    "create_cloudflare_tunnel",
    "update_cloudflare_tunnel_and_domain",
    "tool_help",
}


def get_docker_agent_tools():
    # Import lazily to avoid a cycle while the top-level tool registry is loading.
    from openAI_manager.request_llm_reply_with_tools_list import tools

    return [tool for tool in tools if tool["name"] in DOCKER_AGENT_TOOL_NAMES]


def build_docker_file_agent(
    repo_name,
    llm_manager,
    system_configuration=None,
    on_tool_call=None,
):
    """Run the Docker specialist agent against an already-cloned repository."""
    repository = explore_repository(repo_name)
    if not repository["success"]:
        return repository

    spinner = None
    show_tool_call = on_tool_call
    if show_tool_call is None:
        spinner = LoadingSpinner("Docker agent working... ")
        show_tool_call = create_tool_call_handler(spinner)

    try:
        if spinner is not None:
            spinner.start()
        return llm_manager.request_llm_reply(
            (
                f"Build and verify the Docker deployment for repository '{repo_name}' "
                f"at {repository['path']}."
            ),
            system_configuration=system_configuration,
            on_tool_call=show_tool_call,
            custom_build_input_messages_function=build_input_messages,
            custom_available_tools=get_docker_agent_tools(),
        )
    finally:
        if spinner is not None:
            spinner.stop()


# Preserve the old callable name for code that already imports it.
create_docker_config_file = build_docker_file_agent
