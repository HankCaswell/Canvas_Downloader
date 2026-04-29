# Canvas Archiver — Setup Guide

This guide takes you from zero to a complete archive of your Canvas course materials. No Python experience required. You just need to be able to copy and paste commands into a terminal and follow instructions in order.

**Time estimate:** 30–60 minutes for first-time setup, plus download time (usually 30 minutes to a few hours, depending on how much content you have).

**You'll end up with** a folder on your computer containing all your course files, assignments, pages, syllabi, announcements, and discussions, organized by course, that you can keep forever.

---

## What you need before you start

- A computer running macOS or Windows
- Your Canvas login (the school's website where you view classes)
- About 5–100 GB of free disk space (run the size estimator first if you're unsure — instructions below)
- The `canvas_archiver.py` script file from this repository

---

## Step 1: Get a Canvas access token

This is a long string of letters and numbers that lets the script log in to Canvas as you. Without it, nothing works.

1. Open Canvas in your web browser and log in normally.
2. Click your **Account** icon (usually a circle with your initials or photo, top-left of the page).
3. Click **Settings**.
4. Scroll down until you find a section called **Approved Integrations**.
5. Click the button **+ New Access Token**.
6. In the "Purpose" field, type something like `Archiver`.
7. Leave the "Expires" field blank (so the token doesn't expire while you're using it).
8. Click **Generate Token**.
9. **Copy the long token string immediately** and paste it somewhere safe (like a temporary text file). Canvas only shows you this once — if you close the page without copying, you'll have to delete the token and make a new one.

Also note your **Canvas URL** — the address bar of your browser when you're logged in to Canvas. It looks something like `https://canvas.your-school.edu` or `https://your-school.instructure.com`. You'll need this too.

> **Important:** treat your access token like a password. Anyone who has it can read everything in your Canvas account. Don't share it, don't post it online, and don't email it to yourself. We'll delete it when we're done.

---

## Step 2: Set up your computer

Now follow the section for your operating system. Skip the other one.

- [Mac instructions](#mac-instructions)
- [Windows instructions](#windows-instructions)

---

## Mac instructions

### 2A. Open the Terminal

1. Press **Cmd + Space** to open Spotlight Search.
2. Type `Terminal` and press **Enter**.
3. A window opens with text and a blinking cursor. This is the Terminal — where you'll type commands.

You'll know commands worked when you see no error messages and a fresh prompt appears (a line ending in `$` or `%`).

### 2B. Install Python (if you don't already have it)

In the Terminal window, type this command and press **Enter**:

```bash
python3 --version
```

- **If it prints something like `Python 3.11.5`,** you have Python. Skip to step 2C.
- **If it says "command not found" or pops up a window asking to install Command Line Tools,** click **Install** in that popup and wait (5–10 minutes). When it's done, run `python3 --version` again to confirm.

### 2C. Make a folder for the project

```bash
mkdir ~/canvas-archiver
cd ~/canvas-archiver
```

What this does: creates a new folder called `canvas-archiver` in your home directory, then moves into it. Every command from here on assumes you're in this folder.

### 2D. Save the script into this folder

You need to put `canvas_archiver.py` in the folder you just created. Two ways:

**Option 1 — Download from GitHub:**
On the GitHub page for this repository, click `canvas_archiver.py`, then click the **Download raw file** button (a small download icon, top right of the file view). Then in Terminal:

```bash
mv ~/Downloads/canvas_archiver.py ~/canvas-archiver/
```

**Option 2 — Clone the whole repository:**
If you'd rather grab everything at once:

```bash
cd ~
git clone https://github.com/yourusername/repo-name.git canvas-archiver
cd canvas-archiver
```

(Replace the URL with the actual repository URL.)

Confirm the file is there:

```bash
ls
```

You should see `canvas_archiver.py` listed.

### 2E. Set up a virtual environment

A virtual environment is just a folder that keeps this project's Python tools separate from anything else on your computer. Create one:

```bash
python3 -m venv .venv
```

This takes a few seconds. When it's done, activate it:

```bash
source .venv/bin/activate
```

**Success looks like:** your prompt now starts with `(.venv)` — for example, `(.venv) hank@MacBook canvas-archiver %`. That `(.venv)` prefix means you're inside the environment.

> If you ever close Terminal and come back later, you'll need to run `cd ~/canvas-archiver` and `source .venv/bin/activate` again before running the script. The setup itself is one-time, but activation is per-Terminal-session.

### 2F. Install the required packages

```bash
pip install canvasapi requests tqdm
```

You'll see a flurry of installation messages. When it's done (30–60 seconds), the prompt comes back and you're ready.

**Skip ahead to [Step 3: Run the archiver](#step-3-run-the-archiver).**

---

## Windows instructions

### 2A. Install Python (if you don't already have it)

1. Open the **Start menu** and type `PowerShell`. Click **Windows PowerShell** to open it.
2. In the window that opens, type this and press **Enter**:

   ```powershell
   py --version
   ```

   - **If it prints something like `Python 3.13.0`,** you have Python. Skip to step 2B.
   - **If it says "py is not recognized" or similar,** install Python:
     1. Go to [python.org/downloads](https://www.python.org/downloads/) in your browser.
     2. Click the big yellow **Download Python** button.
     3. Run the installer.
     4. **On the first screen, check the box that says "Add python.exe to PATH"** at the bottom. This is critical — easy to miss.
     5. Click **Install Now**. Wait for it to finish.
     6. Close PowerShell completely and open a new PowerShell window. Run `py --version` again to confirm.

### 2B. Allow PowerShell to run scripts (one-time setup)

By default, Windows blocks PowerShell scripts. The Python virtual environment uses one, so you need to allow it. In PowerShell, run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

When it asks to confirm, type `Y` and press **Enter**.

### 2C. Enable long file paths (one-time setup)

Windows traditionally limits file paths to 260 characters. Canvas folders can have long names, so this limit causes problems. Fix it:

1. Close your current PowerShell window.
2. Open the **Start menu**, type `PowerShell`, **right-click** Windows PowerShell, and choose **Run as administrator**. Click **Yes** on the security prompt.
3. In the new PowerShell window (titled "Administrator: Windows PowerShell"), run:

   ```powershell
   New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
   ```

4. Close that window.
5. **Restart your computer.** This change only takes effect after a reboot.

After your computer restarts, open PowerShell normally (not as administrator) and continue.

### 2D. Make a folder for the project

In PowerShell:

```powershell
mkdir $HOME\Documents\canvas-archiver
cd $HOME\Documents\canvas-archiver
```

This creates a folder called `canvas-archiver` inside your Documents folder, then moves into it.

### 2E. Save the script into this folder

You need to put `canvas_archiver.py` in the folder you just created. Two ways:

**Option 1 — Download from GitHub:**
On the GitHub page for this repository, click `canvas_archiver.py`, then click the **Download raw file** button (small download icon, top right of the file view). Save it to your Downloads folder. Then in PowerShell:

```powershell
Move-Item $HOME\Downloads\canvas_archiver.py .
```

**Option 2 — Clone the whole repository:**
If git is installed, you can grab everything at once:

```powershell
cd $HOME\Documents
git clone https://github.com/yourusername/repo-name.git canvas-archiver
cd canvas-archiver
```

(Replace the URL with the actual repository URL. If `git` isn't installed, use Option 1.)

Confirm the file is there:

```powershell
dir
```

You should see `canvas_archiver.py` listed.

### 2F. Set up a virtual environment

```powershell
py -m venv .venv
```

This takes a few seconds. When it's done, activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

**Success looks like:** your prompt now starts with `(.venv)` — for example, `(.venv) PS C:\Users\You\Documents\canvas-archiver>`. That prefix means you're inside the environment.

> If you ever close PowerShell and come back later, you'll need to run `cd $HOME\Documents\canvas-archiver` and `.\.venv\Scripts\Activate.ps1` again before running the script. The setup itself is one-time, but activation is per-PowerShell-session.

### 2G. Install the required packages

```powershell
pip install canvasapi requests tqdm
```

You'll see a flurry of installation messages. When it's done (30–60 seconds), the prompt comes back and you're ready.

---

## Step 3: Run the archiver

You're all set up. Now you'll actually run the script.

### 3A. Do a test run first ("dry run")

A dry run logs in to Canvas, lists what it *would* download, and stops without writing anything. This confirms your token works and previews the workload.

**Mac:**

```bash
python canvas_archiver.py --dry-run --url "https://canvas.your-school.edu" --token "paste_your_token_here"
```

**Windows:**

```powershell
python canvas_archiver.py --dry-run --url "https://canvas.your-school.edu" --token "paste_your_token_here"
```

Replace `https://canvas.your-school.edu` with your actual Canvas URL and `paste_your_token_here` with the token you copied earlier. Keep the quotation marks.

**What you should see:** within a few seconds, a line saying `Logged in as: Your Name`, followed by your courses listed one by one with what would be downloaded for each. If you see "Authentication failed," your token is wrong — double-check you copied it correctly.

### 3B. Run the real archiver

When the dry run looks good, run it for real by removing `--dry-run`:

**Mac:**

```bash
python canvas_archiver.py --url "https://canvas.your-school.edu" --token "paste_your_token_here"
```

**Windows:**

```powershell
python canvas_archiver.py --url "https://canvas.your-school.edu" --token "paste_your_token_here"
```

This will run for a while — anywhere from 15 minutes to a few hours depending on how much content you have. You'll see progress as it works through each course. **Keep your computer plugged in and don't let it sleep** until it finishes (Settings → Power → set "When plugged in, sleep after" to Never; flip it back when done).

When it finishes, you'll see a line like:

```
Done. Archived 14 course(s) in 1247s -> /Users/you/canvas-archiver/canvas_archive
```

That path is where your archive lives.

### 3C. Useful options

You can add any of these to the command:

- `--skip files` — skip downloading files (just grab text content; very fast, much smaller archive)
- `--active-only` — only currently-active courses (skip past terms)
- `--courses 12345 67890` — only specific courses, identified by their Canvas course ID (find the ID in the URL when viewing a course in your browser: `canvas.../courses/12345`)
- `--output "/path/to/somewhere/else"` — save the archive somewhere other than the default

Example combining a few:

```bash
python canvas_archiver.py --skip files --active-only --url "https://canvas.your-school.edu" --token "paste_your_token_here"
```

---

## Step 4: Look at your archive

Open Finder (Mac) or File Explorer (Windows) and navigate to your project folder. Inside, you'll see a `canvas_archive` folder. Open it.

You'll find one folder per course, named something like `MBA703_Operations_4038691`. Inside each course folder:

- `_course.json` — basic course info
- `syllabus.html` — the course syllabus (open by double-clicking; it'll open in your browser)
- `files/` — all uploaded files, organized by Canvas folder
- `pages/` — Canvas pages saved as HTML
- `assignments/` — assignment descriptions, your submissions, and grades
- `modules.json` — the structure of course modules
- `announcements/` — instructor announcements
- `discussions/` — discussion topics and replies
- `quizzes.json` — quiz titles and metadata

The HTML files open in any web browser. JSON files are readable in any text editor (or just inspect them in TextEdit/Notepad).

**Spot-check a few courses** to make sure things look right. If a course is missing content, you can re-run the script with just that course using `--courses <course_id>`.

---

## Step 5: When you're done

### Back up your archive

The archive is just a folder. Back it up however you normally back up files:

- Copy it to an external drive
- Zip it and upload to Dropbox / Google Drive / iCloud
- Copy to a backup service

Do this **before you graduate**, because once Canvas access is revoked, you can't re-run this.

### Revoke your Canvas token

You don't need it anymore. Leaving it active is a small but unnecessary risk.

1. Go to Canvas → **Account** → **Settings**.
2. Scroll to **Approved Integrations**.
3. Find the token you created (the "Archiver" one).
4. Click the **trash can** icon next to it. Confirm.

Then close any text file where you saved the token, and empty your trash.

---

## Troubleshooting

### "Authentication failed" or 401 errors

Your token is wrong, expired, or doesn't match the Canvas URL. Double-check both. Tokens are case-sensitive and very long — easy to truncate when copying. If unsure, generate a fresh token.

### "Command not found: python" (Mac)

Use `python3` instead of `python`. (Inside an activated virtual environment, plain `python` should work.)

### "py is not recognized" (Windows)

Python isn't installed, or wasn't added to PATH during installation. Reinstall from [python.org](https://www.python.org/downloads/) and make sure to check "Add python.exe to PATH" on the first installer screen.

### "Activate.ps1 cannot be loaded because running scripts is disabled" (Windows)

You skipped step 2B. Run this once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Then try activating again.

### "The filename or extension is too long" (Windows)

You skipped step 2C, or didn't reboot after enabling long paths. Re-do step 2C, restart your computer, and run the script again.

### The script seems frozen

Look closely — there's usually a progress bar that updates per file completed, not per byte. A single large video can make it look frozen for several minutes while it downloads. If it's been more than 15 minutes with no movement at all, press **Ctrl+C** to stop, then run again. The script picks up where it left off (already-downloaded files are skipped).

### Some files failed with "No such file or directory" errors

This is the long-paths problem on Windows. Make sure you completed step 2C (enable long paths) and rebooted. Then re-run the script — it'll fill in the missing files.

### I want to start over

Delete the `canvas_archive` folder and run the script again:

**Mac:**
```bash
rm -rf canvas_archive
```

**Windows:**
```powershell
Remove-Item -Recurse -Force canvas_archive
```

### I want to stop and resume later

Press **Ctrl+C** to stop. Next time, navigate back to the folder, activate the virtual environment, and run the same command. Already-downloaded content is skipped automatically.

### Coming back the next day

To run the script again later, you need to re-activate the virtual environment first. Open a new Terminal/PowerShell window and:

**Mac:**
```bash
cd ~/canvas-archiver
source .venv/bin/activate
python canvas_archiver.py --url "..." --token "..."
```

**Windows:**
```powershell
cd $HOME\Documents\canvas-archiver
.\.venv\Scripts\Activate.ps1
python canvas_archiver.py --url "..." --token "..."
```

You don't need to redo the install or setup steps — just `cd` and activate.

---

## A note on safety

Your Canvas access token is sensitive. While following this guide:

- **Don't paste your token into any website**, even one that claims to help with Canvas.
- **Don't include your token in screenshots** if you post questions for help.
- **Don't commit your token to git** if you put this folder under version control.
- **Revoke the token when you're done.** It's a 5-second operation in Canvas settings.

If you ever suspect your token has been exposed (you posted it somewhere, you ran an untrusted script with it, etc.), revoke it immediately in Canvas and generate a new one. Revoked tokens stop working instantly.
