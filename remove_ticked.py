file_path = "c:/codes/INVR/INVR/audit_report.md"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = [line for line in lines if "✅" not in line]

with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)
