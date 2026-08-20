import subprocess

from inputs.terminal_ui import LoadingSpinner


def list_docker_containers():
    spinner = LoadingSpinner("Fetching Docker containers")
    try:
        spinner.start()
        result = subprocess.run(
            ["docker", "ps", "-a"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to list Docker containers. Error: {result.stderr}")
        return result.stdout
    finally:
        spinner.stop()
