
import re

file_path = r'e:\auto-assit-group-master\auto-assit-group-master\templates\ticket_detail.html'
start_line = 6564
end_line = 12876

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

js_lines = lines[start_line-1:end_line]

jinja_pattern = re.compile(r'\{\{.*?\}\}')

print(f"Scanning lines {start_line} to {end_line} for Jinja tags...")
found = []
for i, line in enumerate(js_lines):
    matches = jinja_pattern.findall(line)
    if matches:
        print(f"Line {start_line + i}: {line.strip()}")
        found.extend(matches)

unique_tags = set(found)
print("\nUnique Jinja Tags Found:")
for tag in unique_tags:
    print(tag)
