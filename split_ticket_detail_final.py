#!/usr/bin/env python3
"""
FINAL CORRECTED Split Script v4

This script fixes all the issues from previous splits by:
1. Properly handling script tag boundaries
2. Removing duplicate style tags
3. Ensuring proper ordering of includes
4. Maintaining complete, valid HTML/JS blocks

Run from the AutoAssist__portal directory:
    python split_ticket_detail_final.py
"""

import os
import re
import shutil
from pathlib import Path

TEMPLATE_DIR = Path("templates")
PARTS_DIR = TEMPLATE_DIR / "ticket_detail_parts"
ORIGINAL_FILE = TEMPLATE_DIR / "ticket_detail.html"


def read_file(filepath):
    """Read file content."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def write_file(filepath, content, desc=""):
    """Write content to file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    size_kb = len(content) / 1024
    lines = content.count('\n') + 1
    print(f"  ✓ {filepath.name:40} {size_kb:7.1f} KB  {lines:5} lines  {desc}")


def clean_parts_dir():
    """Remove old split directories."""
    for subdir in ['css', 'modals', 'js']:
        dir_path = PARTS_DIR / subdir
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  🗑️  Removed old {subdir}/")


def find_section(content, start_marker, end_marker=None, include_end=False):
    """Find content between markers."""
    start_match = re.search(start_marker, content, re.IGNORECASE | re.DOTALL)
    if not start_match:
        return None, -1, -1
    
    start_pos = start_match.start()
    
    if end_marker:
        end_match = re.search(end_marker, content[start_pos:], re.IGNORECASE | re.DOTALL)
        if end_match:
            end_pos = start_pos + end_match.start()
            if include_end:
                end_pos = start_pos + end_match.end()
        else:
            end_pos = len(content)
    else:
        end_pos = len(content)
    
    return content[start_pos:end_pos], start_pos, end_pos


