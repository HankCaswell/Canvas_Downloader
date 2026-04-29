"""
Canvas LMS Archiver (v2)
------------------------
Downloads your Canvas courses (files, pages, assignments, modules, announcements,
discussions, syllabus) for offline preservation.

v2 change: Canvas folder paths are preserved as real nested directories
(e.g. files/Lectures/Week 1/Slides/lecture.pdf) rather than collapsed into
underscore-joined names. Output paths from v1 will not match v2, so the
resume logic won't recognize a v1 archive — start with a fresh output folder.

Uses the official Canvas REST API via the `canvasapi` library — no scraping,
no broken selectors, no ToS issues.

SETUP
=====
1. Generate a Canvas access token:
   - Log in to Canvas in your browser
   - Account -> Settings -> "+ New Access Token"
   - Name it something like "Archiver", leave expiry blank or far out
   - Copy the token (you won't see it again)

2. Install dependencies:
       pip install canvasapi requests tqdm

3. Set environment variables (or edit the CONFIG block below):
       export CANVAS_URL="https://canvas.your-school.edu"
       export CANVAS_TOKEN="your_token_here"
       export CANVAS_OUTPUT_DIR="./canvas_archive"

4. Run:
       python canvas_archiver.py

   Optional flags:
       --courses 12345 67890     # only archive specific course IDs
       --include-concluded       # also archive concluded/past courses (default: yes)
       --skip files,discussions  # skip certain content types
       --dry-run                 # list what would be downloaded, don't download

The script is resumable — already-downloaded files are skipped on reruns.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

try:
    import requests
    from canvasapi import Canvas
    from canvasapi.exceptions import (
        CanvasException,
        Forbidden,
        ResourceDoesNotExist,
        Unauthorized,
    )
    from tqdm import tqdm
except ImportError as e:
    print(f"Missing dependency: {e.name}")
    print("Install with:  pip install canvasapi requests tqdm")
    sys.exit(1)


# ---------- Config ----------

@dataclass
class Config:
    canvas_url: str
    token: str
    output_dir: Path
    course_ids: list[int] = field(default_factory=list)  # empty = all
    include_concluded: bool = True
    skip: set[str] = field(default_factory=set)
    dry_run: bool = False


CONTENT_TYPES = {
    "syllabus",
    "files",
    "pages",
    "assignments",
    "modules",
    "announcements",
    "discussions",
    "quizzes",  # metadata only — not the questions
}


# ---------- Helpers ----------

INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize(name: str, max_len: int = 120) -> str:
    """Make a string safe to use as a filename on Windows/Mac/Linux."""
    name = INVALID_CHARS.sub("_", name).strip().rstrip(".")
    return name[:max_len] or "untitled"


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text or "", encoding="utf-8")


def html_wrap(title: str, body_html: str) -> str:
    """Wrap raw Canvas HTML in a minimal standalone document."""
    safe_title = (title or "").replace("<", "&lt;").replace(">", "&gt;")
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>{safe_title}</title>"
        "<style>body{font-family:system-ui,sans-serif;max-width:900px;"
        "margin:2em auto;padding:0 1em;line-height:1.5}"
        "img{max-width:100%}pre,code{background:#f4f4f4;padding:2px 4px}"
        "</style></head><body>"
        f"<h1>{safe_title}</h1>{body_html or ''}</body></html>"
    )


def safe_call(fn, *args, default=None, **kwargs):
    """Call a Canvas API method, swallowing 'not available' errors."""
    try:
        return fn(*args, **kwargs)
    except (Forbidden, Unauthorized, ResourceDoesNotExist):
        return default
    except CanvasException as e:
        print(f"  ! Canvas error: {e}")
        return default


# ---------- Downloader ----------

class CourseArchiver:
    def __init__(self, cfg: Config, canvas: Canvas, course):
        self.cfg = cfg
        self.canvas = canvas
        self.course = course
        self.course_dir = (
            cfg.output_dir
            / sanitize(f"{course.course_code or 'course'}_{course.id}")
        )
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Bearer {cfg.token}"

    def run(self):
        print(f"\n=== {self.course.name} (id={self.course.id}) ===")
        if not self.cfg.dry_run:
            self.course_dir.mkdir(parents=True, exist_ok=True)
            write_json(
                self.course_dir / "_course.json",
                {
                    "id": self.course.id,
                    "name": getattr(self.course, "name", None),
                    "course_code": getattr(self.course, "course_code", None),
                    "start_at": getattr(self.course, "start_at", None),
                    "end_at": getattr(self.course, "end_at", None),
                    "term": str(getattr(self.course, "term", None)),
                    "workflow_state": getattr(self.course, "workflow_state", None),
                },
            )

        steps = [
            ("syllabus", self.archive_syllabus),
            ("files", self.archive_files),
            ("pages", self.archive_pages),
            ("assignments", self.archive_assignments),
            ("modules", self.archive_modules),
            ("announcements", self.archive_announcements),
            ("discussions", self.archive_discussions),
            ("quizzes", self.archive_quizzes),
        ]
        for name, fn in steps:
            if name in self.cfg.skip:
                continue
            try:
                fn()
            except Exception as e:  # never let one section kill the rest
                print(f"  ! {name} failed: {e}")

    # ----- syllabus -----
    def archive_syllabus(self):
        # Need the include[] param to get syllabus_body
        course = safe_call(
            self.canvas.get_course, self.course.id, include=["syllabus_body"]
        )
        body = getattr(course, "syllabus_body", None) if course else None
        if not body:
            return
        print("  syllabus")
        if self.cfg.dry_run:
            return
        write_text(
            self.course_dir / "syllabus.html",
            html_wrap("Syllabus", body),
        )

    # ----- files -----
    def archive_files(self):
        # Build a folder map so we mirror Canvas's folder structure
        folders = safe_call(lambda: list(self.course.get_folders()), default=[])
        folder_map = {f.id: f.full_name for f in (folders or [])}

        files = safe_call(lambda: list(self.course.get_files()), default=[])
        if not files:
            return

        print(f"  files: {len(files)}")
        for f in tqdm(files, desc="    downloading", leave=False):
            # full_name looks like "course files/Lectures/Week 1/Slides" —
            # strip the "course files/" prefix, then split into real directory
            # segments so the on-disk structure mirrors Canvas instead of
            # collapsing everything into a single underscore-joined folder.
            rel_folder = folder_map.get(f.folder_id, "")
            rel_folder = re.sub(r"^course files/?", "", rel_folder)
            parts = [sanitize(p) for p in rel_folder.split("/") if p]
            target = self.course_dir.joinpath(
                "files", *parts, sanitize(f.display_name)
            )

            if target.exists() and target.stat().st_size == (f.size or 0):
                continue  # already downloaded
            if self.cfg.dry_run:
                continue

            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                # Stream so big files don't blow up memory
                with self.session.get(f.url, stream=True, timeout=60) as r:
                    r.raise_for_status()
                    with open(target, "wb") as out:
                        for chunk in r.iter_content(chunk_size=64 * 1024):
                            out.write(chunk)
            except Exception as e:
                print(f"    ! failed {f.display_name}: {e}")

    # ----- pages -----
    def archive_pages(self):
        pages = safe_call(lambda: list(self.course.get_pages()), default=[])
        if not pages:
            return
        print(f"  pages: {len(pages)}")
        out_dir = self.course_dir / "pages"
        for p in pages:
            # Listing returns stubs; fetch full page for body
            full = safe_call(self.course.get_page, p.url)
            if not full:
                continue
            if self.cfg.dry_run:
                continue
            write_text(
                out_dir / f"{sanitize(full.title)}.html",
                html_wrap(full.title, getattr(full, "body", "") or ""),
            )

    # ----- assignments -----
    def archive_assignments(self):
        assignments = safe_call(
            lambda: list(self.course.get_assignments()), default=[]
        )
        if not assignments:
            return
        print(f"  assignments: {len(assignments)}")
        out_dir = self.course_dir / "assignments"
        for a in assignments:
            if self.cfg.dry_run:
                continue
            base = out_dir / sanitize(f"{a.id}_{a.name}")
            write_json(
                base.with_suffix(".json"),
                {
                    "id": a.id,
                    "name": a.name,
                    "due_at": getattr(a, "due_at", None),
                    "points_possible": getattr(a, "points_possible", None),
                    "submission_types": getattr(a, "submission_types", None),
                    "html_url": getattr(a, "html_url", None),
                    "rubric": getattr(a, "rubric", None),
                },
            )
            desc = getattr(a, "description", None)
            if desc:
                write_text(
                    base.with_suffix(".html"),
                    html_wrap(a.name, desc),
                )
            # Your own submissions (text + comments + attachments metadata)
            sub = safe_call(a.get_submission, "self")
            if sub:
                write_json(
                    base.parent / f"{sanitize(str(a.id) + '_' + a.name)}_submission.json",
                    {
                        "score": getattr(sub, "score", None),
                        "grade": getattr(sub, "grade", None),
                        "submitted_at": getattr(sub, "submitted_at", None),
                        "body": getattr(sub, "body", None),
                        "url": getattr(sub, "url", None),
                        "attachments": getattr(sub, "attachments", None),
                    },
                )

    # ----- modules -----
    def archive_modules(self):
        modules = safe_call(lambda: list(self.course.get_modules()), default=[])
        if not modules:
            return
        print(f"  modules: {len(modules)}")
        structure = []
        for m in modules:
            items = safe_call(lambda: list(m.get_module_items()), default=[]) or []
            structure.append(
                {
                    "id": m.id,
                    "name": m.name,
                    "position": getattr(m, "position", None),
                    "items": [
                        {
                            "title": getattr(it, "title", None),
                            "type": getattr(it, "type", None),
                            "html_url": getattr(it, "html_url", None),
                            "url": getattr(it, "url", None),
                            "content_id": getattr(it, "content_id", None),
                        }
                        for it in items
                    ],
                }
            )
        if not self.cfg.dry_run:
            write_json(self.course_dir / "modules.json", structure)

    # ----- announcements -----
    def archive_announcements(self):
        # Announcements are discussion topics flagged as announcements
        topics = safe_call(
            lambda: list(self.course.get_discussion_topics(only_announcements=True)),
            default=[],
        )
        if not topics:
            return
        print(f"  announcements: {len(topics)}")
        out_dir = self.course_dir / "announcements"
        for t in topics:
            if self.cfg.dry_run:
                continue
            posted = (getattr(t, "posted_at", "") or "").replace(":", "-")[:19]
            fname = sanitize(f"{posted}_{t.title}") + ".html"
            write_text(
                out_dir / fname,
                html_wrap(t.title, getattr(t, "message", "") or ""),
            )

    # ----- discussions -----
    def archive_discussions(self):
        topics = safe_call(
            lambda: list(self.course.get_discussion_topics()), default=[]
        )
        # Filter out announcements (already covered)
        topics = [t for t in (topics or []) if not getattr(t, "is_announcement", False)]
        if not topics:
            return
        print(f"  discussions: {len(topics)}")
        out_dir = self.course_dir / "discussions"
        for t in topics:
            if self.cfg.dry_run:
                continue
            base = out_dir / sanitize(f"{t.id}_{t.title}")
            entries = safe_call(lambda: list(t.get_topic_entries()), default=[]) or []
            replies_data = []
            for e in entries:
                sub_replies = safe_call(lambda: list(e.get_replies()), default=[]) or []
                replies_data.append(
                    {
                        "user": getattr(e, "user_name", None),
                        "created_at": getattr(e, "created_at", None),
                        "message": getattr(e, "message", None),
                        "replies": [
                            {
                                "user": getattr(r, "user_name", None),
                                "created_at": getattr(r, "created_at", None),
                                "message": getattr(r, "message", None),
                            }
                            for r in sub_replies
                        ],
                    }
                )
            write_json(
                base.with_suffix(".json"),
                {
                    "title": t.title,
                    "message": getattr(t, "message", None),
                    "posted_at": getattr(t, "posted_at", None),
                    "entries": replies_data,
                },
            )

    # ----- quizzes -----
    def archive_quizzes(self):
        # Metadata only — questions/answers usually aren't accessible to students
        # post-submission, and dumping them feels academic-integrity-adjacent.
        quizzes = safe_call(lambda: list(self.course.get_quizzes()), default=[])
        if not quizzes:
            return
        print(f"  quizzes (metadata): {len(quizzes)}")
        if self.cfg.dry_run:
            return
        write_json(
            self.course_dir / "quizzes.json",
            [
                {
                    "id": q.id,
                    "title": q.title,
                    "due_at": getattr(q, "due_at", None),
                    "points_possible": getattr(q, "points_possible", None),
                    "question_count": getattr(q, "question_count", None),
                    "description": getattr(q, "description", None),
                    "html_url": getattr(q, "html_url", None),
                }
                for q in quizzes
            ],
        )


# ---------- Orchestration ----------

def get_courses(cfg: Config, canvas: Canvas) -> Iterable:
    if cfg.course_ids:
        for cid in cfg.course_ids:
            c = safe_call(canvas.get_course, cid)
            if c:
                yield c
        return

    user = canvas.get_current_user()
    state = ["available"]
    if cfg.include_concluded:
        state.append("completed")
    courses = user.get_courses(state=state, include=["term"])
    yield from courses


def parse_args() -> Config:
    p = argparse.ArgumentParser(description="Archive Canvas LMS courses")
    p.add_argument("--url", default=os.environ.get("CANVAS_URL"))
    p.add_argument("--token", default=os.environ.get("CANVAS_TOKEN"))
    p.add_argument(
        "--output",
        default=os.environ.get("CANVAS_OUTPUT_DIR", "./canvas_archive"),
    )
    p.add_argument(
        "--courses",
        nargs="*",
        type=int,
        default=[],
        help="Specific course IDs to archive (default: all)",
    )
    p.add_argument(
        "--include-concluded",
        action="store_true",
        default=True,
        help="Include past/concluded courses (default: yes)",
    )
    p.add_argument(
        "--active-only",
        action="store_true",
        help="Only currently-active courses",
    )
    p.add_argument(
        "--skip",
        default="",
        help=f"Comma-separated content types to skip. Options: {','.join(sorted(CONTENT_TYPES))}",
    )
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if not args.url or not args.token:
        p.error(
            "Canvas URL and token required. Set CANVAS_URL and CANVAS_TOKEN env "
            "vars, or pass --url and --token."
        )

    skip = {s.strip() for s in args.skip.split(",") if s.strip()}
    bad = skip - CONTENT_TYPES
    if bad:
        p.error(f"Unknown skip types: {bad}. Valid: {CONTENT_TYPES}")

    return Config(
        canvas_url=args.url.rstrip("/"),
        token=args.token,
        output_dir=Path(args.output).expanduser().resolve(),
        course_ids=args.courses,
        include_concluded=not args.active_only,
        skip=skip,
        dry_run=args.dry_run,
    )


def main():
    cfg = parse_args()
    print(f"Canvas:    {cfg.canvas_url}")
    print(f"Output:    {cfg.output_dir}")
    if cfg.dry_run:
        print("DRY RUN — no files will be written")

    canvas = Canvas(cfg.canvas_url, cfg.token)

    # Validate token early
    try:
        me = canvas.get_current_user()
        print(f"Logged in as: {me.name} (id={me.id})\n")
    except Unauthorized:
        print("Authentication failed. Check your token.")
        sys.exit(1)

    cfg.output_dir.mkdir(parents=True, exist_ok=True)

    start = time.time()
    n = 0
    for course in get_courses(cfg, canvas):
        try:
            CourseArchiver(cfg, canvas, course).run()
            n += 1
        except Exception as e:
            print(f"! Course {getattr(course, 'id', '?')} failed: {e}")

    elapsed = time.time() - start
    print(f"\nDone. Archived {n} course(s) in {elapsed:.0f}s -> {cfg.output_dir}")


if __name__ == "__main__":
    main()
