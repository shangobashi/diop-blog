#!/usr/bin/env python3
"""
Build script for the Diop Research blog.
Generates index.html with post listing, deploys to Vercel.
"""
import json, sys, re, hashlib, html
from pathlib import Path
from datetime import datetime, date
from difflib import SequenceMatcher
from collections import defaultdict

SITE_DIR = Path(__file__).parent.parent / "static"
POSTS_DIR = SITE_DIR / "posts"

def strip_tags(fragment):
    """Return readable text from a small HTML fragment."""
    fragment = re.sub(r'<script[\s\S]*?</script>', ' ', fragment, flags=re.I)
    fragment = re.sub(r'<style[\s\S]*?</style>', ' ', fragment, flags=re.I)
    fragment = re.sub(r'<[^>]+>', ' ', fragment)
    return html.unescape(re.sub(r'\s+', ' ', fragment)).strip()


def extract_lang_body(text, lang='en'):
    """Extract one language body for duplicate-content checks."""
    m = re.search(
        rf'<div class="article__body"[^>]*data-lang-body="{lang}"[^>]*>([\s\S]*?)(?=<div class="article__body"[^>]*data-lang-body=|</article>)',
        text,
    )
    return strip_tags(m.group(1)) if m else ''


def parse_post_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), '%B %d, %Y').date()
    except ValueError:
        return None


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
        post_date = m.group(1).strip() if m else ''
        english_body = extract_lang_body(text, 'en')
        # Extract excerpt (first paragraph)
        m2 = re.search(r'<p>(.{80,300}?)</p>', text.split('<div class="article__body">')[-1])
        excerpt = m2.group(1) if m2 else ''
        # Tags from the last h2 content or infer from content
        tags = []
        posts.append({
            'id': f.stem,
            'title': title,
            'date': post_date,
            'parsed_date': parse_post_date(post_date),
            'excerpt': excerpt,
            'tags': tags,
            'filename': f.name,
            'english_body': english_body,
            'english_body_hash': hashlib.sha256(english_body.encode('utf-8')).hexdigest(),
        })
    return posts

def verify_post_integrity(posts):
    """Reject duplicate/future live posts before README, commit, or deploy."""
    failures = []
    today = date.today()

    by_date = defaultdict(list)
    by_title = defaultdict(list)
    by_body_hash = defaultdict(list)

    for post in posts:
        if post['parsed_date'] is None:
            failures.append(f"{post['id']}: invalid or missing <time> date: {post['date']!r}")
        elif post['parsed_date'] > today:
            failures.append(f"{post['id']}: future-dated post ({post['date']}) exceeds today ({today.isoformat()})")
        by_date[post['date']].append(post['id'])
        by_title[post['title'].strip().lower()].append(post['id'])
        if post['english_body']:
            by_body_hash[post['english_body_hash']].append(post['id'])
        else:
            failures.append(f"{post['id']}: missing English article body for duplicate-content check")

    for post_date, ids in sorted(by_date.items()):
        if post_date and len(ids) > 1:
            failures.append(f"duplicate publication date {post_date}: {', '.join(ids)}")
    for title, ids in sorted(by_title.items()):
        if title and len(ids) > 1:
            failures.append(f"duplicate article title {title!r}: {', '.join(ids)}")
    for body_hash, ids in sorted(by_body_hash.items()):
        if len(ids) > 1:
            failures.append(f"exact duplicate English body {body_hash[:12]}: {', '.join(ids)}")

    # Similarity is a guardrail, not a literary censor: 0.80 catches cloned
    # entries while allowing adjacent research topics to share vocabulary.
    for i, left in enumerate(posts):
        for right in posts[i + 1:]:
            ratio = SequenceMatcher(None, left['english_body'][:12000], right['english_body'][:12000]).ratio()
            if ratio >= 0.80:
                failures.append(f"near-duplicate English body ({ratio:.3f}): {left['id']} vs {right['id']}")

    if failures:
        print("ERROR: post integrity check failed", file=sys.stderr)
        for failure in failures:
            print("  " + failure, file=sys.stderr)
        return False

    print("Post integrity verified: unique dates, titles, and article bodies; no future-dated live posts")
    return True


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
    if not verify_post_integrity(posts):
        sys.exit(1)
    if not generate_index(posts):
        sys.exit(1)
    generate_readme()
