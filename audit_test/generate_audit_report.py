import json, os, socket, datetime as dt, subprocess, sys

def run(cmd):
    try:
        p = subprocess.run([sys.executable, cmd], capture_output=True, text=True, timeout=90)
        return {"ok": p.returncode == 0, "stdout": p.stdout, "stderr": p.stderr}
    except Exception as e:
        return {"ok": False, "error": str(e)}

report = {"generated_at": dt.datetime.utcnow().isoformat()+"Z", "host": socket.gethostname(), "sections": {}}

sections = {
    "vector_store": "audit_test/audit_vector_data.py",
    "context_generation": "audit_test/trace_context_generation.py",
    "endpoint_integration": "audit_test/audit_chat_endpoint.py",
    "llm_calls": "audit_test/intercept_llm_calls.py",
    "data_accuracy": "audit_test/verify_data_accuracy.py",
}

for name, script in sections.items():
    res = run(script)
    report["sections"][name] = res

os.makedirs("audit_test/out", exist_ok=True)
with open("audit_test/out/audit_report.json", "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)
print("WROTE audit_test/out/audit_report.json")
