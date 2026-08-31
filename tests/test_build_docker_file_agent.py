import unittest
from types import SimpleNamespace
from unittest import mock

from openAI_manager.request_llm_reply_with_tools_list import (
    build_input_messages as build_parent_messages,
)
from openAI_manager.request_llm_reply_with_tools_list import tools
from openAI_manager.service import OpenAIManager
from openAI_manager.tool_calling_logic import check_for_tool_calling
from tools.docker import create_docker_config_file as docker_agent
from tools.docker.build_input_messages_docker_config_generation import (
    build_input_messages,
)


class BuildDockerFileAgentTests(unittest.TestCase):
    def test_parent_agent_is_told_about_docker_agent_tool(self):
        definition = next(
            tool for tool in tools if tool["name"] == "build_docker_file_agent"
        )
        self.assertEqual(definition["parameters"]["required"], ["repo_name"])

        messages = build_parent_messages("deploy demo", "system details")
        self.assertTrue(
            any(
                "MUST call build_docker_file_agent" in message["content"]
                for message in messages
            )
        )
        self.assertIn("must always call", definition["description"].lower())
        self.assertIn(
            "cloudflare publication is required",
            definition["description"].lower(),
        )

    def test_docker_prompt_keeps_system_configuration_as_system_context(self):
        messages = build_input_messages("build demo", "arm64 with Docker")

        self.assertEqual(messages[-1], {"role": "user", "content": "build demo"})
        self.assertTrue(
            any(
                message["role"] == "system"
                and "arm64 with Docker" in message["content"]
                for message in messages
            )
        )
        self.assertTrue(
            any(
                "create_cloudflare_tunnel" in message["content"]
                for message in messages
            )
        )
        self.assertTrue(
            any(
                "primary objective" in message["content"]
                and "Cloudflare Tunnel" in message["content"]
                and "public URL is reachable" in message["content"]
                for message in messages
            )
        )
        self.assertTrue(
            any(
                "mandatory for every application deployment without exception"
                in message["content"]
                and "assigned a domain" in message["content"]
                and "local-only" in message["content"]
                for message in messages
            )
        )

    def test_specialist_tool_set_is_bounded_and_not_recursive(self):
        names = {tool["name"] for tool in docker_agent.get_docker_agent_tools()}

        self.assertIn("read_file", names)
        self.assertIn("write_to_file", names)
        self.assertIn("run_command", names)
        self.assertIn("create_cloudflare_tunnel", names)
        self.assertNotIn("build_docker_file_agent", names)

    def test_agent_selects_repository_and_starts_custom_tool_loop(self):
        manager = mock.Mock()
        manager.request_llm_reply.return_value = "deployment complete"
        spinner = mock.Mock()

        with (
            mock.patch.object(
                docker_agent,
                "explore_repository",
                return_value={
                    "success": True,
                    "repo_name": "demo",
                    "path": "/repos/demo",
                },
            ),
            mock.patch.object(docker_agent, "LoadingSpinner", return_value=spinner),
            mock.patch.object(
                docker_agent,
                "get_docker_agent_tools",
                return_value=[{"name": "read_file"}],
            ),
        ):
            result = docker_agent.build_docker_file_agent(
                "demo",
                manager,
                system_configuration="server config",
            )

        self.assertEqual(result, "deployment complete")
        request = manager.request_llm_reply.call_args
        self.assertIn("repository 'demo'", request.args[0])
        self.assertEqual(request.kwargs["system_configuration"], "server config")
        self.assertIs(
            request.kwargs["custom_build_input_messages_function"],
            build_input_messages,
        )
        spinner.start.assert_called_once()
        spinner.stop.assert_called_once()

    def test_dispatcher_runs_docker_agent_tool(self):
        runner = mock.Mock(return_value="agent result")
        tool_call = SimpleNamespace(
            name="build_docker_file_agent",
            arguments='{"repo_name": "demo"}',
        )

        result = check_for_tool_calling(
            tool_call,
            search_tool=mock.Mock(),
            desktop_tool=mock.Mock(),
            chat_history_manager=mock.Mock(),
            build_docker_file_agent_runner=runner,
        )

        runner.assert_called_once_with("demo")
        self.assertEqual(result, "agent result")

    def test_custom_agent_loop_receives_system_configuration_and_chat_history(self):
        history = mock.Mock()
        custom_builder = mock.Mock()
        custom_tools = [{"name": "read_file"}]

        with (
            mock.patch("openAI_manager.service.OpenAI"),
            mock.patch(
                "openAI_manager.service.request_reply_with_tool_loop",
                return_value="agent result",
            ) as reply_loop,
        ):
            manager = OpenAIManager("api-key", history, model="gpt-test")
            result = manager.request_llm_reply(
                "agent prompt",
                system_configuration="server config",
                custom_build_input_messages_function=custom_builder,
                custom_available_tools=custom_tools,
            )

        self.assertEqual(result, "agent result")
        call = reply_loop.call_args
        self.assertEqual(call.args[3], "server config")
        self.assertIs(call.args[4], history)
        self.assertIs(call.kwargs["build_input_messages_function"], custom_builder)
        self.assertIs(call.kwargs["custom_available_tools"], custom_tools)


if __name__ == "__main__":
    unittest.main()