def split_original_file():
    """Split the original ticket_detail.html into proper parts."""
    print("\n📖 Reading original ticket_detail.html...")
    
    # Check if original exists or use backup
    if ORIGINAL_FILE.exists():
        content = read_file(ORIGINAL_FILE)
    elif (TEMPLATE_DIR / "ticket_detail_original.html").exists():
        content = read_file(TEMPLATE_DIR / "ticket_detail_original.html")
        print("   Using ticket_detail_original.html as source")
    else:
        print("❌ No original file found!")
        return False
    
    print(f"   File size: {len(content) / 1024:.1f} KB, {content.count(chr(10)) + 1} lines")
    
    # === EXTRACT HEAD SECTION ===
    print("\n📦 Extracting HEAD section...")
    head_match = re.search(r'<head>(.*?)</head>', content, re.DOTALL)
    if head_match:
        head_content = head_match.group(1)
        
        # Extract styles from head
        style_match = re.search(r'<style>(.*?)</style>', head_content, re.DOTALL)
        if style_match:
            css_content = style_match.group(1).strip()
            write_file(PARTS_DIR / "_styles.html", css_content, "All CSS styles")
    
    # === EXTRACT BODY SECTION ===
    print("\n📦 Extracting BODY section...")
    body_match = re.search(r'<body[^>]*>(.*?)</body>', content, re.DOTALL)
    if body_match:
        body_content = body_match.group(1)
        
        # Find body opening tag with classes
        body_open_match = re.search(r'<body[^>]*>', content)
        body_tag = body_open_match.group(0) if body_open_match else '<body>'
        
        # === EXTRACT MODALS ===
        print("\n📦 Extracting modals...")
        modals_dir = PARTS_DIR / "modals"
        
        # Body start (background, notifications) - before first modal
        body_start_match = re.search(r'^(.*?)(?=<div\s+id="messageModal")', body_content, re.DOTALL)
        if body_start_match:
            body_start = body_tag + "\n" + body_start_match.group(1).strip()
            write_file(modals_dir / "_00_body_start.html", body_start, "Body tag + background")
        
        # Extract each modal individually
        modal_ids = [
            ("messageModal", "Message expansion"),
            ("confirmModal", "Confirm close"),
            ("forwardModal", "Forward ticket"),
            ("noteModal", "Add note"),
            ("editTemplateModal", "Edit template"),
            ("documentModal", "Document upload"),
            ("vehicleClaimModal", "Vehicle/claim edit"),
            ("assignModal", "Assignment"),
            ("emailTemplateModal", "Email template"),
        ]
        
        for i, (modal_id, desc) in enumerate(modal_ids, 1):
            modal_content = extract_div_by_id(body_content, modal_id)
            if modal_content:
                write_file(modals_dir / f"_{i:02d}_{modal_id}.html", modal_content.strip() + "\n", desc)
        
        # Main content (after modals, before scripts)
        main_layout_match = re.search(
            r'(<!--\s*Main Layout Container.*?)(?=<script\s+type="application/json")',
            body_content, 
            re.DOTALL | re.IGNORECASE
        )
        if main_layout_match:
            main_content = main_layout_match.group(1).strip()
            write_file(modals_dir / "_10_main_content.html", main_content + "\n", "Main layout")
        
        # === EXTRACT SCRIPTS ===
        print("\n📦 Extracting JavaScript...")
        js_dir = PARTS_DIR / "js"
        
        # JSON data blocks
        json_attachments = re.search(
            r'(<script\s+type="application/json"\s+id="attachments-data">.*?</script>)',
            body_content, re.DOTALL
        )
        if json_attachments:
            write_file(js_dir / "_01_json_attachments.html", json_attachments.group(1).strip() + "\n", "Attachments JSON")
        
        json_vehicle = re.search(
            r'(<script\s+type="application/json"\s+id="vehicle-data">.*?</script>)',
            body_content, re.DOTALL
        )
        if json_vehicle:
            write_file(js_dir / "_02_json_vehicle.html", json_vehicle.group(1).strip() + "\n", "Vehicle JSON")
        
        # Main JavaScript (find the main script block)
        main_js_match = re.search(
            r'(<script>.*?let processedDocuments.*?</script>)',
            body_content, 
            re.DOTALL
        )
        
        if main_js_match:
            main_js = main_js_match.group(1)
            
            # Split the script into logical sections
            # Remove script tags for processing
            js_inner = re.sub(r'^<script>\s*', '', main_js)
            js_inner = re.sub(r'\s*</script>$', '', js_inner)
            
            # Find key function boundaries for splitting
            js_sections = []
            
            # Section 1: Initial variables and basic functions
            init_end = js_inner.find("function openModal")
            if init_end > 0:
                js_sections.append(("_03_init_vars.html", js_inner[:init_end].strip(), "Init variables"))
            
            # Section 2: Modal functions
            modal_start = js_inner.find("function openModal")
            modal_end = js_inner.find("function loadNotes")
            if modal_start > 0 and modal_end > modal_start:
                js_sections.append(("_04_modal_funcs.html", js_inner[modal_start:modal_end].strip(), "Modal functions"))
            
            # Section 3: Notes functions
            notes_start = js_inner.find("function loadNotes")
            notes_end = js_inner.find("function loadTemplates")
            if notes_start > 0 and notes_end > notes_start:
                js_sections.append(("_05_notes.html", js_inner[notes_start:notes_end].strip(), "Notes"))
            
            # Section 4: Templates functions  
            templates_start = js_inner.find("function loadTemplates")
            templates_end = js_inner.find("function loadCommonDocuments")
            if templates_start > 0 and templates_end > templates_start:
                js_sections.append(("_06_templates.html", js_inner[templates_start:templates_end].strip(), "Templates"))
            
            # Section 5: Common documents
            docs_start = js_inner.find("function loadCommonDocuments")
            docs_end = js_inner.find("// ====") 
            if docs_end < docs_start:
                docs_end = js_inner.find("function previewAttachment")
            if docs_start > 0 and docs_end > docs_start:
                js_sections.append(("_07_common_docs.html", js_inner[docs_start:docs_end].strip(), "Common docs"))
            
            # Section 6: Attachment preview/download functions
            preview_start = js_inner.find("function previewAttachment")
            preview_end = js_inner.find("function setupAttachmentHandlers")
            if preview_start > 0 and preview_end > preview_start:
                js_sections.append(("_08_preview_funcs.html", js_inner[preview_start:preview_end].strip(), "Preview functions"))
            
            # Section 7: Attachment handlers (main drag/drop system)
            handlers_start = js_inner.find("function setupAttachmentHandlers")
            # Find the end - look for next major section
            handlers_end = js_inner.find("// Status dropdown")
            if handlers_end < handlers_start:
                handlers_end = js_inner.find("function updateStatusBadge")
            if handlers_start > 0 and handlers_end > handlers_start:
                js_sections.append(("_09_attachment_handlers.html", js_inner[handlers_start:handlers_end].strip(), "Attachment handlers"))
            
            # Section 8: Status dropdown and UI functions
            status_start = js_inner.find("// Status dropdown")
            if status_start < 0:
                status_start = js_inner.find("function updateStatusBadge")
            status_end = js_inner.find("// Real-time Socket.IO")
            if status_end < 0:
                status_end = js_inner.find("(function socketIO")
            if status_start > 0 and status_end > status_start:
                js_sections.append(("_10_status_ui.html", js_inner[status_start:status_end].strip(), "Status/UI"))
            
            # Section 9: Socket.IO (everything remaining)
            socket_start = js_inner.find("// Real-time Socket.IO")
            if socket_start < 0:
                socket_start = js_inner.find("(function socketIO")
            if socket_start > 0:
                socket_content = js_inner[socket_start:].strip()
                js_sections.append(("_11_socket.html", socket_content, "Socket.IO"))
            
            # Write all sections wrapped in script tags
            for filename, js_content, desc in js_sections:
                if js_content:
                    # Wrap in script tags
                    full_content = "<script>\n" + js_content + "\n</script>\n"
                    write_file(js_dir / filename, full_content, desc)
    
    return True


