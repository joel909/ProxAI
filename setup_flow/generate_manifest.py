import ipaddress
import json
import platform
import re
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_FILE = PROJECT_ROOT / "manifest.json"


def run(command, timeout=6):
    """Run a read-only shell command and return a JSON-serializable result."""
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
            return result["stdout"].splitlines()[0].strip()
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


def parse_hostnamectl(hostnamectl_output):
    values = {}
    for line in hostnamectl_output.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        normalized_key = key.strip().lower().replace(" ", "_").replace("-", "_")
        values[normalized_key] = value.strip()
    return values


def _address_from_token(token):
    token = token.strip().strip(",")
    if not token or token == "dynamic":
        return None
    try:
        return ipaddress.ip_interface(token)
    except ValueError:
        return None


def parse_ip_addresses(ip_output):
    private_ipv4 = []
    private_ipv6 = []
    global_ipv4 = []
    global_ipv6 = []

    for line in ip_output.splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        interface = parts[0]
        for token in parts[2:]:
            parsed = _address_from_token(token)
            if parsed is None:
                continue
            ip = parsed.ip
            entry = f"{parsed} on {interface}"
            if ip.version == 4:
                if ip.is_loopback:
                    continue
                if ip.is_global:
                    global_ipv4.append(entry)
                else:
                    private_ipv4.append(entry)
            elif ip.version == 6:
                if ip.is_loopback:
                    continue
                if ip.is_global:
                    global_ipv6.append(entry)
                else:
                    private_ipv6.append(entry)

    return private_ipv4, private_ipv6, global_ipv4, global_ipv6


def parse_network_interfaces(ip_output):
    interfaces = []
    for line in ip_output.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        addresses = []
        for token in parts[2:]:
            parsed = _address_from_token(token)
            if parsed is None:
                continue
            ip = parsed.ip
            scope = "loopback" if ip.is_loopback else "global" if ip.is_global else "private/link-local"
            addresses.append(
                {
                    "address": str(parsed),
                    "family": "ipv4" if ip.version == 4 else "ipv6",
                    "scope": scope,
                }
            )
        interfaces.append(
            {
                "name": parts[0],
                "state": parts[1],
                "ipv4": [item["address"] for item in addresses if item["family"] == "ipv4"],
                "ipv6": [item["address"] for item in addresses if item["family"] == "ipv6"],
                "addresses": addresses,
            }
        )
    return interfaces


def parse_default_gateway(route_output):
    for line in route_output.splitlines():
        if not line.startswith("default "):
            continue
        match = re.search(r"via\s+(\S+)", line)
        if match:
            return match.group(1)
    return None


def _parse_port(local_address):
    if not local_address:
        return None
    if local_address.startswith("["):
        match = re.search(r"]:(\d+)$", local_address)
        return int(match.group(1)) if match else None
    match = re.search(r":(\d+)$", local_address)
    return int(match.group(1)) if match else None


def _parse_process(process_text):
    if not process_text:
        return None
    names = re.findall(r'"([^"]+)"', process_text)
    pids = re.findall(r"pid=(\d+)", process_text)
    if names or pids:
        return {
            "raw": process_text,
            "names": sorted(set(names)),
            "pids": sorted(set(pids), key=int),
        }
    return {"raw": process_text, "names": [], "pids": []}


def parse_listening_ports(ss_output, protocol):
    ports = []
    for line in ss_output.splitlines():
        if line.startswith("Netid") or line.startswith("State") or not line.strip():
            continue
        columns = line.split()
        if len(columns) < 4:
            continue
        local_address = columns[3]
        process_text = " ".join(columns[5:]) if len(columns) > 5 else ""
        ports.append(
            {
                "protocol": protocol,
                "local_address": local_address,
                "port": _parse_port(local_address),
                "process": process_text or None,
                "process_details": _parse_process(process_text),
            }
        )
    return ports


def command_stdout(command_map):
    return {name: result["stdout"] for name, result in command_map.items()}


def command_summary(result):
    if result["ok"]:
        return result["stdout"] or None
    return None


