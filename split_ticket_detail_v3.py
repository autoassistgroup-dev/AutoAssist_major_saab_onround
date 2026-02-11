#!/usr/bin/env python3
"""
Enhanced Script v3: Proper extraction of complete modal blocks and JS sections.
Uses regex to find complete div blocks for modals.

Run from the AutoAssist__portal directory:
    python split_ticket_detail_v3.py
"""

import os
import re
from pathlib import Path

TEMPLATE_DIR = Path("templates")
PARTS_DIR = TEMPLATE_DIR / "ticket_detail_parts"


def read_file(filepath):
    """Read file content."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def write_file(filepath, content):
    """Write content to file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    size_kb = len(content) / 1024
    print(f"  ✓ {filepath.name} ({size_kb:.1f} KB)")


def extract_modal_by_id(content, modal_id):
    """Extract a complete modal div by its ID, handling nested divs."""
    # Find the start of the modal
    pattern = rf'<div\s+id="{modal_id}"'
    match = re.search(pattern, content)
    if not match:
        return None, None
    
    start_pos = match.start()
    
    # Find the end by counting div tags
    pos = start_pos
    div_count = 0
    found_first = False
    
    while pos < len(content):
        # Look for opening or closing div tags
        open_match = re.match(r'<div\b', content[pos:], re.IGNORECASE)
        close_match = re.match(r'</div>', content[pos:], re.IGNORECASE)
        
        if open_match:
            div_count += 1
            found_first = True
            pos += len(open_match.group())
        elif close_match:
            div_count -= 1
            pos += len(close_match.group())
            if found_first and div_count == 0:
                # Found the closing tag
                return content[start_pos:pos], (start_pos, pos)
        else:
            pos += 1
    
    return None, None


def split_modals_properly():
    """Split modals properly by extracting complete div blocks."""
    print("\n📦 Splitting Modals (proper extraction)...")
    
    modals_file = PARTS_DIR / "_modals.html"
    if not modals_file.exists():
        print("  ⚠️ _modals.html not found")
        return False
    
    content = read_file(modals_file)
    modals_dir = PARTS_DIR / "modals"
    
    # Define modals to extract in order
    modals = [
        ("messageModal", "_modal_message.html"),
        ("confirmModal", "_modal_confirm.html"),
        ("forwardModal", "_modal_forward.html"),
        ("noteModal", "_modal_note.html"),
        ("editTemplateModal", "_modal_edit_template.html"),
        ("documentModal", "_modal_document.html"),
        ("vehicleClaimModal", "_modal_vehicle_claim.html"),
        ("assignModal", "_modal_assign.html"),
        ("emailTemplateModal", "_modal_email_template.html"),
    ]
    
    # Track extraction positions
    extracted_ranges = []
    
    for modal_id, filename in modals:
        modal_content, pos_range = extract_modal_by_id(content, modal_id)
        if modal_content:
            # Add proper indentation and newlines
            write_file(modals_dir / filename, modal_content + "\n")
            extracted_ranges.append((pos_range[0], pos_range[1], modal_id))
    
    # Extract body start (before first modal)
    first_modal_pos = min([r[0] for r in extracted_ranges]) if extracted_ranges else len(content)
    body_start = content[:first_modal_pos].strip()
    write_file(modals_dir / "_body_start.html", body_start + "\n")
    
    # Extract main content (after last modal, starting from "Main Layout Container")
    main_layout_match = re.search(r'<!-- Main Layout Container', content)
    if main_layout_match:
        main_content = content[main_layout_match.start():].strip()
        write_file(modals_dir / "_main_content.html", main_content + "\n")
    
    print(f"  ✓ Created {len(modals) + 2} modal files")
    return True