def extract_div_by_id(content, div_id):
    """Extract a complete div element by its ID, handling nested divs."""
    pattern = rf'<div\s+id="{div_id}"'
    match = re.search(pattern, content)
    if not match:
        return None
    
    start_pos = match.start()
    pos = start_pos
    div_count = 0
    found_first = False
    
    while pos < len(content):
        # Look for div tags
        if content[pos:pos+4].lower() == '<div':
            div_count += 1
            found_first = True
            pos += 4
        elif content[pos:pos+6].lower() == '</div>':
            div_count -= 1
            pos += 6
            if found_first and div_count == 0:
                return content[start_pos:pos]
        else:
            pos += 1
    
    return None


def create_modular_template():
    """Create the main modular template that includes all parts."""
    print("\n📝 Creating modular template...")
    
    css_dir = PARTS_DIR / "css"
    modals_dir = PARTS_DIR / "modals"
    js_dir = PARTS_DIR / "js"
    
    template = '''<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="AutoAssistGroup Support Ticket #{{ ticket.ticket_id }} - {{ (ticket.subject or 'No Subject')[:100] }}">
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
    
    <!-- CSS Styles -->
    <style>
    {% include 'ticket_detail_parts/_styles.html' %}
    </style>
</head>

<!-- Body Start -->
{% include 'ticket_detail_parts/modals/_00_body_start.html' %}

<!-- Modals -->
'''
    
    # Add modal includes
    if modals_dir.exists():
        modal_files = sorted([f.name for f in modals_dir.iterdir() if f.is_file() and f.name.startswith('_0') and 'Modal' in f.name])
        for modal_file in modal_files:
            template += f"{{% include 'ticket_detail_parts/modals/{modal_file}' %}}\n"
    
    template += '''
<!-- Main Content -->
{% include 'ticket_detail_parts/modals/_10_main_content.html' %}

<!-- JSON Data -->
'''
    
    # Add JS includes
    if js_dir.exists():
        js_files = sorted([f.name for f in js_dir.iterdir() if f.is_file()])
        for js_file in js_files:
            template += f"{{% include 'ticket_detail_parts/js/{js_file}' %}}\n"
    
    template += '''
</body>
</html>
'''
    
    write_file(TEMPLATE_DIR / "ticket_detail_modular_v4.html", template, "Main modular template")
    return True


def main():
    print("\n" + "=" * 70)
    print("  FINAL Split Script v4 - Complete Rebuild")  
    print("=" * 70)
    
    # Clean up old directories
    print("\n🧹 Cleaning old split directories...")
    clean_parts_dir()
    
    # Split the original file
    if not split_original_file():
        return
    
    # Create the modular template
    create_modular_template()
    
    # Summary
    print("\n" + "=" * 70)
    print("  ✅ SPLIT COMPLETE!")
    print("=" * 70)
    
    # Count files
    def count_files(dir_path):
        return len(list(dir_path.iterdir())) if dir_path.exists() else 0
    
    modals_count = count_files(PARTS_DIR / "modals")
    js_count = count_files(PARTS_DIR / "js")
    
    print(f"""
📁 Created files in templates/ticket_detail_parts/:

   📄 _styles.html     (All CSS in one file)
   📂 modals/  ({modals_count} files) - Body start, modals, main content  
   📂 js/      ({js_count} files) - JavaScript modules with proper <script> tags

📄 New template: templates/ticket_detail_modular_v4.html

🔄 To test the modular version:
   1. Stop Flask
   2. Rename: ticket_detail.html -> ticket_detail_backup.html
   3. Rename: ticket_detail_modular_v4.html -> ticket_detail.html  
   4. Restart Flask and test
""")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