def detect_provider(vendor, model, hostnamectl_values, commands):
    vendor_model = " ".join(part for part in [vendor, model] if part).strip()
    dmi_text = vendor_model.lower()

    if commands["cloud_aws_instance_id"]["ok"] and commands["cloud_aws_instance_id"]["stdout"]:
        return "Amazon Web Services (EC2 metadata detected)"
    if commands["cloud_azure_instance"]["ok"] and commands["cloud_azure_instance"]["stdout"]:
        return "Microsoft Azure (metadata detected)"
    if commands["cloud_gcp_instance_id"]["ok"] and commands["cloud_gcp_instance_id"]["stdout"]:
        return "Google Cloud Platform (metadata detected)"

    cloud_markers = {
        "amazon": "Amazon Web Services",
        "ec2": "Amazon Web Services",
        "google": "Google Cloud Platform",
        "microsoft corporation virtual machine": "Microsoft Azure / Hyper-V",
        "digitalocean": "DigitalOcean",
        "hetzner": "Hetzner",
        "oracle": "Oracle Cloud / Oracle hardware",
        "qemu": "QEMU/KVM virtual machine",
        "vmware": "VMware virtual machine",
        "xen": "Xen virtual machine",
        "virtualbox": "VirtualBox virtual machine",
        "raspberry pi": "Raspberry Pi",
    }
    for marker, provider in cloud_markers.items():
        if marker in dmi_text:
            return provider

    hardware_vendor = hostnamectl_values.get("hardware_vendor")
    hardware_model = hostnamectl_values.get("hardware_model")
    hostnamectl_hardware = " ".join(
        part for part in [hardware_vendor, hardware_model] if part
    ).strip()
    return vendor_model or hostnamectl_hardware or "unknown"


def infer_deployment_type(provider, hostnamectl_values, commands):
    provider_lower = (provider or "").lower()
    cloud_words = ["aws", "amazon", "azure", "google cloud", "digitalocean", "hetzner", "oracle cloud", "ec2"]
    if any(word in provider_lower for word in cloud_words):
        return "cloud"
    if "raspberry pi" in provider_lower:
        return "home lab"

    chassis = hostnamectl_values.get("chassis", "").lower()
    nmcli_output = commands["nmcli_devices"]["stdout"].lower()
    if chassis in {"laptop", "desktop", "convertible", "tablet"} or " wifi " in nmcli_output:
        return "home lab / workstation"
    if commands["cloud_aws_instance_id"]["ok"] or commands["cloud_azure_instance"]["ok"] or commands["cloud_gcp_instance_id"]["ok"]:
        return "cloud"
    return "unknown"


def local_ips_without_prefix(address_entries):
    ips = set()
    for entry in address_entries:
        address = entry.split(" on ", 1)[0]
        try:
            ips.add(str(ipaddress.ip_interface(address).ip))
        except ValueError:
            continue
    return ips


def infer_exposure(public_ipv4, public_ipv6, global_ipv4, global_ipv6, private_ipv4):
    local_global_ipv4 = local_ips_without_prefix(global_ipv4)
    local_global_ipv6 = local_ips_without_prefix(global_ipv6)

    public_ipv4_is_local = bool(public_ipv4 and public_ipv4 in local_global_ipv4)
    public_ipv6_is_local = bool(public_ipv6 and public_ipv6 in local_global_ipv6)

    if public_ipv4_is_local and public_ipv6_is_local:
        return "public IPv4 and public IPv6 assigned locally", True
    if public_ipv4_is_local:
        return "public IPv4 assigned locally", True
    if public_ipv6_is_local:
        if public_ipv4 and private_ipv4:
            return "public IPv6 assigned locally; IPv4 appears private/NAT with public egress", True
        return "public IPv6 assigned locally", True
    if public_ipv4 or public_ipv6:
        if private_ipv4:
            return "private network with public egress/NAT detected", False
        return "public egress detected; local exposure unknown", None
    if private_ipv4:
        return "private network only detected from local commands", False
    return "unknown; no safe public reachability scan was performed", None


