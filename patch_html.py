
html_path = r'e:\auto-assit-group-master\auto-assit-group-master\templates\ticket_detail.html'
start_line = 6563
end_line = 12877

replacement_block = """    <script>
        // Pass server-side data to the external JS (Refactored)
        window.flaskContext = {
            ticketId: "{{ ticket.ticket_id }}",
            memberId: "{{ session.member_id if session.member_id else '' }}",
            ticketStatus: "{{ ticket.status|default('', true) }}",
            ticketSubject: "{{ ticket.subject|default('', true)|e }}",
            ticketName: "{{ ticket.name|default('', true)|e }}",
            ticketEmail: "{{ ticket.email|default('', true)|e }}",
            ticketPriority: "{{ ticket.Priority|default('Medium', true) }}",
            ticketMessageId: "{{ ticket.message_id|default('', true) }}",
            ticketCreationMethod: "{{ ticket.creation_method|default('', true) }}",
            sessionName: "{{ session.name or 'User' }}",
            userId: "{{ session.user_id if session.user_id else 'customer' }}",
            userType: "{{ 'agent' if session.is_agent else 'customer' }}",
            technician: "{{ technician or 'No Technician' }}",
            repliesCount: {{ replies|length|default(0) }}
        };
    </script>
    <script src="{{ url_for('static', filename='js/ticket_detail.js') }}"></script>
"""

with open(html_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Ensure we are targeting the right lines
print(f"Replacing lines {start_line} to {end_line}")
print(f"Original Start: {lines[start_line-1].strip()}")
print(f"Original End: {lines[end_line-1].strip()}")

# Keep lines before start_line
new_content = lines[:start_line-1]
# Add replacement
new_content.append(replacement_block)
# Add lines after end_line
new_content.extend(lines[end_line:])

with open(html_path, 'w', encoding='utf-8') as f:
    f.writelines(new_content)

print("Patch applied successfully.")