def split_css_by_comments():
    """Split CSS by comment section markers."""
    print("\n📦 Splitting CSS by sections...")
    
    styles_file = PARTS_DIR / "_styles.html"
    if not styles_file.exists():
        print("  ⚠️ _styles.html not found")
        return False
    
    content = read_file(styles_file)
    css_dir = PARTS_DIR / "css"
    
    # CSS section markers (comments in the file)
    # Format: (search_pattern, output_filename, description)
    sections = [
        (r'/\*\s*=+\s*PROFESSIONAL DARK THEME', '_01_theme.html', 'Theme Variables'),
        (r'/\*\s*=+\s*CUSTOM SCROLLBAR', '_02_scrollbar.html', 'Scrollbar'),
        (r'/\*\s*=+\s*GLOBAL STYLES', '_03_global.html', 'Global Styles'),
        (r'/\*\s*=+\s*NAVBAR', '_04_navbar.html', 'Navbar'),
        (r'/\*\s*=+\s*USER AVATAR', '_05_avatar.html', 'User Avatar'),
        (r'/\*\s*=+\s*MOBILE MENU', '_06_mobile.html', 'Mobile Menu'),
        (r'/\*\s*=+\s*COMPACT STYLING', '_07_compact.html', 'Compact Styling'),
        (r'/\*\s*=+\s*BACKGROUND', '_08_background.html', 'Background'),
        (r'/\*\s*=+\s*GLASS COMPONENTS', '_09_glass.html', 'Glass Components'),
        (r'/\*\s*=+\s*COMPACT PROFESSIONAL', '_10_professional.html', 'Professional Styling'),
        (r'/\*\s*=+\s*ADDITIONAL FIXES', '_11_fixes.html', 'Additional Fixes'),
        (r'/\*\s*=+\s*GRADIENT TEXT', '_12_gradients.html', 'Gradients'),
        (r'/\*\s*=+\s*PRIORITY INDICATORS', '_13_priority.html', 'Priority'),
        (r'/\*\s*=+\s*PROFESSIONAL MESSAGE', '_14_messages.html', 'Messages'),
        (r'/\*\s*=+\s*EMAIL TEMPLATE MODAL', '_15_email_modal.html', 'Email Modal'),
        (r'/\*\s*=+\s*REPLY FORM', '_16_reply_form.html', 'Reply Form'),
        (r'/\*\s*=+\s*MODERN ATTACHMENT', '_17_attachments.html', 'Attachments'),
        (r'/\*\s*=+\s*SIDEBAR', '_18_sidebar.html', 'Sidebar'),
        (r'/\*\s*=+\s*VEHICLE', '_19_vehicle.html', 'Vehicle Modal'),
        (r'/\*\s*=+\s*NORMAL UI', '_20_normal_ui.html', 'Normal UI'),
        (r'/\*\s*=+\s*ENHANCED DRAG', '_21_dragdrop.html', 'Drag & Drop'),
        (r'/\*\s*=+\s*STICKY', '_22_sticky.html', 'Sticky Layout'),
        (r'/\*\s*=+\s*STATUS', '_23_status.html', 'Status Dropdown'),
    ]
    
    # Find all section positions
    section_positions = []
    for pattern, filename, desc in sections:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            section_positions.append((match.start(), filename, desc))
    
    # Sort by position
    section_positions.sort(key=lambda x: x[0])
    
    # Extract sections
    for i, (start, filename, desc) in enumerate(section_positions):
        if i + 1 < len(section_positions):
            end = section_positions[i + 1][0]
        else:
            end = len(content)
        
        section_content = content[start:end].strip()
        if section_content:
            write_file(css_dir / filename, section_content + "\n")
    
    # Handle content before first section (style tag open, etc.)
    if section_positions:
        first_pos = section_positions[0][0]
        if first_pos > 0:
            preamble = content[:first_pos].strip()
            write_file(css_dir / "_00_base.html", preamble + "\n")
    
    print(f"  ✓ Created {len(section_positions) + 1} CSS files")
    return True


def split_javascript():
    """Split JavaScript into logical modules."""
    print("\n📦 Splitting JavaScript...")
    
    scripts_file = PARTS_DIR / "_scripts.html"
    if not scripts_file.exists():
        print("  ⚠️ _scripts.html not found")
        return False
    
    content = read_file(scripts_file)
    js_dir = PARTS_DIR / "js"
    
    # JavaScript section markers
    sections = [
        (r'<script type="application/json" id="attachments-data">', '_01_json_attachments.html', 'Attachments JSON'),
        (r'<script type="application/json" id="vehicle-data">', '_02_json_vehicle.html', 'Vehicle JSON'),
        (r'<script>\s*\n?\s*let processedDocuments', '_03_init.html', 'Initialization'),
        (r'function openModal\s*\(', '_04_modal_funcs.html', 'Modal Functions'),
        (r'function loadNotes\s*\(', '_05_notes.html', 'Notes'),
        (r'function loadTemplates\s*\(', '_06_templates.html', 'Templates'),
        (r'function loadCommonDocuments\s*\(', '_07_common_docs.html', 'Common Documents'),
        (r'// =+\s*\n\s*// ATTACHMENT HANDLING', '_08_attachment_funcs.html', 'Attachment Functions'),
        (r'function previewAttachment\s*\(', '_09_preview_funcs.html', 'Preview Functions'),
        (r'function setupAttachmentHandlers\s*\(', '_10_attachment_handlers.html', 'Attachment Handlers'),
        (r'// Enhanced Response attachment handling', '_11_dragdrop.html', 'Drag & Drop'),
        (r"document\.getElementById\('replyForm'\)", '_12_reply_form.html', 'Reply Form'),
        (r'// =+\s*Status dropdown', '_13_status.html', 'Status Dropdown'),
        (r'// =+\s*Real-time Socket', '_14_socket.html', 'Socket.IO'),
        (r'\(function\s*socketIO', '_14_socket.html', 'Socket.IO IIFE'),
    ]
    
    # Find section positions
    section_positions = []
    for pattern, filename, desc in sections:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            # Check for duplicate filenames (merge sections)
            existing = [s for s in section_positions if s[1] == filename]
            if not existing:
                section_positions.append((match.start(), filename, desc))
    
    # Sort and deduplicate
    section_positions.sort(key=lambda x: x[0])
    
    # Extract sections
    created = set()
    for i, (start, filename, desc) in enumerate(section_positions):
        if filename in created:
            continue
        
        if i + 1 < len(section_positions):
            end = section_positions[i + 1][0]
        else:
            end = len(content)
        
        section_content = content[start:end].strip()
        if section_content:
            write_file(js_dir / filename, section_content + "\n")
            created.add(filename)
    
    print(f"  ✓ Created {len(created)} JavaScript files")
    return True