def infer_ip_static(commands):
    route_output = commands["ip_route"]["stdout"]
    ip6_route_output = commands["ip6_route"]["stdout"]
    nmcli_output = "\n".join(
        [commands["nmcli_devices"]["stdout"], commands["nmcli_connections"]["stdout"]]
    ).lower()
    if " proto dhcp" in route_output or " dhcp" in nmcli_output:
        return "dynamic / DHCP detected"
    if " proto ra" in ip6_route_output or " proto ra" in route_output:
        return "dynamic / IPv6 router advertisements detected"
    return "unknown; no DHCP/static configuration was confirmed by safe local commands"


def build_manifest():
    commands = {
        "hostname": run("hostname"),
        "hostnamectl": run("hostnamectl"),
        "os": run("uname -a"),
        "ip_addr": run("ip -brief addr"),
        "ip_route": run("ip route"),
        "ip6_route": run("ip -6 route"),
        "ss_tcp": run("ss -H -tlnp"),
        "ss_udp": run("ss -H -ulnp"),
        "nmcli_devices": run("nmcli device status"),
        "nmcli_connections": run("nmcli connection show --active"),
        "ufw": run("ufw status"),
        "firewalld": run("firewall-cmd --state"),
        "docker": run("docker --version"),
        "docker_ps": run("docker ps --format '{{.Names}} {{.Image}} {{.Ports}}'"),
        "docker_compose_plugin": run("docker compose version"),
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
        "cloud_aws_instance_id": run(
            "curl -fsS --connect-timeout 1 --max-time 2 http://169.254.169.254/latest/meta-data/instance-id",
            timeout=3,
        ),
        "cloud_azure_instance": run(
            "curl -H Metadata:true -fsS --connect-timeout 1 --max-time 2 'http://169.254.169.254/metadata/instance?api-version=2021-02-01'",
            timeout=3,
        ),
        "cloud_gcp_instance_id": run(
            "curl -H 'Metadata-Flavor: Google' -fsS --connect-timeout 1 --max-time 2 http://metadata.google.internal/computeMetadata/v1/instance/id",
            timeout=3,
        ),
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
    hostnamectl_values = parse_hostnamectl(commands["hostnamectl"]["stdout"])
    private_ipv4, private_ipv6, global_ipv4, global_ipv6 = parse_ip_addresses(
        commands["ip_addr"]["stdout"]
    )
    active_interfaces = parse_network_interfaces(commands["ip_addr"]["stdout"])
    default_gateway = parse_default_gateway(commands["ip_route"]["stdout"])
    tcp_ports = parse_listening_ports(commands["ss_tcp"]["stdout"], "tcp")
    udp_ports = parse_listening_ports(commands["ss_udp"]["stdout"], "udp")

    vendor = read_file("/sys/class/dmi/id/sys_vendor") or hostnamectl_values.get("hardware_vendor")
    model = read_file("/sys/class/dmi/id/product_name") or hostnamectl_values.get("hardware_model")
    cpu = first_stdout(
        "lscpu | awk -F: '/Model name/ {gsub(/^[ \\t]+/, \"\", $2); print $2; exit}'"
    )
    virt = commands["virt"]["stdout"] if commands["virt"]["stdout"] else "none"
    provider = detect_provider(vendor, model, hostnamectl_values, commands)
    deployment_type = infer_deployment_type(provider, hostnamectl_values, commands)
    exposure, is_public = infer_exposure(
        public_ipv4, public_ipv6, global_ipv4, global_ipv6, private_ipv4
    )
    ip_static = infer_ip_static(commands)

    notes = [
        "Generated by setup_flow/generate_manifest.py using read-only local commands.",
        "The generator writes manifest.json with the correct spelling.",
        "public_ports is empty because this recovery flow does not perform an external inbound port scan.",
        "A public IPv4 returned by an egress service may be NAT/router egress, not necessarily an address assigned to this host.",
        "is_public is inferred from locally assigned global IP addresses and public egress checks; inbound reachability still requires external verification.",
        "deployment_type and provider are inferred from DMI, hostnamectl, NetworkManager, and metadata probes when available.",
    ]
    if public_ipv6 and public_ipv6 in local_ips_without_prefix(global_ipv6):
        notes.append("Public IPv6 check matches a global IPv6 address assigned to a local interface.")
    if public_ipv4 and public_ipv4 not in local_ips_without_prefix(global_ipv4) and private_ipv4:
        notes.append("Public IPv4 check does not match a local interface address; IPv4 is likely behind NAT.")

    return {
        "hostname": hostname,
        "deployment_type": deployment_type,
        "exposure": exposure,
        "provider": provider,
        "is_public": is_public,
        "public_ipv4": public_ipv4,
        "public_ipv6": public_ipv6,
        "private_ipv4": private_ipv4,
        "private_ipv6": private_ipv6,
        "global_ipv4_addresses": global_ipv4,
        "global_ipv6_addresses": global_ipv6,
        "ip_static": ip_static,
        "ip_confidence": "verified by successful local read-only commands and public egress IP lookup where available; public inbound ports were not externally scanned",
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
                    "ip6_route": commands["ip6_route"],
                    "nmcli_devices": commands["nmcli_devices"],
                    "nmcli_connections": commands["nmcli_connections"],
                }
            ),
            "firewall": {
                "ufw": commands["ufw"]["stdout"] or commands["ufw"]["stderr"] or "unknown",
                "firewalld": commands["firewalld"]["stdout"] or commands["firewalld"]["stderr"] or "unknown",
            },
            "docker": command_summary(commands["docker"]),
            "docker_running_containers": commands["docker_ps"]["stdout"] or "",
            "docker_ps_error": None if commands["docker_ps"]["ok"] else commands["docker_ps"]["stderr"] or None,
            "docker_compose": command_summary(commands["docker_compose_plugin"]) or command_summary(commands["docker_compose"]),
            "node": command_summary(commands["node"]),
            "npm": command_summary(commands["npm"]),
            "python3": command_summary(commands["python3"]),
            "postgres_client": command_summary(commands["psql"]),
            "git": command_summary(commands["git"]),
            "ollama": command_summary(commands["ollama"]),
            "samba": command_summary(commands["smbd"]),
            "running_services": commands["systemctl_services"]["stdout"],
        },
        "hardware": {
            "vendor": vendor,
            "model": model,
            "chassis": hostnamectl_values.get("chassis"),
            "virtualization_detected": virt,
            "cpu": cpu,
            "memory": commands["free"]["stdout"],
            "disk": commands["lsblk"]["stdout"],
            "lscpu": commands["lscpu"]["stdout"],
        },
        "network_interfaces": {
            "default_gateway": default_gateway,
            "active_interfaces": active_interfaces,
            "ip_addr": commands["ip_addr"]["stdout"],
            "ip_route": commands["ip_route"]["stdout"],
            "ip6_route": commands["ip6_route"]["stdout"],
            "nmcli_devices": commands["nmcli_devices"]["stdout"],
            "nmcli_connections": commands["nmcli_connections"]["stdout"],
        },
        "notes": notes,
        "raw_qa_log": [],
        "raw_command_outputs": commands,
        "last_updated_at": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
    }


def generate_manifest(manifest_file=MANIFEST_FILE):
    """Collect device information and write the completed manifest file."""
    manifest_path = Path(manifest_file)
    manifest = build_manifest()
    temp_file = manifest_path.with_suffix(".json.tmp")
    temp_file.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    json.loads(temp_file.read_text(encoding="utf-8"))
    temp_file.replace(manifest_path)
    return manifest_path


def run_all(manifest_file=MANIFEST_FILE):
    """Run the complete manifest collection, parsing, and writing pipeline."""
    return generate_manifest(manifest_file)


def generate_manifests(manifest_file=MANIFEST_FILE):
    """Public entry point for generating the complete device manifest."""
    return run_all(manifest_file)


def main():
    manifest_path = generate_manifests()
    print(f"success manifest.json generated at {manifest_path}")


if __name__ == "__main__":
    main()
