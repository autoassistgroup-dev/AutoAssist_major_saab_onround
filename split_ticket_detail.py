#!/usr/bin/env python3
"""
Script to split ticket_detail.html into manageable partial files.
Uses Jinja2 {% include %} pattern for Flask templates.

Run from the AutoAssist__portal directory:
    python split_ticket_detail.py

This will:
1. Create a 'templates/ticket_detail_parts/' directory
2. Split the file into logical sections:
   - _styles.html (CSS)
   - _modals.html (Modal dialogs)
   - _main_layout.html (Main HTML content)
   - _scripts_core.html (Core JavaScript)
   - _scripts_socket.html (Socket.IO code)
3. Create a new ticket_detail_modular.html that includes all parts
4. Keep the original ticket_detail.html as backup

After running, test with ticket_detail_modular.html
If working correctly, you can rename it to ticket_detail.html
"""

import os
import re
from pathlib import Path

# Configuration
TEMPLATE_DIR = Path("templates")
ORIGINAL_FILE = TEMPLATE_DIR / "ticket_detail.html"
PARTS_DIR = TEMPLATE_DIR / "ticket_detail_parts"
OUTPUT_FILE = TEMPLATE_DIR / "ticket_detail_modular.html"

# Define line ranges for each section (1-indexed, inclusive)
# These are approximate and the script will find exact boundaries
SECTIONS = {
    "head_start": {
        "start_line": 1,
        "end_marker": "<style>",  # Line containing this marker
        "output_file": "_head_meta.html",
        "description": "HTML head meta tags and external links"
    },
    "styles": {
        "start_marker": "<style>",
        "end_marker": "</style>",
        "include_markers": True,
        "output_file": "_styles.html",
        "description": "All CSS styles"
    },
    "head_end_body_start": {
        "start_marker": "</style>",
        "end_marker": "<!-- Main Layout Container",
        "output_file": "_modals.html",
        "description": "Modal dialogs and body start"
    },
    "main_layout": {
        "start_marker": "<!-- Main Layout Container",
        "end_marker": "<script type=\"application/json\"",
        "output_file": "_main_layout.html",
        "description": "Main page layout HTML"
    },
    "scripts": {
        "start_marker": "<script type=\"application/json\"",
        "end_marker": "</body>",
        "output_file": "_scripts.html",
        "description": "All JavaScript code"
    },
    "end": {
        "start_marker": "</body>",
        "end_marker": None,  # Until end of file
        "output_file": "_end.html",
        "description": "Closing body and html tags"
    }
}


def read_file(filepath):
    """Read file content and return lines."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.readlines()


def write_file(filepath, lines):
    """Write lines to file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f"  ✓ Created: {filepath} ({len(lines)} lines)")


def find_line_containing(lines, marker, start_from=0):
    """Find the line number (0-indexed) containing the marker."""
    for i in range(start_from, len(lines)):
        if marker in lines[i]:
            return i
    return -1


