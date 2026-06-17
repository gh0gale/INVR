issues = ["P7-02", "P7-03", "P9-01", "P9-03", "P8-02", "P2-12", "P6-04"]
file_path = "c:/codes/INVR/INVR/audit_report.md"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

for issue in issues:
    content = content.replace(f"**[{issue}]**", f"✅ **[{issue}]**")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
