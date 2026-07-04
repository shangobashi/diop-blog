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

def generate_index(posts=None):
    """Verify the hand-curated index is complete before any deploy can proceed."""
    posts = posts or scan_posts()
    index = SITE_DIR / "index.html"
    if not index.exists():
        print(f"ERROR: index.html missing at {index}", file=sys.stderr)
        return False

    text = index.read_text(encoding='utf-8')
    card_ids = re.findall(r'data-post="([^"]+)"', text)
    post_ids = [p['id'] for p in posts]
    missing = [pid for pid in post_ids if pid not in card_ids]
    extra = [cid for cid in card_ids if cid not in post_ids]
    duplicates = sorted({cid for cid in card_ids if card_ids.count(cid) > 1})

    print(f"index.html exists at {index}")
    print(f"Index cards: {len(card_ids)}; post files: {len(post_ids)}")

    if missing or extra or duplicates or len(card_ids) != len(post_ids):
        print("ERROR: index.html post-card register is inconsistent with static/posts", file=sys.stderr)
        if missing:
            print("  Missing cards: " + ', '.join(missing), file=sys.stderr)
        if extra:
            print("  Extra cards: " + ', '.join(extra), file=sys.stderr)
        if duplicates:
            print("  Duplicate cards: " + ', '.join(duplicates), file=sys.stderr)
        return False

    print("Index card register verified complete")
    return True

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
    if not generate_index(posts):
        sys.exit(1)
    generate_readme()
