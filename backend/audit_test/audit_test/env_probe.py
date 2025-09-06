# audit_test/env_probe.py
import os, platform, subprocess, json, socket

def sh(cmd: str):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=8).decode().strip()
    except Exception as e:
        return f"ERR: {e}"

out = {
  "cwd": os.getcwd(),
  "platform": platform.platform(),
  "python": sh("python -V"),
  "which_python": sh("which python" if os.name != "nt" else "where python"),
  "docker_ps": sh("docker ps"),
  "docker_context": sh("docker context ls"),
  "wsl_list": sh("wsl.exe -l -v") if os.name == "nt" else "N/A",
  "git_root": sh("git rev-parse --show-toplevel"),
  "net_ping": sh("ping -c 1 google.com" if os.name != "nt" else "ping -n 1 google.com"),
}
print(json.dumps(out, indent=2))

