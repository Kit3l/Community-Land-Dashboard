#!/usr/bin/env python3
"""
DLCI Community Profile Generator
=================================
Reads data/communities.json and the profile template, then generates
one HTML file per community into the correct county sub-folder.

Usage:
    python3 generate.py

Run this script from the root of the dlci-system folder.
Output structure:
    communities/
        turkana/
            alale.html
            lorengippi.html
            ...
        samburu/
            nairimirimo.html
            ...
        (one folder per county slug)
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).parent
DATA_FILE   = ROOT / "data" / "communities.json"
TEMPLATE    = ROOT / "assets" / "profile-template.html"
OUTPUT_DIR  = ROOT / "communities"

# ── Status helpers ─────────────────────────────────────────────────────────────
STATUS_LABELS = {
    "green":  "✅ Registered",
    "orange": "🟠 Adjudicated — not yet complete",
    "red":    "🔴 Un-adjudicated",
}

PROGRESS = {
    "green":  (100, "#2e7d32"),
    "orange": ( 55, "#ef6c00"),
    "red":    ( 15, "#c62828"),
}

# ── Timeline builder ───────────────────────────────────────────────────────────
def build_timeline(community):
    status = community["status"]
    adj_start = community.get("adjudicationStart")
    reg_date  = community.get("registrationDate")

    def fmt_date(d):
        if not d:
            return "—"
        try:
            return datetime.strptime(d, "%Y-%m-%d").strftime("%B %Y")
        except:
            return d

    # Stage 1: Community mobilisation
    stage1_class = "done"
    stage1_note  = "Community organised and DLCI engagement begun"

    # Stage 2: Adjudication started
    stage2_class = "done" if adj_start else ("active" if status == "red" else "done")
    stage2_date  = fmt_date(adj_start) if adj_start else ("In progress" if status != "red" else "Pending")

    # Stage 3: Adjudication complete
    stage3_class = "done" if status in ("green", "orange") else "future"
    stage3_date  = "Complete" if status in ("green",) else ("In progress" if status == "orange" else "Not yet started")

    # Stage 4: Registration
    stage4_class = "done" if status == "green" else "future"
    stage4_date  = fmt_date(reg_date) if reg_date else ("Pending" if status != "green" else "—")

    items = [
        (stage1_class, "✓", "Community mobilisation", stage1_note, "Complete"),
        (stage2_class, "📋" if adj_start else "⏳", "Adjudication process started", "Filing with County Land Management Board", stage2_date),
        (stage3_class, "✓" if stage3_class == "done" else "⏳", "Adjudication completed", "All boundaries agreed and gazetted", stage3_date),
        (stage4_class, "📜" if stage4_class == "done" else "⏳", "Community Land Register certificate issued", "Final registration under CLA 2016", stage4_date),
    ]

    html = ""
    for cls, icon, label, note, date in items:
        html += f"""
          <div class="tl-item">
            <div class="tl-dot {cls}">{icon}</div>
            <div class="tl-content">
              <div class="tl-date">{date}</div>
              <div class="tl-label">{label}</div>
              <div class="tl-note">{note}</div>
            </div>
          </div>"""
    return html

# ── Description block ──────────────────────────────────────────────────────────
def build_description(community):
    desc = community.get("description", "").strip()
    if not desc:
        return ""
    return f'<p class="description">{desc}</p>'

# ── Cert badge ─────────────────────────────────────────────────────────────────
def cert_info(status):
    if status == "green":
        return ("", "Available")
    return ("pending", "Pending upload")

# ── Main generator ─────────────────────────────────────────────────────────────
def generate():
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)

    template = TEMPLATE.read_text(encoding="utf-8")

    total = 0
    for county_name, county_data in data["counties"].items():
        county_slug = county_data["slug"]
        county_dir  = OUTPUT_DIR / county_slug
        county_dir.mkdir(parents=True, exist_ok=True)

        for community in county_data["communities"]:
            name   = community["name"]
            slug   = community["slug"]
            status = community["status"]

            lat = community.get("lat")
            lng = community.get("lng")
            lat_display = f"{lat:.6f}° N" if lat else "Not recorded"
            lng_display = f"{lng:.6f}° E" if lng else "Not recorded"
            coords_display = f"{lat_display}, {lng_display}" if lat else "Coordinates not yet recorded"

            pct, color = PROGRESS[status]
            cert_cls, cert_lbl = cert_info(status)

            size = community.get("size") or "—"
            pop  = community.get("population")
            mem  = community.get("registeredMembers")

            page = template
            page = page.replace("{{COMMUNITY_NAME}}", name)
            page = page.replace("{{COUNTY_NAME}}", county_name)
            page = page.replace("{{COUNTY_SLUG}}", county_slug)
            page = page.replace("{{STATUS_CLASS}}", status)
            page = page.replace("{{STATUS_LABEL}}", STATUS_LABELS[status])
            page = page.replace("{{SIZE}}", size)
            page = page.replace("{{SIZE_PENDING}}", "pending" if size == "—" else "")
            page = page.replace("{{POPULATION}}", f"{pop:,}" if pop else "—")
            page = page.replace("{{POP_PENDING}}", "pending" if not pop else "")
            page = page.replace("{{REGISTERED_MEMBERS}}", f"{mem:,}" if mem else "—")
            page = page.replace("{{MEM_PENDING}}", "pending" if not mem else "")
            page = page.replace("{{LAT}}", coords_display)
            page = page.replace("{{LNG}}", "")
            page = page.replace("{{LAT_JS}}", str(lat) if lat else "null")
            page = page.replace("{{LNG_JS}}", str(lng) if lng else "null")
            page = page.replace("{{TIMELINE_ITEMS}}", build_timeline(community))
            page = page.replace("{{DESCRIPTION_BLOCK}}", build_description(community))
            page = page.replace("{{CERT_STATUS}}", cert_cls)
            page = page.replace("{{CERT_LABEL}}", cert_lbl)
            page = page.replace("{{PROGRESS_PCT}}", str(pct))
            page = page.replace("{{PROGRESS_COLOR}}", color)

            # Title tag
            page = page.replace(
                "<title>{{COMMUNITY_NAME}} — DLCI Community Profile</title>",
                f"<title>{name} — DLCI Community Profile</title>"
            )

            out_path = county_dir / f"{slug}.html"
            out_path.write_text(page, encoding="utf-8")
            total += 1
            print(f"  ✓  {county_name:12}  →  communities/{county_slug}/{slug}.html")

    print(f"\n{'─'*55}")
    print(f"  Generated {total} community profile pages.")
    print(f"  All files are in:  {OUTPUT_DIR}")
    print(f"{'─'*55}\n")
    print("  Next step: open dashboard.html and verify pin links work.")

if __name__ == "__main__":
    generate()
