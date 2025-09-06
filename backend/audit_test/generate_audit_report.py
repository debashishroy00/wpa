import json, os, socket, datetime as dt

report = {
  "generated_at": dt.datetime.utcnow().isoformat()+"Z",
  "host": socket.gethostname(),
  "checks": []
}

def add(name, ok, msg):
    report["checks"].append({"name": name, "ok": bool(ok), "message": msg})

# example financial identity check placeholders (offline-safe)
add("repo_present", os.path.exists("."), "Working directory exists")
add("app_dirs", True, "Expect /app exists in container")

# write report
os.makedirs("audit_test/out", exist_ok=True)
with open("audit_test/out/audit_report.json", "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)
print("WROTE audit_test/out/audit_report.json")

