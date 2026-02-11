#!/usr/bin/env python3
"""
Enhanced Script v2: Split ticket_detail parts into even smaller, meaningful sections.
This is a pure CODE SPLITTING - no logic changes.

Run from the AutoAssist__portal directory:
    python split_ticket_detail_v2.py

This will further split:
1. _styles.html -> Multiple CSS section files
2. _modals.html -> Individual modal files + main layout
3. _scripts.html -> Logical JavaScript modules
"""

import os
import re
from pathlib import Path

# Configuration
TEMPLATE_DIR = Path("templates")
PARTS_DIR = TEMPLATE_DIR / "ticket_detail_parts"

# CSS Section markers (comments in the CSS)
CSS_SECTIONS = [
    ("PROFESSIONAL DARK THEME", "_css_theme.html"),
    ("CUSTOM SCROLLBAR", "_css_scrollbar.html"),
    ("NAVBAR", "_css_navbar.html"),
    ("COMPACT STYLING", "_css_compact.html"),
    ("GLASS COMPONENTS", "_css_glass.html"),
    ("GRADIENT TEXT", "_css_gradients.html"),
    ("PRIORITY INDICATORS", "_css_priority.html"),
    ("MESSAGE BOX", "_css_messages.html"),
    ("EMAIL TEMPLATE MODAL", "_css_email_modal.html"),
    ("REPLY FORM", "_css_reply_form.html"),
    ("ATTACHMENT", "_css_attachments.html"),
    ("SIDEBAR", "_css_sidebar.html"),
    ("VEHICLE", "_css_vehicle_modal.html"),
    ("RESPONSIVE", "_css_responsive.html"),
    ("DRAG", "_css_dragdrop.html"),
    ("STICKY", "_css_sticky.html"),
    ("STATUS", "_css_status.html"),
]

# Modal markers (HTML comments or IDs)
MODAL_SECTIONS = [
    ("messageModal", "_modal_message.html", "Message Expansion Modal"),
    ("confirmModal", "_modal_confirm.html", "Confirmation Modal"),
    ("forwardModal", "_modal_forward.html", "Forward Modal"),
    ("noteModal", "_modal_note.html", "Add Note Modal"),
    ("editTemplateModal", "_modal_edit_template.html", "Edit Template Modal"),
    ("documentModal", "_modal_document.html", "Document Modal"),
    ("vehicleClaimModal", "_modal_vehicle_claim.html", "Vehicle & Claim Edit Modal"),
    ("assignModal", "_modal_assign.html", "Assignment Modal"),
    ("emailTemplateModal", "_modal_email_template.html", "Email Template Modal"),
]

# JavaScript section markers
JS_SECTIONS = [
    ("DOMContentLoaded", "_js_init.html", "Initialization & DOMContentLoaded"),
    ("Modal functions", "_js_modals.html", "Modal Functions"),
    ("Note functions", "_js_notes.html", "Note Functions"),
    ("Template functionality", "_js_templates.html", "Template Functions"),
    ("Document", "_js_documents.html", "Document Functions"),
    ("Attachment", "_js_attachments.html", "Attachment Handling"),
    ("Vehicle", "_js_vehicle.html", "Vehicle & Claim Functions"),
    ("Reply form", "_js_reply_form.html", "Reply Form Handling"),
    ("Socket", "_js_socket.html", "Socket.IO Real-time"),
]


def read_file(filepath):
    """Read file content."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def read_lines(filepath):
    """Read file lines."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.readlines()


