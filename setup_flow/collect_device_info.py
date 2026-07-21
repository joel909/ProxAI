from inputs import (
    GREEN,
    LoadingSpinner,
    RESET,
    YELLOW,
    create_tool_call_handler,
    print_assistant_response,
    select_menu,
)
from server_info_collector import build_input_messages, info_collector_agent_tools

from .generate_manifest import generate_manifests


def generate_new_manifest_generating_code(llm_manager, show_tool_call, spinner):
    """Ask the fallback AI agent to repair the manifest generator."""
    try:
        spinner.start()
        return llm_manager.request_llm_reply(
            "Please repair the failed manifest generator.",
            on_tool_call=show_tool_call,
            custom_build_input_messages_function=build_input_messages,
            custom_available_tools=info_collector_agent_tools,
        )
    except Exception as exc:
        print(f"Error collecting device info: {exc}")
        return None
    finally:
        spinner.stop()


def collect_device_info(llm_manager, is_setup_completed):
    while True:
        spinner = LoadingSpinner()
        show_tool_call = create_tool_call_handler(spinner)
        manifest_error = None

        try:
            spinner.start()
            generate_manifests()
        except Exception as exc:
            manifest_error = exc
        finally:
            spinner.stop()

        if manifest_error is None:
            if is_setup_completed():
                print(f"{GREEN}Setup is complete. Please start the application again{RESET}")
                return
            manifest_error = RuntimeError("manifest.json was not created")

        print(f"{YELLOW}Error generating manifest.json: {manifest_error}.{RESET}")
        setup_action = select_menu(
            ["Fix with AI", "Exit"],
            "Would you like ProxAI's AI agent to help fix the setup?",
        )
        if setup_action == "Exit":
            print(f"{YELLOW}Setup cancelled.{RESET}")
            return

        response = generate_new_manifest_generating_code(
            llm_manager,
            show_tool_call,
            spinner,
        )
        if response is None:
            print(f"{YELLOW}AI repair was cancelled or failed. Retrying manifest generation.{RESET}")
            continue

        if is_setup_completed():
            print(f"{GREEN}System info generation is complete.{RESET}")
            return

        print_assistant_response(response)
