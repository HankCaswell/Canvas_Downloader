# Canvas_Downloader
Python Script for downloading all course materials from Canvas LMS. Users simply need to establish environmental variables for their Canvas Tokens and school-specific URLs then run the script to download all course files locally. 


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