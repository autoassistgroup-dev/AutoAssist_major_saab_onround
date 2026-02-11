#!/usr/bin/env python3
"""
SIMPLE SPLIT v5 - A more conservative approach

This creates just 4-5 large files instead of many small ones:
1. _styles.html - All CSS
2. _body_modals.html - Body start + all modals  
3. _main_content.html - Main layout/content
4. _scripts.html - ALL JavaScript (kept together to avoid breaking)

This is safer because JavaScript often has interdependencies.
"""

import re
import shutil
from pathlib import Path

TEMPLATE_DIR = Path("templates")
PARTS_DIR = TEMPLATE_DIR / "ticket_detail_parts"


def read_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def write_file(filepath, content, desc=""):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    size_kb = len(content) / 1024
    lines = content.count('\n') + 1
    print(f"  ✓ {filepath.name:35} {size_kb:8.1f} KB  {lines:6} lines  {desc}")


def main():
    print("\n" + "=" * 70)
    print("  SIMPLE SPLIT v5 - Conservative Approach")
    print("=" * 70)
    
    # Find the original file
    if (TEMPLATE_DIR / "ticket_detail.html").exists():
        source_file = TEMPLATE_DIR / "ticket_detail.html"
    elif (TEMPLATE_DIR / "ticket_detail_original.html").exists():
        source_file = TEMPLATE_DIR / "ticket_detail_original.html"
    else:
        print("❌ No source file found!")
        return
    
    print(f"\n📖 Reading {source_file.name}...")
    content = read_file(source_file)
    print(f"   Size: {len(content) / 1024:.1f} KB, {content.count(chr(10)) + 1} lines")
    
    # Clean old split directories
    for subdir in ['css', 'modals', 'js']:
        dir_path = PARTS_DIR / subdir
        if dir_path.exists():
            shutil.rmtree(dir_path)
    
    # === EXTRACT CSS ===
    print("\n📦 Extracting sections...")
    
    # Find the style block
    style_match = re.search(r'<style>(.*?)</style>', content, re.DOTALL)
    if style_match:
        css_content = style_match.group(1).strip()
        write_file(PARTS_DIR / "_styles.html", css_content, "All CSS")
    
    # === EXTRACT BODY (before scripts) ===
    # Find body start to before JSON script blocks
    body_match = re.search(
        r'(<body[^>]*>.*?)(?=<script\s+type="application/json")',
        content,
        re.DOTALL
    )
    if body_match:
        body_content = body_match.group(1).strip()
        
        # Split body into modals and main content
        # Find main layout container
        main_layout_idx = body_content.find('<!-- Main Layout Container')
        if main_layout_idx > 0:
            # Everything before main layout is body start + modals
            modals_content = body_content[:main_layout_idx].strip()
            main_content = body_content[main_layout_idx:].strip()
            
            write_file(PARTS_DIR / "_body_modals.html", modals_content, "Body + modals")
            write_file(PARTS_DIR / "_main_content.html", main_content, "Main layout")
        else:
            write_file(PARTS_DIR / "_body_all.html", body_content, "Body content")
    
    # === EXTRACT ALL SCRIPTS ===
    # Find from JSON scripts to closing body
    scripts_match = re.search(
        r'(<script\s+type="application/json".*?</body>)',
        content,
        re.DOTALL
    )
    if scripts_match:
        scripts_content = scripts_match.group(1).strip()
        # Remove the </body> tag as it will be in the template
        scripts_content = re.sub(r'\s*</body>\s*$', '', scripts_content)
        write_file(PARTS_DIR / "_scripts.html", scripts_content, "All JS")
    
    # === CREATE MODULAR TEMPLATE ===
    print("\n📝 Creating modular template...")
    
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

<!-- Body Start & Modals -->
{% include 'ticket_detail_parts/_body_modals.html' %}

<!-- Main Content -->
{% include 'ticket_detail_parts/_main_content.html' %}

<!-- All Scripts (JSON data + JavaScript) -->
{% include 'ticket_detail_parts/_scripts.html' %}

</body>
</html>
'''
    
    write_file(TEMPLATE_DIR / "ticket_detail_simple.html", template, "Modular template")
    
    # === VERIFY ===
    print("\n🔍 Verifying split files...")
    
    # Check that we have all the critical parts
    styles = read_file(PARTS_DIR / "_styles.html")
    modals = read_file(PARTS_DIR / "_body_modals.html") if (PARTS_DIR / "_body_modals.html").exists() else ""
    main = read_file(PARTS_DIR / "_main_content.html") if (PARTS_DIR / "_main_content.html").exists() else ""
    scripts = read_file(PARTS_DIR / "_scripts.html")
    
    # Check for key patterns
    checks = [
        ("CSS theme", "PROFESSIONAL DARK THEME" in styles),
        ("Body tag", "<body" in modals),
        ("Message modal", "messageModal" in modals),
        ("Confirm modal", "confirmModal" in modals),
        ("Vehicle modal", "vehicleClaimModal" in modals),
        ("Main layout", "Main Layout Container" in main or "Main Layout Container" in modals),
        ("JSON attachments", "attachments-data" in scripts),
        ("JSON vehicle", "vehicle-data" in scripts),
        ("DOMContentLoaded", "DOMContentLoaded" in scripts),
        ("Socket.IO", "socket" in scripts.lower()),
        ("Reply form", "replyForm" in scripts),
        ("Notifications", "showNotification" in scripts),
    ]
    
    all_ok = True
    for name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"   {status} {name}")
        if not passed:
            all_ok = False
    
    print("\n" + "=" * 70)
    if all_ok:
        print("  ✅ SPLIT COMPLETE - All checks passed!")
    else:
        print("  ⚠️ SPLIT COMPLETE - Some checks failed (review above)")
    print("=" * 70)
    
    print(f"""
📁 Created files in templates/ticket_detail_parts/:
   
   📄 _styles.html       - All CSS styles
   📄 _body_modals.html  - Body tag, background, notifications, modals
   📄 _main_content.html - Main layout with header, conversation, sidebar
   📄 _scripts.html      - All JavaScript (JSON data + main script)

📄 New template: templates/ticket_detail_simple.html

🔄 To test:
   1. Stop Flask
   2. copy templates\\ticket_detail.html templates\\ticket_detail_backup.html
   3. copy templates\\ticket_detail_simple.html templates\\ticket_detail.html
   4. Restart Flask and test
   5. If broken, restore: copy templates\\ticket_detail_backup.html templates\\ticket_detail.html
""")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
