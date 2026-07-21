# ProxAI

I started ProxAI because I wanted to learn AI by building something practical, not just reading about it.

ProxAI is my work-in-progress project for integrating LLMs with my own tools and workflows so I can make everyday tasks faster, smarter, and more useful. The focus is on building a real system around AI, not just a generic chatbot or a vague "AI agent" demo.

## What I am building

- A place to experiment with AI-powered tooling
- A setup for connecting models to my own processes
- A foundation for turning ideas into usable workflows

## Status

- Early work in progress
- Still being shaped as I learn and build

## Run on Linux

ProxAI uses a project-local Python environment, so it does not depend on a
machine-specific path or username. Python 3.10 or newer is required.

After cloning the repository, run:

```bash
./setup_flow/setup.sh
./setup_flow/run.sh
```

`setup_flow/setup.sh` creates `.venv`, installs the packages in
`requirements.txt`, and generates `manifest.json` for the current device. Run
it again whenever the dependencies or device configuration change. The `.venv`
directory is local to each machine and should not be copied or committed.

If your distribution reports that the `venv` module is missing, install its
Python venv package (for example, `python3-venv` on Debian or Ubuntu) and rerun
the setup command.

## Notes

More details will be added as the project grows.
