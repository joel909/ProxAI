#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PROXAI_PROJECT_ROOT="$SCRIPT_DIR"

python3 <<'PY'
import json
import os
import platform
import re
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(os.environ["PROXAI_PROJECT_ROOT"])
MANIFEST_FILE = PROJECT_ROOT / "manifest.json"


def run(command, timeout=6):
    try:
        completed = subprocess.run(
            command,
            shell=True,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except Exception as exc:
        return {
            "command": command,
            "ok": False,
            "stdout": "",
            "stderr": str(exc),
            "returncode": None,
        }

    return {
        "command": command,
        "ok": completed.returncode == 0,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "returncode": completed.returncode,
    }


def first_stdout(*commands, timeout=6):
    for command in commands:
        result = run(command, timeout=timeout)
        if result["ok"] and result["stdout"]:
            return result["stdout"]
    return None


def read_file(path):
    try:
        value = Path(path).read_text(encoding="utf-8").strip()
    except Exception:
        return None
    return value or None


def parse_os_release():
    os_release = {}
    try:
        for line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            os_release[key] = value.strip().strip('"')
    except Exception:
        pass
    return os_release


def parse_ip_addresses(ip_output):
    private_ipv4 = []
    private_ipv6 = []
    global_ipv6 = []

    for line in ip_output.splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue
        interface = parts[1]
        family = parts[2]
        address = parts[3]
        if family == "inet":
            private_ipv4.append(f"{address} on {interface}")
        elif family == "inet6":
            if address.startswith("fe80:") or address.startswith("::1"):
                private_ipv6.append(f"{address} on {interface}")
            else:
                global_ipv6.append(f"{address} on {interface}")

    return private_ipv4, private_ipv6, global_ipv6


def parse_default_gateway(route_output):
    for line in route_output.splitlines():
        if not line.startswith("default "):
            continue
        match = re.search(r"via\s+(\S+)", line)
        if match:
            return match.group(1)
    return None


def parse_listening_ports(ss_output, protocol):
    ports = []
    for line in ss_output.splitlines():
        if line.startswith("Netid") or line.startswith("State") or not line.strip():
            continue
        columns = line.split()
        if len(columns) < 4:
            continue
        ports.append(
            {
                "protocol": protocol,
                "local_address": columns[3],
                "process": " ".join(columns[5:]) if len(columns) > 5 else None,
            }
        )
    return ports


def command_stdout(command_map):
    return {name: result["stdout"] for name, result in command_map.items()}


commands = {
    "hostname": run("hostname"),
    "os": run("uname -a"),
    "ip_addr": run("ip -brief addr"),
    "ip_route": run("ip route"),
    "ss_tcp": run("ss -H -tlnp"),
    "ss_udp": run("ss -H -ulnp"),
    "nmcli_devices": run("nmcli device status"),
    "nmcli_connections": run("nmcli connection show --active"),
    "ufw": run("ufw status"),
    "docker": run("docker --version"),
    "docker_ps": run("docker ps --format '{{.Names}} {{.Image}} {{.Ports}}'"),
    "docker_compose": run("docker-compose --version"),
    "node": run("node --version"),
    "npm": run("npm --version"),
    "python3": run("python3 --version"),
    "psql": run("psql --version"),
    "git": run("git --version"),
    "ollama": run("ollama --version"),
    "smbd": run("smbd --version"),
    "systemctl_services": run(
        "systemctl list-units --type=service --state=running --no-pager --plain"
    ),
    "lscpu": run("lscpu"),
    "free": run("free -h"),
    "lsblk": run("lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS,MODEL"),
    "virt": run("systemd-detect-virt"),
}

public_ipv4 = first_stdout(
    "curl -4 -fsS --max-time 4 https://api.ipify.org",
    "curl -4 -fsS --max-time 4 https://ifconfig.me/ip",
    timeout=6,
)
public_ipv6 = first_stdout(
    "curl -6 -fsS --max-time 4 https://api64.ipify.org",
    "curl -6 -fsS --max-time 4 https://ifconfig.me/ip",
    timeout=6,
)

hostname = commands["hostname"]["stdout"] or socket.gethostname()
os_release = parse_os_release()
private_ipv4, private_ipv6, global_ipv6 = parse_ip_addresses(commands["ip_addr"]["stdout"])
default_gateway = parse_default_gateway(commands["ip_route"]["stdout"])
tcp_ports = parse_listening_ports(commands["ss_tcp"]["stdout"], "tcp")
udp_ports = parse_listening_ports(commands["ss_udp"]["stdout"], "udp")

vendor = read_file("/sys/class/dmi/id/sys_vendor")
model = read_file("/sys/class/dmi/id/product_name")
cpu = first_stdout("lscpu | awk -F: '/Model name/ {gsub(/^[ \\t]+/, \"\", $2); print $2; exit}'")
virt = commands["virt"]["stdout"] if commands["virt"]["ok"] else "none"

manifest = {
    "hostname": hostname,
    "deployment_type": "unknown",
    "exposure": "unknown; generated from local read-only commands",
    "provider": " ".join(part for part in [vendor, model] if part) or "unknown",
    "is_public": None,
    "public_ipv4": public_ipv4,
    "public_ipv6": public_ipv6,
    "private_ipv4": private_ipv4,
    "private_ipv6": private_ipv6,
    "global_ipv6_addresses": global_ipv6,
    "ip_static": "unknown; inspect ip_route and NetworkManager command output",
    "ip_confidence": "local command generated; public reachability was not externally scanned",
    "open_ports": {
        "tcp": tcp_ports,
        "udp": udp_ports,
    },
    "public_ports": [],
    "services_tools": {
        "os": os_release.get("PRETTY_NAME") or platform.platform(),
        "kernel": platform.release(),
        "networking": command_stdout(
            {
                "ip_route": commands["ip_route"],
                "nmcli_devices": commands["nmcli_devices"],
                "nmcli_connections": commands["nmcli_connections"],
            }
        ),
        "firewall": commands["ufw"]["stdout"] or commands["ufw"]["stderr"] or "unknown",
        "docker": commands["docker"]["stdout"] or None,
        "docker_running_containers": commands["docker_ps"]["stdout"] or "",
        "docker_compose": commands["docker_compose"]["stdout"] or None,
        "node": commands["node"]["stdout"] or None,
        "npm": commands["npm"]["stdout"] or None,
        "python3": commands["python3"]["stdout"] or None,
        "postgres_client": commands["psql"]["stdout"] or None,
        "git": commands["git"]["stdout"] or None,
        "ollama": commands["ollama"]["stdout"] or None,
        "samba": commands["smbd"]["stdout"] or None,
        "running_services": commands["systemctl_services"]["stdout"],
    },
    "hardware": {
        "vendor": vendor,
        "model": model,
        "virtualization_detected": virt,
        "cpu": cpu,
        "memory": commands["free"]["stdout"],
        "disk": commands["lsblk"]["stdout"],
        "lscpu": commands["lscpu"]["stdout"],
    },
    "network_interfaces": {
        "default_gateway": default_gateway,
        "ip_addr": commands["ip_addr"]["stdout"],
        "ip_route": commands["ip_route"]["stdout"],
        "nmcli_devices": commands["nmcli_devices"]["stdout"],
        "nmcli_connections": commands["nmcli_connections"]["stdout"],
    },
    "notes": [
        "Generated by generate_manifests.sh.",
        "The script writes manifest.json with the correct spelling.",
        "public_ports is empty because the script does not perform an external inbound port scan.",
        "deployment_type, exposure, is_public, and ip_static may require user confirmation.",
    ],
    "raw_qa_log": [],
    "raw_command_outputs": commands,
    "last_updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
}

temp_file = MANIFEST_FILE.with_suffix(".json.tmp")
temp_file.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
json.loads(temp_file.read_text(encoding="utf-8"))
temp_file.replace(MANIFEST_FILE)

print(f"success manifest.json generated at {MANIFEST_FILE}")
PY
