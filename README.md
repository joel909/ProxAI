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

## Requirements

- Linux with Python 3.10 or newer
- The Python `venv` module (`python3-venv` on Debian and Ubuntu)
- An OpenAI API key for the currently supported provider
- Optional API credentials for the tools you want ProxAI to use

ProxAI uses a project-local virtual environment. Do not copy or commit the
`.venv` directory between machines.

## Install on Linux or a virtual machine

Clone the repository and enter its directory:

```bash
git clone https://github.com/joel909/ProxAI.git
cd ProxAI
```

The recommended setup command creates `.venv`, installs the dependencies, and
generates `manifest.json` for the current machine:

```bash
./setup_flow/setup.sh
```

The equivalent manual setup is:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python setup_flow/generate_manifest.py
```

Install the requirements before starting ProxAI. Running `main.py` first will
produce errors such as `ModuleNotFoundError: No module named 'openai'`.

Use the virtual environment directly rather than `sudo`. This keeps installed
packages, configuration, and generated files owned by the current user.

## Complete the basic application setup

Start the terminal application:

```bash
./setup_flow/run.sh
```

You can also run the same application directly:

```bash
.venv/bin/python main.py
```

On the first run:

1. Select **Start setup**.
2. Select **OpenAI** as the provider.
3. Paste your OpenAI API key.
4. Select the model and complete the remaining prompts.
5. Start ProxAI again after the setup finishes.

This only completes the basic model-provider setup. External tools have their
own credentials and must be configured separately.

## Configure individual tools

Start the terminal application and enter this command in the ProxAI prompt:

```text
/setup-tools
```

Choose a tool and follow its prompts. ProxAI validates each credential before
saving it.

### Firecrawl

Create an API key in the Firecrawl dashboard. Select **Firecrawl** under
`/setup-tools` and paste only the API key. ProxAI validates it with a small
search. If validation fails, check that the key is complete and active, has
available usage, and that the machine can reach Firecrawl.

### GitHub

Open GitHub **Settings > Developer settings > Personal access tokens > Tokens
(classic)** and generate a classic personal access token. Give it an expiration
and enable the `repo` scope if ProxAI needs access to private repositories. Then
select **GitHub** under `/setup-tools` and paste only the token.

Tokens can be created at
<https://github.com/settings/personal-access-tokens/new>.

### Cloudflare

Open Cloudflare **Profile > API Tokens** and create a custom token with:

- **Account > Cloudflare Tunnel > Edit**
- **Zone > DNS > Edit**
- Access to the intended Cloudflare account and zone resources

Select **Cloudflare** under `/setup-tools` and paste the raw API token without
`Bearer` or `Authorization:`. ProxAI validates authentication, Tunnel access,
DNS access, and edit permissions. It then saves the selected account ID, zone
ID, and zone name with the credential.

An active Cloudflare domain is required. Cloudflare setup fails if the token
cannot access an active zone.

## Where configuration is stored

Provider keys, tool credentials, Cloudflare account and zone details, and chat
history are stored in `assistant.db` in the repository directory. This SQLite
database contains secrets in plain application storage, so do not commit, copy,
publish, or share it. The generated `manifest.json` contains information about
the current machine. Both files are excluded by `.gitignore`.

## Use the terminal application

Run ProxAI in the terminal with:

```bash
./setup_flow/run.sh
```

Use the terminal primarily for the initial provider setup, `/setup-tools`,
configuration changes, and testing. After setup, the web dashboard is the
easier interface for normal conversations and deployments.

## Open the web dashboard

The dashboard uses the provider and tool credentials configured through the
terminal. A dashboard visitor does not need to enter a separate OpenAI API key.
It provides formatted chat history, shows tool calls while they run, and allows
existing conversations to be reopened and continued.

Start it from the repository directory:

```bash
./setup_flow/run_dashboard.sh
```

Then open <http://127.0.0.1:7681> in a browser on the same machine.

If ProxAI is running on a remote virtual machine, keep the dashboard bound to
loopback and create an SSH tunnel from your computer:

```bash
ssh -L 7681:127.0.0.1:7681 ubuntu@VM_PUBLIC_IP
```

Keep that SSH connection open, then visit <http://127.0.0.1:7681> on your own
computer.

### Run the dashboard in the background

For a detached process that remains available after the SSH session closes:

```bash
PROXAI_DASHBOARD_HOST=127.0.0.1 \
./setup_flow/run_dashboard_detached.sh
```

Dashboard output is written to `/tmp/proxai-dashboard.log`, and its process ID
is stored in `/tmp/proxai-dashboard.pid`.

```bash
tail -f /tmp/proxai-dashboard.log
```

### Publish the dashboard through Cloudflare

Point a Cloudflare Tunnel service at `http://127.0.0.1:7681`. Protect the public
hostname with Cloudflare Access, then require the Access assertion in ProxAI:

```bash
PROXAI_DASHBOARD_HOST=127.0.0.1 \
PROXAI_REQUIRE_CLOUDFLARE_ACCESS=true \
PROXAI_ALLOWED_EMAILS=you@example.com \
./setup_flow/run_dashboard_detached.sh
```

`PROXAI_ALLOWED_EMAILS` is optional and accepts the email addresses allowed by
the dashboard's Cloudflare Access check.

The web dashboard always approves command and file-write confirmations so that
non-interactive deployments do not fail with `EOF when reading a line`. Treat
dashboard access as terminal access: expose it only to trusted users, protect it
with Cloudflare Access, use narrowly scoped credentials, and run it on an
isolated machine without sensitive files or repositories.

## Troubleshooting

- **`No module named 'openai'`:** activate `.venv` and run
  `python -m pip install -r requirements.txt`.
- **The setup screen appears again:** finish **Start setup**, enter a valid API
  key, and then restart the terminal application.
- **The dashboard refuses the connection:** make sure
  `./setup_flow/run_dashboard.sh` is still running and listening on port `7681`.
- **A detached dashboard does not start:** inspect
  `/tmp/proxai-dashboard.log`.
- **Tool setup fails:** run `/setup-tools` again and review the permission or
  validation message for that provider.