def split_file():
    """Main function to split the ticket_detail.html file."""
    
    print("\n" + "="*60)
    print("  Splitting ticket_detail.html into modular parts")
    print("="*60)
    
    # Check if original file exists
    if not ORIGINAL_FILE.exists():
        print(f"❌ Error: {ORIGINAL_FILE} not found!")
        return False
    
    # Create parts directory
    PARTS_DIR.mkdir(exist_ok=True)
    print(f"\n📁 Created directory: {PARTS_DIR}")
    
    # Read original file
    lines = read_file(ORIGINAL_FILE)
    total_lines = len(lines)
    print(f"📄 Read {total_lines} lines from {ORIGINAL_FILE}")
    
    # Find key boundaries
    print("\n🔍 Finding section boundaries...")
    
    # Find </style> tag (end of CSS)
    style_end = find_line_containing(lines, "</style>")
    print(f"   </style> found at line {style_end + 1}")
    
    # Find </head> tag
    head_end = find_line_containing(lines, "</head>", style_end)
    print(f"   </head> found at line {head_end + 1}")
    
    # Find <body> tag
    body_start = find_line_containing(lines, "<body", head_end)
    print(f"   <body> found at line {body_start + 1}")
    
    # Find first <script> (after modals)
    first_script = find_line_containing(lines, '<script type="application/json"', body_start)
    print(f"   First JSON script at line {first_script + 1}")
    
    # Find main <script> tag for JS code
    main_script = find_line_containing(lines, "<script>", first_script)
    print(f"   Main <script> found at line {main_script + 1}")
    
    # Find Socket.IO section (approximately line 13200+)
    socket_section = find_line_containing(lines, "Socket.IO Real-time", main_script)
    if socket_section == -1:
        socket_section = find_line_containing(lines, "SOCKET.IO", main_script)
    print(f"   Socket.IO section at line {socket_section + 1}")
    
    # Find </body> tag
    body_end = find_line_containing(lines, "</body>", socket_section if socket_section > 0 else main_script)
    print(f"   </body> found at line {body_end + 1}")
    
    # Split into sections
    print("\n✂️  Creating partial files...")
    
    # 1. Styles (lines 28 to style_end inclusive)
    style_start = find_line_containing(lines, "<style>")
    styles_content = lines[style_start:style_end + 1]
    write_file(PARTS_DIR / "_styles.html", styles_content)
    
    # 2. Modals (after </head> through first_script)
    modals_content = lines[body_start:first_script]
    write_file(PARTS_DIR / "_modals.html", modals_content)
    
    # 3. Main layout HTML (first_script to main_script)
    # This includes JSON data blocks
    main_layout = lines[first_script:main_script]
    write_file(PARTS_DIR / "_main_layout.html", main_layout)
    
    # 4. Core scripts (main_script to socket_section or body_end)
    if socket_section > main_script:
        scripts_core = lines[main_script:socket_section]
        write_file(PARTS_DIR / "_scripts_core.html", scripts_core)
        
        # 5. Socket scripts (socket_section to body_end)
        scripts_socket = lines[socket_section:body_end]
        write_file(PARTS_DIR / "_scripts_socket.html", scripts_socket)
    else:
        # All scripts together
        scripts_all = lines[main_script:body_end]
        write_file(PARTS_DIR / "_scripts.html", scripts_all)
    
    # Create the new modular template
    print("\n📝 Creating modular template...")
    
    modular_template = f'''<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description"
        content="AutoAssistGroup Support Ticket #{{{{ ticket.ticket_id }}}} - {{{{ (ticket.subject or 'No Subject')[:100] }}}}">
    <meta name="robots" content="noindex, nofollow">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="theme-color" content="#4f46e5">
    <title>Ticket #{{{{ ticket.ticket_id }}}} - AutoAssistGroup Portal</title>

    <!-- Preconnect to external domains for performance -->
    <link rel="preconnect" href="https://cdn.jsdelivr.net">
    <link rel="preconnect" href="https://cdnjs.cloudflare.com">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>

    <!-- Optimized external stylesheets -->
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet" media="all">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" media="all">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet"
        media="all">
    <link href="/static/css/animations.css" rel="stylesheet">
    <!-- Socket.IO for real-time updates -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.min.js"></script>
    
    <!-- Styles included from partial -->
    {{% include 'ticket_detail_parts/_styles.html' %}}
</head>

<!-- Modals included from partial -->
{{% include 'ticket_detail_parts/_modals.html' %}}

<!-- Main Layout included from partial -->
{{% include 'ticket_detail_parts/_main_layout.html' %}}

<!-- Scripts included from partial -->
'''
    
    # Check which script files were created
    if (PARTS_DIR / "_scripts_core.html").exists():
        modular_template += '''{% include 'ticket_detail_parts/_scripts_core.html' %}

{% include 'ticket_detail_parts/_scripts_socket.html' %}
'''
    else:
        modular_template += '''{% include 'ticket_detail_parts/_scripts.html' %}
'''
    
    modular_template += '''
</body>

</html>
'''
    
    write_file(OUTPUT_FILE, [modular_template])
    
    # Print summary
    print("\n" + "="*60)
    print("  ✅ Split Complete!")
    print("="*60)
    print(f"""
📁 Created files in {PARTS_DIR}/:
   - _styles.html       (CSS styles)
   - _modals.html       (Modal dialogs) 
   - _main_layout.html  (Main HTML layout)
   - _scripts_core.html (Core JavaScript)
   - _scripts_socket.html (Socket.IO code)
   
📄 New modular template: {OUTPUT_FILE}

🔄 Next Steps:
   1. Backup your original: copy ticket_detail.html ticket_detail_backup.html
   2. Test the modular version by temporarily renaming:
      - Rename ticket_detail.html -> ticket_detail_original.html
      - Rename ticket_detail_modular.html -> ticket_detail.html
   3. Test your application
   4. If working, delete the backup files
   
⚠️  The original ticket_detail.html is UNCHANGED
""")
    
    return True


if __name__ == "__main__":
    try:
        success = split_file()
        if not success:
            print("\n❌ Split failed!")
            exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
