import subprocess
import sys
import time
import urllib.request

BASE = ["docker", "compose", "--env-file", "config/lab.env", "-f", "compose.yaml"]
VALID_FAULTS = {"F1", "F2", "F3"}

def run(args, check=True):
    print("+", " ".join(args))
    return subprocess.run(args, check=check)

def compose(*args):
    return run(BASE + list(args))

def reset():
    compose("down", "--remove-orphans")
    compose("up", "-d", "--build")

def baseline():
    with urllib.request.urlopen("http://localhost:8000/context/INC-1001", timeout=5) as resp:
        print(resp.read().decode("utf-8"))
    compose("ps")
    compose("logs", "--tail", "30", "integration-client")

def fault(fid):
    if fid not in VALID_FAULTS:
        raise SystemExit("fault id must be F1, F2, or F3")
    compose("down", "--remove-orphans")
    cmd = BASE + ["-f", f"faults/{fid}.yaml", "up", "-d", "--build"]
    run(cmd, check=False)
    print(f"Seeded fault {fid} activated. Use docker compose ps and docker compose logs as evidence before changing anything.")

def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: python labctl.py up|down|reset|baseline|logs|ps|restart-client|fault <F1|F2|F3>")
    cmd = sys.argv[1]
    if cmd == "up": compose("up", "-d", "--build")
    elif cmd == "down": compose("down", "--remove-orphans")
    elif cmd == "reset": reset()
    elif cmd == "baseline": baseline()
    elif cmd == "logs": compose("logs", "--tail", "100")
    elif cmd == "ps": compose("ps")
    elif cmd == "restart-client": compose("up", "-d", "--force-recreate", "integration-client")
    elif cmd == "fault" and len(sys.argv) == 3: fault(sys.argv[2])
    else: raise SystemExit("unknown command")

if __name__ == "__main__":
    main()
