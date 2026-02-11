
import re
import os

html_path = r'e:\auto-assit-group-master\auto-assit-group-master\templates\ticket_detail.html'
js_output_path = r'e:\auto-assit-group-master\auto-assit-group-master\static\js\ticket_detail.js'
start_line = 6564
end_line = 12876

# 1. Read the HTML file
with open(html_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 2. Extract JS lines (converting 1-based index to 0-based)
js_block = "".join(lines[start_line-1 : end_line])

# 3. Define Replacements (Jinja -> JS Context)
replacements = [
    (r"\{\{ ticket\.ticket_id \}\}", "window.flaskContext.ticketId"),
    (r"\{\{ ticket\.ticket_id\|e \}\}", "window.flaskContext.ticketId"),
    (r"\{\{ session\.member_id \}\}", "window.flaskContext.memberId"),
    (r"\{\{ session\.member_id if session\.member_id else '' \}\}", "window.flaskContext.memberId"),
    (r"\{\{ session\.member_id if session\.member_id else \"unknown\" \}\}", "window.flaskContext.memberId"), 
    (r"\{\{ ticket\.status \}\}", "window.flaskContext.ticketStatus"),
    (r"\{\{ ticket\.status\|default\(\"\", true\) \}\}", "window.flaskContext.ticketStatus"),
    (r"\{\{ ticket\.subject\|default\(\"\", true\) \}\}", "window.flaskContext.ticketSubject"),
    (r"\{\{ ticket\.name \}\}", "window.flaskContext.ticketName"),
    (r"\{\{ ticket\.name\|default\(\"\", true\) \}\}", "window.flaskContext.ticketName"),
    (r"\{\{ ticket\.email\|default\(\"\", true\) \}\}", "window.flaskContext.ticketEmail"),
    (r"\{\{ ticket\.Priority\|default\(\"\", true\) \}\}", "window.flaskContext.ticketPriority"),
    (r"\{\{ ticket\.message_id\|default\(\"\", true\) \}\}", "window.flaskContext.ticketMessageId"),
    (r"\{\{ ticket\.creation_method\|default\(\"\", true\) \}\}", "window.flaskContext.ticketCreationMethod"),
    (r"\{\{ session\.name \}\}", "window.flaskContext.sessionName"),
    (r"\{\{ session\.name or \"User\" \}\}", "window.flaskContext.sessionName"),
    (r"\{\{ session\.user_id if session\.user_id else \"customer\" \}\}", "window.flaskContext.userId"),
    (r"\{\{ \"agent\" if session\.is_agent else \"customer\" \}\}", "window.flaskContext.userType"),
    (r"\{\{ technician or \"No Technician\" \}\}", "window.flaskContext.technician"),
    # Handle "replies|length"
    (r"\{\{ replies\|length\|default\(0\) \}\}", "window.flaskContext.repliesCount"),
    # Careful with quotes in JS. If the Jinja was inside quotes, we might now have "window.flaskContext..." inside quotes.
    # We will need to check for that.
]

# Apply replacements
processed_js = js_block
for pattern, replacement in replacements:
    # Check if the pattern is inside quotes in the source
    # This is a naive check. A better way is to replacing specific known lines or context.
    # However, since we are moving to an object, we often want the VALUE.
    # Case 1: var x = "{{ val }}"; -> var x = window.flaskContext.val;
    
    # We will first try to remove surrounding quotes if they exist
    # e.g. '{{ val }}' -> window.flaskContext.val
    regex_quote_single = r"'" + pattern + r"'"
    processed_js = re.sub(regex_quote_single, replacement, processed_js)
    
    regex_quote_double = r'"' + pattern + r'"'
    processed_js = re.sub(regex_quote_double, replacement, processed_js)
    
    # Case 2: Just the value (e.g. inside a function call or interpolation)
    # {{ val }} -> window.flaskContext.val
    processed_js = re.sub(pattern, replacement, processed_js)


# 4. Write JS file
os.makedirs(os.path.dirname(js_output_path), exist_ok=True)
with open(js_output_path, 'w', encoding='utf-8') as f:
    f.write("document.addEventListener('DOMContentLoaded', function() {\n")
    f.write(processed_js)
    f.write("\n});")

print(f"Extracted JS to {js_output_path}")

# 5. We do NOT overwrite the HTML file here. We will let the Agent do that separately 
# using multi_replace_file_content to remain safe and atomic.
# This script is purely for extracting the code safely with python processing.