def write_file(filepath, content):
    """Write content to file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        if isinstance(content, list):
            f.writelines(content)
        else:
            f.write(content)
    print(f"  ✓ Created: {filepath}")


def find_line_index(lines, marker, start_from=0):
    """Find the line index (0-indexed) containing the marker."""
    for i in range(start_from, len(lines)):
        if marker.lower() in lines[i].lower():
            return i
    return -1


def split_styles():
    """Split _styles.html into meaningful CSS sections."""
    print("\n📦 Splitting CSS Styles...")
    
    styles_file = PARTS_DIR / "_styles.html"
    if not styles_file.exists():
        print("  ⚠️ _styles.html not found, skipping...")
        return False
    
    lines = read_lines(styles_file)
    total_lines = len(lines)
    
    # Create css subdirectory
    css_dir = PARTS_DIR / "css"
    css_dir.mkdir(exist_ok=True)
    
    # Find section boundaries based on CSS comments
    sections = []
    
    for marker, filename in CSS_SECTIONS:
        idx = find_line_index(lines, marker)
        if idx != -1:
            sections.append((idx, marker, filename))
    
    # Sort by line index
    sections.sort(key=lambda x: x[0])
    
    # Extract each section
    created_files = []
    for i, (start_idx, marker, filename) in enumerate(sections):
        # Find the end (start of next section or end of file)
        if i + 1 < len(sections):
            end_idx = sections[i + 1][0]
        else:
            end_idx = total_lines
        
        # Extract lines for this section
        section_lines = lines[start_idx:end_idx]
        
        # Write to file
        filepath = css_dir / filename
        write_file(filepath, section_lines)
        created_files.append(filename)
    
    # Handle the beginning (before first section marker)
    if sections and sections[0][0] > 0:
        beginning = lines[:sections[0][0]]
        write_file(css_dir / "_css_base.html", beginning)
        created_files.insert(0, "_css_base.html")
    
    # Create the new _styles.html that includes all CSS parts
    includes = ['<style>\n']
    for filename in created_files:
        includes.append(f"{{% include 'ticket_detail_parts/css/{filename}' %}}\n")
    includes.append('</style>\n')
    
    # Actually, we need to keep the original structure
    # Let's just create the individual files and a combined include file
    
    print(f"  ✓ Created {len(created_files)} CSS section files in css/")
    return True


def split_modals():
    """Split _modals.html into individual modal files + main layout."""
    print("\n📦 Splitting Modals...")
    
    modals_file = PARTS_DIR / "_modals.html"
    if not modals_file.exists():
        print("  ⚠️ _modals.html not found, skipping...")
        return False
    
    content = read_file(modals_file)
    lines = read_lines(modals_file)
    
    # Create modals subdirectory
    modals_dir = PARTS_DIR / "modals"
    modals_dir.mkdir(exist_ok=True)
    
    # Find each modal by ID
    modal_boundaries = []
    
    for modal_id, filename, description in MODAL_SECTIONS:
        # Find the modal opening div
        pattern = rf'<div\s+id="{modal_id}"'
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            # Find line number
            char_pos = match.start()
            line_num = content[:char_pos].count('\n')
            modal_boundaries.append((line_num, modal_id, filename, description))
    
    # Sort by line number
    modal_boundaries.sort(key=lambda x: x[0])
    
    # Find body start and notifications (before first modal)
    first_modal_line = modal_boundaries[0][0] if modal_boundaries else len(lines)
    
    # Extract body start + notifications
    body_start = lines[:first_modal_line]
    write_file(modals_dir / "_body_start.html", body_start)
    
    # Extract each modal
    for i, (start_line, modal_id, filename, description) in enumerate(modal_boundaries):
        # Find the end of this modal (next modal or main layout)
        if i + 1 < len(modal_boundaries):
            end_line = modal_boundaries[i + 1][0]
        else:
            # Find "Main Layout Container" comment
            main_layout_idx = find_line_index(lines, "Main Layout Container", start_line)
            if main_layout_idx != -1:
                end_line = main_layout_idx
            else:
                end_line = len(lines)
        
        modal_lines = lines[start_line:end_line]
        write_file(modals_dir / filename, modal_lines)
    
    # Extract main layout (after last modal)
    main_layout_idx = find_line_index(lines, "Main Layout Container")
    if main_layout_idx != -1:
        main_layout = lines[main_layout_idx:]
        write_file(modals_dir / "_main_content.html", main_layout)
    
    print(f"  ✓ Created {len(modal_boundaries) + 2} modal/layout files in modals/")
    return True


def split_scripts():
    """Split _scripts.html into logical JavaScript modules."""
    print("\n📦 Splitting JavaScript...")
    
    scripts_file = PARTS_DIR / "_scripts.html"
    if not scripts_file.exists():
        print("  ⚠️ _scripts.html not found, skipping...")
        return False
    
    lines = read_lines(scripts_file)
    total_lines = len(lines)
    
    # Create js subdirectory
    js_dir = PARTS_DIR / "js"
    js_dir.mkdir(exist_ok=True)
    
    # Find key JavaScript sections by searching for function definitions and comments
    section_markers = [
        ("application/json", "_js_data.html", "JSON Data Blocks"),
        ("DOMContentLoaded", "_js_dom_ready.html", "DOM Ready Handler"),
        ("function openModal", "_js_modal_funcs.html", "Modal Functions"),
        ("function loadNotes", "_js_notes.html", "Notes Functions"),
        ("function loadTemplates", "_js_templates.html", "Template Functions"),
        ("function loadCommonDocuments", "_js_common_docs.html", "Common Documents"),
        ("ATTACHMENT HANDLING", "_js_attachments.html", "Attachment Handling"),
        ("function setupAttachmentHandlers", "_js_attachment_handlers.html", "Attachment Handlers"),
        ("Enhanced Response attachment", "_js_dragdrop.html", "Drag & Drop"),
        ("Reply form submission", "_js_reply_form.html", "Reply Form"),
        ("Vehicle & Claim", "_js_vehicle_claim.html", "Vehicle & Claim"),
        ("Status dropdown", "_js_status.html", "Status Dropdown"),
        ("Socket.IO", "_js_socket.html", "Socket.IO Real-time"),
    ]
    
    # Find all section boundaries
    sections = []
    for marker, filename, description in section_markers:
        idx = find_line_index(lines, marker)
        if idx != -1:
            sections.append((idx, filename, description))
    
    # Sort by line index
    sections.sort(key=lambda x: x[0])
    
    # Remove duplicates (keep first occurrence)
    seen_files = set()
    unique_sections = []
    for idx, filename, desc in sections:
        if filename not in seen_files:
            seen_files.add(filename)
            unique_sections.append((idx, filename, desc))
    sections = unique_sections
    
    # Extract each section
    created_files = []
    for i, (start_idx, filename, description) in enumerate(sections):
        # Find end
        if i + 1 < len(sections):
            end_idx = sections[i + 1][0]
        else:
            end_idx = total_lines
        
        section_lines = lines[start_idx:end_idx]
        write_file(js_dir / filename, section_lines)
        created_files.append((filename, description))
    
    # Handle the script tag opening (before first section)
    if sections and sections[0][0] > 0:
        beginning = lines[:sections[0][0]]
        write_file(js_dir / "_js_start.html", beginning)
        created_files.insert(0, ("_js_start.html", "Script Tag Start"))
    
    print(f"  ✓ Created {len(created_files)} JavaScript files in js/")
    return True


def create_combined_template():
    """Create the new ticket_detail_v2.html that includes all parts."""
    print("\n📝 Creating combined modular template...")
    
    # Check what subdirectories exist
    css_dir = PARTS_DIR / "css"
    modals_dir = PARTS_DIR / "modals"
    js_dir = PARTS_DIR / "js"
    
    template = '''<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description"
        content="AutoAssistGroup Support Ticket #{{ ticket.ticket_id }} - {{ (ticket.subject or 'No Subject')[:100] }}">
    <meta name="robots" content="noindex, nofollow">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="theme-color" content="#4f46e5">
    <title>Ticket #{{ ticket.ticket_id }} - AutoAssistGroup Portal</title>

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
    
    <!-- ===== CSS STYLES ===== -->
    <style>
'''
    
    # Add CSS includes
    if css_dir.exists():
        css_files = sorted([f.name for f in css_dir.iterdir() if f.is_file()])
        for css_file in css_files:
            template += f"    {{% include 'ticket_detail_parts/css/{css_file}' %}}\n"
    else:
        template += "    {% include 'ticket_detail_parts/_styles.html' %}\n"
    
    template += '''    </style>
</head>

<!-- ===== BODY: MODALS & MAIN LAYOUT ===== -->
'''
    
    # Add modal includes
    if modals_dir.exists():
        modal_files = sorted([f.name for f in modals_dir.iterdir() if f.is_file()])
        for modal_file in modal_files:
            template += f"{{% include 'ticket_detail_parts/modals/{modal_file}' %}}\n"
    else:
        template += "{% include 'ticket_detail_parts/_modals.html' %}\n"
    
    template += '''
<!-- ===== JSON DATA ===== -->
{% include 'ticket_detail_parts/_main_layout.html' %}

<!-- ===== JAVASCRIPT ===== -->
'''
    
    # Add JS includes
    if js_dir.exists():
        js_files = sorted([f.name for f in js_dir.iterdir() if f.is_file()])
        for js_file in js_files:
            template += f"{{% include 'ticket_detail_parts/js/{js_file}' %}}\n"
    else:
        template += "{% include 'ticket_detail_parts/_scripts.html' %}\n"
    
    template += '''
</body>

</html>
'''
    
    write_file(TEMPLATE_DIR / "ticket_detail_v2.html", template)
    return True


def main():
    """Main function."""
    print("\n" + "="*60)
    print("  Enhanced Split v2: Further splitting into sections")
    print("="*60)
    
    if not PARTS_DIR.exists():
        print(f"❌ Error: {PARTS_DIR} not found!")
        print("   Run split_ticket_detail.py first.")
        return False
    
    # Split CSS
    split_styles()
    
    # Split Modals
    split_modals()
    
    # Split JavaScript
    split_scripts()
    
    # Create combined template
    create_combined_template()
    
    # Print summary
    print("\n" + "="*60)
    print("  ✅ Enhanced Split Complete!")
    print("="*60)
    
    # Count files
    css_count = len(list((PARTS_DIR / "css").iterdir())) if (PARTS_DIR / "css").exists() else 0
    modals_count = len(list((PARTS_DIR / "modals").iterdir())) if (PARTS_DIR / "modals").exists() else 0
    js_count = len(list((PARTS_DIR / "js").iterdir())) if (PARTS_DIR / "js").exists() else 0
    
    print(f"""
📁 Created subdirectories in {PARTS_DIR}/:

   📂 css/     ({css_count} files)  - CSS sections by feature
   📂 modals/  ({modals_count} files) - Individual modal dialogs
   📂 js/      ({js_count} files)  - JavaScript modules

📄 New template: templates/ticket_detail_v2.html

🔄 To use the new modular version:
   1. Stop your Flask app
   2. Rename: ticket_detail.html -> ticket_detail_backup.html
   3. Rename: ticket_detail_v2.html -> ticket_detail.html
   4. Restart your app and test

⚠️  Original files are preserved - no changes to existing code!
""")
    
    return True


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
