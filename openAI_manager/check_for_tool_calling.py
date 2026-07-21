from .reply_flow_utils import read_memory
import json
from server_info_collector import (
    ask_question,
    ask_question_with_options,
    save_device_details,
)
from pathlib import Path


def parse_tool_arguments(tool_call):
    if not tool_call.arguments:
        return {}
    return json.loads(tool_call.arguments)

def check_for_tool_calling(tool_call, search_tool, desktop_tool,  chat_history_manager):
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    MANIFEST_GENERATOR_DIR = PROJECT_ROOT / "setup_flow"
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
        if tool_call.name == "ask_question_with_options":
            arguments = parse_tool_arguments(tool_call)
            return ask_question_with_options(
                arguments["question"],
                arguments["options"],
            )
        if tool_call.name == "ask_question":
            arguments = parse_tool_arguments(tool_call)
            return ask_question(arguments["question"])
        if tool_call.name == "save_device_details":
            arguments = parse_tool_arguments(tool_call)
            return save_device_details(arguments["data"])

        if tool_call.name == "edit_manifest_code":
            arguments = parse_tool_arguments(tool_call)
            return desktop_tool.write_to_file(
                str(MANIFEST_GENERATOR_DIR),
                arguments["content"],
                "generate_manifest.py",
            )

        return {"error": f"Unsupported tool call: {tool_call.name}"}
    except Exception as e:
        return {"error": f"{tool_call.name} failed: {e}"}