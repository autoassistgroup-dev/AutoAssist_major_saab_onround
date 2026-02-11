
file_path = r'e:\auto-assit-group-master\auto-assit-group-master\static\js\ticket_detail.js'

print(f"Checking {file_path} for '{{' ...")
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

found_count = 0
for i, line in enumerate(lines):
    if "{{" in line:
        print(f"Line {i+1}: {line.strip()}")
        found_count += 1

if found_count == 0:
    print("✅ No Jinja tags found.")
else:
    print(f"❌ Found {found_count} remaining tags.")
