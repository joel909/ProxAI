from tools.github.fetch_repos import fetch_repos
from tools.github.fetch_pre_cloned_repos import fetch_pre_cloned_repos
from tools.github.clone_repo import clone_github_repo, normalize_github_repo
from tools.github.explore_repository import explore_repository
from tools.github.pull_repo import pull_github_repo
from tools.github.unset_repository import unset_repository
from tools.docker import list_docker_containers
from tools.cloudflare_tunnels.list_cloudflare_domains import list_cloudflare_domains
from storage.tool_credentials import get_tool_api_key, get_tool_help

from .reply_flow_utils import read_memory
import json
from server_info_collector import (
    ask_question,
    ask_question_with_options,
    save_device_details,
)
from pathlib import Path
from var_files import GITHUB_REPOS_DIR

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

        if tool_call.name == "tool_help":
            arguments = parse_tool_arguments(tool_call)
            return get_tool_help(arguments["tool"])
        

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
        if tool_call.name == "read_manifest_code":
            arguments = parse_tool_arguments(tool_call)
            return desktop_tool.read_file(str(MANIFEST_GENERATOR_DIR / "generate_manifest.py"))
        
        if tool_call.name == "list_github_repos":
            PAT = get_tool_api_key("github")
            return fetch_repos(PAT)
        if tool_call.name == "fetched_pre_cloned_repos":
            return fetch_pre_cloned_repos()
        if tool_call.name == "pull_github_repo":
            arguments = parse_tool_arguments(tool_call)
            return pull_github_repo(arguments["repo_name"])
        if tool_call.name == "clone_github_repo":
            arguments = parse_tool_arguments(tool_call)
            PAT = get_tool_api_key("github")
            repo_url = arguments["repo_url"]
            repo_name = normalize_github_repo(repo_url)
            clone_root = GITHUB_REPOS_DIR
            clone_root.mkdir(parents=True, exist_ok=True)
            destination = clone_root / repo_name.rsplit("/", 1)[-1]
            return clone_github_repo(PAT, repo_name, str(destination))
        if tool_call.name == "list_docker_containers":
            return list_docker_containers()
        if tool_call.name == "list_cloudflare_domains":
            return list_cloudflare_domains()
        if tool_call.name == "explore_repository":
            arguments = parse_tool_arguments(tool_call)
            return explore_repository(arguments["repo_name"])
        if tool_call.name == "unset_repository":
            return unset_repository()
        if tool_call.name == "create_cloudflare_tunnel":
            arguments = parse_tool_arguments(tool_call)
            from tools.cloudflare_tunnels.create_cloudflare_tunnel import create_cloudflare_tunnel
            return create_cloudflare_tunnel(arguments["tunnel_name"])
        
        return {"error": f"Unsupported tool call: {tool_call.name}"}
    except Exception as e:
        return {"error": f"{tool_call.name} failed: {e}"}
