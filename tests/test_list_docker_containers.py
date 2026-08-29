import subprocess
import unittest
from types import SimpleNamespace
from unittest import mock

from openAI_manager.tool_calling_logic import check_for_tool_calling
from openAI_manager.request_llm_reply_with_tools_list import tools
from tools.docker.list_docker_containers import list_docker_containers


class ListDockerContainersTests(unittest.TestCase):
    def test_tool_is_available_to_the_llm(self):
        self.assertIn(
            "list_docker_containers",
            {tool["name"] for tool in tools},
        )

    @mock.patch("tools.docker.list_docker_containers.LoadingSpinner")
    @mock.patch("tools.docker.list_docker_containers.subprocess.run")
    def test_returns_raw_docker_ps_output(self, run, spinner):
        run.return_value = subprocess.CompletedProcess(
            args=["docker", "ps", "-a"],
            returncode=0,
            stdout="CONTAINER ID   IMAGE\nabc123         nginx\n",
            stderr="",
        )

        result = list_docker_containers()

        run.assert_called_once_with(
            ["docker", "ps", "-a"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result, "CONTAINER ID   IMAGE\nabc123         nginx\n")
        spinner.return_value.stop.assert_called_once_with()

    def test_dispatcher_calls_docker_handler(self):
        tool_call = SimpleNamespace(name="list_docker_containers", arguments="{}")

        with mock.patch(
            "openAI_manager.tool_calling_logic.list_docker_containers",
            return_value="docker output",
        ) as list_containers:
            result = check_for_tool_calling(
                tool_call,
                search_tool=mock.Mock(),
                desktop_tool=mock.Mock(),
                chat_history_manager=mock.Mock(),
            )

        list_containers.assert_called_once_with()
        self.assertEqual(result, "docker output")


if __name__ == "__main__":
    unittest.main()
