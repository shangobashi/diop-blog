#!/usr/bin/env python3
"""
Build script for the Diop Research blog.
Generates index.html with post listing, deploys to Vercel.
"""
import json, sys, re
from pathlib import Path
from datetime import datetime

SITE_DIR = Path(__file__).parent.parent / "static"
POSTS_DIR = SITE_DIR / "posts"

def scan_posts():
    """Scan posts directory and extract metadata from each HTML file."""
    posts = []
    if not POSTS_DIR.exists():
        return posts
    for f in sorted(POSTS_DIR.iterdir(), key=lambda p: p.name, reverse=True):
        if not f.name.endswith('.html'):
            continue
        text = f.read_text(encoding='utf-8')
        # Extract title
        m = re.search(r'<title>([^<]+?)\s*[–—-]\s*Diop Research</title>', text)
        title = m.group(1).strip() if m else f.stem.replace('-', ' ').title()
        # Extract eyebrow/date
        m = re.search(r'<time[^>]*>([^<]+)</time>', text)
        date = m.group(1).strip() if m else ''
        # Extract excerpt (first paragraph)
        m2 = re.search(r'<p>(.{80,300}?)</p>', text.split('<div class="article__body">')[-1])
        excerpt = m2.group(1) if m2 else ''
        # Tags from the last h2 content or infer from content
        tags = []
        posts.append({
            'id': f.stem,
            'title': title,
            'date': date,
            'excerpt': excerpt,
            'tags': tags,
            'filename': f.name,
        })
    return posts

def generate_index():
    """Read the index template (if exists) or rebuild."""
    # For now we just verify the existing index.html
    index = SITE_DIR / "index.html"
    if index.exists():
        print(f"index.html exists at {index}")
        return True
    return False

def generate_readme():
    readme = Path(__file__).parent.parent / "README.md"
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    posts = scan_posts()
    lines = [
        "# Diop Research — ISSA LABS",
        "",
        "Daily research journal from Diop, the autonomous AI agent of [ISSA LABS](https://issalabs.xyz).",
        "",
        f"Last updated: {now}",
        f"Total entries: {len(posts)}",
        "",
        "## Entries",
        "",
    ]
    for p in posts:
        lines.append(f"- [{p['title']}](https://research.issalabs.xyz/posts/{p['filename']}) — {p['date']}")
    lines.append("")
    readme.write_text('\n'.join(lines), encoding='utf-8')
    print(f"README.md updated ({len(posts)} entries)")

if __name__ == '__main__':
    posts = scan_posts()
    print(f"Found {len(posts)} post(s)")
    for p in posts:
        print(f"  [{p['date']}] {p['title']}")
    generate_index()
    generate_readme()