def create_final_template():
    """Create the properly ordered final template."""
    print("\n📝 Creating final modular template...")
    
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

    <!-- External Resources -->
    <link rel="preconnect" href="https://cdn.jsdelivr.net">
    <link rel="preconnect" href="https://cdnjs.cloudflare.com">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet" media="all">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" media="all">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet" media="all">
    <link href="/static/css/animations.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.min.js"></script>
    
    <!-- ===== CSS STYLES ===== -->
    <style>
'''
    
    # Add CSS includes in order
    if css_dir.exists():
        css_files = sorted([f.name for f in css_dir.iterdir() if f.is_file()])
        for css_file in css_files:
            template += f"    {{% include 'ticket_detail_parts/css/{css_file}' %}}\n"
    
    template += '''    </style>
</head>

<!-- ===== BODY ===== -->
{% include 'ticket_detail_parts/modals/_body_start.html' %}

<!-- ===== MODALS ===== -->
'''
    
    # Add modal includes in order
    modal_order = [
        '_modal_message.html',
        '_modal_confirm.html',
        '_modal_forward.html',
        '_modal_note.html',
        '_modal_edit_template.html',
        '_modal_document.html',
        '_modal_vehicle_claim.html',
        '_modal_assign.html',
        '_modal_email_template.html',
    ]
    
    for modal_file in modal_order:
        if (modals_dir / modal_file).exists():
            template += f"{{% include 'ticket_detail_parts/modals/{modal_file}' %}}\n"
    
    template += '''
<!-- ===== MAIN CONTENT ===== -->
{% include 'ticket_detail_parts/modals/_main_content.html' %}

<!-- ===== JSON DATA ===== -->
{% include 'ticket_detail_parts/_main_layout.html' %}

<!-- ===== JAVASCRIPT ===== -->
'''
    
    # Add JS includes in order
    if js_dir.exists():
        js_files = sorted([f.name for f in js_dir.iterdir() if f.is_file()])
        for js_file in js_files:
            template += f"{{% include 'ticket_detail_parts/js/{js_file}' %}}\n"
    
    template += '''
</body>
</html>
'''
    
    write_file(TEMPLATE_DIR / "ticket_detail_v3.html", template)
    return True


def main():
    print("\n" + "=" * 60)
    print("  Enhanced Split v3: Proper section extraction")
    print("=" * 60)
    
    if not PARTS_DIR.exists():
        print(f"❌ {PARTS_DIR} not found. Run split_ticket_detail.py first.")
        return
    
    # Clean up old split directories
    import shutil
    for subdir in ['css', 'modals', 'js']:
        dir_path = PARTS_DIR / subdir
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  🗑️ Cleaned {subdir}/")
    
    split_modals_properly()
    split_css_by_comments()
    split_javascript()
    create_final_template()
    
    # Count files
    css_count = len(list((PARTS_DIR / "css").iterdir())) if (PARTS_DIR / "css").exists() else 0
    modals_count = len(list((PARTS_DIR / "modals").iterdir())) if (PARTS_DIR / "modals").exists() else 0
    js_count = len(list((PARTS_DIR / "js").iterdir())) if (PARTS_DIR / "js").exists() else 0
    
    print("\n" + "=" * 60)
    print("  ✅ Complete!")
    print("=" * 60)
    print(f"""
📁 Split files in templates/ticket_detail_parts/:

   📂 css/     {css_count:2d} files - CSS sections by feature
   📂 modals/  {modals_count:2d} files - Individual modal dialogs
   📂 js/      {js_count:2d} files - JavaScript modules
   
📄 New template: templates/ticket_detail_v3.html

🔄 To test:
   1. Rename ticket_detail.html -> ticket_detail_backup.html
   2. Rename ticket_detail_v3.html -> ticket_detail.html
   3. Restart Flask and test
""")


if __name__ == "__main__":
    main()
