---
title: Git Setup & Usage Guide
description: Step-by-step guide to setting up Git, your development environment, and contributing to Millennium Dawn
---

This guide walks you through everything you need to start working on Millennium Dawn. It is written for people with little or no coding experience. Follow each section in order and you will be up and running.

---

## Step 1: Create a GitHub Account

GitHub is the website where all of the mod's files are stored. You need an account to access them.

1. Go to [github.com](https://github.com) and click **Sign up**.
2. Enter your email address, create a password, and pick a username.
3. Check your email for a verification code and enter it on the site.
4. When asked how many people are on your team, choose **Just me**.
5. Choose the **free** account.

Once your account is created, give your GitHub username to **TheBrokenDroid** or **XCezor** so they can add you to the team. If they are unavailable, contact **AngriestBird**. **Playtesters can skip this step** — you do not need to be added to clone the repo.

---

## Step 2: Install a Git Application

A Git application is a program that downloads the mod files to your computer and keeps them in sync with the team. You do not need to type commands — it has buttons for everything.

We recommend **GitKraken** (free): [gitkraken.com](https://www.gitkraken.com/)

Alternatively, you can use **GitHub Desktop**: [desktop.github.com](https://desktop.github.com/download/)

Download and install whichever one you prefer.

---

## Step 3: Clone the Repository

"Cloning" means downloading a copy of all the mod's files to your computer. You only need to do this once.

1. Go to [the Millennium Dawn repository](https://github.com/MillenniumDawn/Millennium-Dawn) on GitHub.
2. Click the green **Code** button and copy the **HTTPS** link. Do not use SSH or GitHub CLI — HTTPS is the simplest option.
3. Open your Git application (GitKraken or GitHub Desktop).
4. Click **Clone a repository** (or **Clone a repository from the Internet** in GitHub Desktop).
5. Paste the HTTPS link you copied.
6. For the **local path** (where the files will be saved), navigate to your HOI4 mod folder:
   - **Windows:** `C:\Users\YOUR_USERNAME\Documents\Paradox Interactive\Hearts of Iron IV\mod`
   - **Linux:** `~/.local/share/Paradox Interactive/Hearts of Iron IV/mod`
   - **macOS:** `~/Documents/Paradox Interactive/Hearts of Iron IV/mod`
7. Click **Clone** and wait for it to finish.

> If you see an "Authentication failed" error, follow the [Authentication Failed guide](/dev-resources/authentication-failed-cloning-repo) to fix it.
>
> If downloading at less than 200 KB/s, the clone may fail. Try again on a faster connection.

---

## Step 4: Enable the Mod in HOI4

1. Open your file explorer and go to the folder where you just cloned the mod (e.g., `Documents/Paradox Interactive/Hearts of Iron IV/mod/Millennium_Dawn`).
2. Find the file called `Millennium_Dawn.mod`. **Copy** it.
3. Go up one folder to the `mod` folder itself.
4. **Paste** the `.mod` file here. You should now have a copy in both the `Millennium_Dawn` folder and the `mod` folder.
5. Launch HOI4. In the Paradox Launcher, click **Playsets**, then **Add more mods**, and enable **Millennium Dawn Dev**.
6. Start the game. If it loads with the mod, you are done with this step.

> **Still loading vanilla?** Make sure the `.mod` file is in the `mod` folder (not just inside `Millennium_Dawn`). If it still does not work, try the [Irony Mod Manager](https://bcssov.github.io/IronyModManager/) as an alternative launcher.
>
> You can move the `Millennium_Dawn` folder to another drive if needed. Just edit the file path inside the `.mod` file to point to the new location. Make sure the path does not contain Cyrillic or special characters.

---

## Step 5: Set Up Your Text Editor

You will be editing plain text files (`.txt` and `.yml`). We recommend **Visual Studio Code** (free): [code.visualstudio.com](https://code.visualstudio.com/Download)

The repo includes a pre-configured workspace that sets up syntax highlighting, error detection, and other useful features for HOI4 modding:

1. Open VSCode.
2. Go to **File** > **Open Workspace from File**.
3. Navigate to the mod folder, then open `.vscode/hoi4_millennium_dawn.code-workspace`.
4. A popup will ask to install recommended extensions. Click **Install All**.

This gives you:

- Paradox syntax highlighting so HOI4 script files are colour-coded and easier to read.
- Automatic trailing whitespace removal on save, which prevents unnecessary merge conflicts.
- Markdown support for editing documentation files.

> **Why a workspace instead of your own settings?** When someone finds a useful extension or setting, they can add it to the workspace file and everyone on the team gets it automatically. Your personal preferences (font size, theme, etc.) stay in your own VSCode settings.

---

## Note for Playtesters

If you are a playtester (not a developer), your setup is done after Step 4. When a tester task is assigned to you:

1. Open your Git application.
2. Click the **Current branch** button (top of the window).
3. Search for the branch name given in the tester task.
4. Switch to that branch and **Pull** to get the latest files.
5. Launch the game and test.

**Playtester instructions end here.** The rest of this guide is for developers.

---

## Developer Environment Setup

This section sets up the tools that automatically check your code for problems when you commit. You need **Python** installed for this.

### Installing Python

1. Go to [python.org/downloads](https://www.python.org/downloads/) and download Python 3.12 or newer.
2. **Windows users:** During installation, check the box that says **"Add Python to PATH"**. This is important — without it, the commands below will not work.
3. Finish the installation.

To verify Python is installed, open a terminal and type:

```bash
python3 --version
```

You should see something like `Python 3.12.x`. On Windows, you may need to use `python` instead of `python3`.

> **What is a terminal?** On Windows, press the **Windows key**, type `cmd`, and open **Command Prompt**. On macOS, open **Terminal** from Applications > Utilities. On Linux, open your terminal application. A terminal lets you type commands that your computer runs.

### Running the Setup Script

Open a terminal, navigate to the Millennium Dawn folder, and run:

```bash
python3 tools/setup.py
```

On Windows, if `python3` does not work, try:

```bash
python tools/setup.py
```

This script does three things for you:

1. **Installs pre-commit** — a tool that checks your code for problems every time you commit.
2. **Sets up git hooks** — connects pre-commit to Git so the checks run automatically. You do not have to remember to run them.
3. **Installs tool dependencies** — a couple of Python packages (`requests` and `pillow`) that some development tools need.

Once it finishes, you are set up. To check that everything is working at any time, run:

```bash
python3 tools/setup.py --check
```

### What Are Pre-commit Hooks?

When you make a commit (save your changes to Git), pre-commit hooks automatically scan your files for common problems:

- Wrong indentation (should be tabs, not spaces)
- Encoding issues in localisation files
- Missing or mismatched braces
- Trailing whitespace that clutters diffs

If a hook finds a problem, one of two things happens:

- **It fixes the problem for you** and asks you to commit again (just run your commit a second time).
- **It tells you what to fix** with a clear error message. Fix the issue, then commit again.

You do not need to memorize any rules. The hooks catch mistakes automatically.

### How Hooks Work in Different Git Applications

Pre-commit hooks work differently depending on which Git application you use. Here is what to expect:

**Terminal / Command Line (full support)**

If you commit using `git commit` in a terminal, hooks run automatically every time. This is the most reliable method and what CI uses. No extra setup is needed beyond `python3 tools/setup.py`.

**GitKraken (works, with one caveat)**

GitKraken runs hooks when you commit through its interface. However, GitKraken uses its own process environment, which sometimes cannot find Python or pre-commit on your system. If you see an error like `pre-commit: command not found` when committing in GitKraken:

1. Go to **File** > **Preferences** > **General**.
2. Make sure **Use Custom Terminal** is not overriding your PATH.
3. Try closing and reopening GitKraken after installing Python and running `tools/setup.py`. GitKraken picks up PATH changes on restart.
4. If hooks still do not run, you can run them manually in a terminal before committing:

```bash
pre-commit run --all-files
```

Then commit in GitKraken as normal. The hooks will not block you if the files are already clean.

**GitHub Desktop (limited support on Windows)**

GitHub Desktop on Windows often uses a bundled version of Git with a restricted environment. This means it may not be able to find `python3` or `pre-commit`, even if both are installed on your system. When this happens, hooks silently fail or show a "Did you forget to activate your virtualenv?" error.

On macOS and Linux, GitHub Desktop generally works fine because it inherits your shell's PATH.

If hooks are not running in GitHub Desktop on Windows:

1. Run hooks manually in a terminal before committing:

```bash
pre-commit run --all-files
```

2. Then commit in GitHub Desktop as normal.

Alternatively, consider switching to **GitKraken** or committing from the terminal for a smoother experience. The CI pipeline will also catch any issues that hooks would have flagged, so your code is always validated before merge regardless of which application you use.

### Development Tools

The repo includes helpful tools for analysis, validation, and content generation. You can see everything available and run tools by name:

```bash
python3 tools/run.py --list
```

To run a specific tool:

```bash
python3 tools/run.py estimate_gdp USA
python3 tools/run.py find_idea common/ideas/Greek.txt
```

You do not need to remember which folder a tool is in — `run.py` finds it for you. Partial names also work (e.g., `find_idea` matches `find_idea_references`).

### Docs Site Setup (Optional)

If you are editing the documentation website (the files under `docs/`), you need two extra tools: [Node.js 24+](https://nodejs.org/) and [Bun](https://bun.sh/). Once those are installed, run:

```bash
python3 tools/setup.py --docs
```

To preview the docs site on your computer:

```bash
cd docs
bun run dev
```

This opens a local preview at `http://localhost:4321/`. For full details, see [CONTRIBUTING.md](https://github.com/MillenniumDawn/Millennium-Dawn/blob/main/CONTRIBUTING.md).

---

## Understanding Git

This section explains how Git works. If you already know Git, skip ahead to [Making a Commit](#making-a-commit--pushing).

### What is Git?

Git is a **version control system** — it tracks every change made to every file. Think of it like an unlimited undo history that the entire team shares. If something breaks, we can look at what changed and roll it back.

We use **GitHub** to store the files online so everyone can access them.

### Branches

A **branch** is like a separate copy of the mod where you can make changes without affecting anyone else. Each project or feature gets its own branch. For example, Iranian content would be in a branch called `iranian-content`.

When you are done, your branch gets **merged** into the main branch so everyone gets your changes.

### Commits

A **commit** is a snapshot of your changes with a short description of what you did. Think of it like a save point in a game — you can always go back to any previous commit. Example: _"Fixed all the bugs in the Argentina focus tree"_.

### Push and Pull

- **Push** uploads your commits from your computer to GitHub so others can see them.
- **Pull** downloads commits from GitHub that others have pushed.

Until you push, your commits only exist on your computer.

### Shared Branches

The team maintains a few communal branches that multiple people work on:

- **master / main** — The current release-ready version. Content reaches here through approved pull requests.
- **gfx-input** — All graphics go here, regardless of what content they are for. See the [Art Standards](/dev-resources/art-standards/) for details.
- **bug-fixes** — General bug fix work. Most fixes should be done here unless told otherwise.
- **map-work** — Map-related changes.

Work on your own feature branch unless you are contributing to one of these. Do not commit to shared branches without checking with the team first.

---

## Making a Commit & Pushing

This is the day-to-day workflow: you edit files, then save and upload your changes.

1. Edit mod files on your computer as normal (using VSCode, Notepad++, or any text editor).
2. When you are ready to save your progress, open **GitKraken**.
3. You will see your changed files listed. Click **Stage All Changes** to prepare them for committing.
4. Type a short summary of what you changed in the **Summary** field. For example: _"Added new focus for Turkish military reform"_. A description is optional.
5. Click **Commit Changes**.
6. Click **Push** to upload your commit to GitHub.

That's it. Your changes are now on the server and visible to the team.

---

## Pulling Changes

Other team members will be pushing their own changes. To download their latest work:

1. Select the branch you want to update.
2. Click **Pull** in the top bar.

GitKraken checks for new changes in the background, so you will usually see a notification when there is something to pull.

---

## Updating Your Branch from Master

You should regularly update your branch with changes from the master branch. This keeps your files current and prevents conflicts later.

1. Switch to the **master** branch.
2. Click **Pull** to download the latest changes.
3. Switch back to your own branch.
4. Right-click your branch name and select the merge option (e.g., "Merge master into your-branch-name").

The more often you do this, the fewer merge conflicts you will encounter.

---

## Merge Conflicts

A **merge conflict** happens when two people edit the same lines in the same file. Git cannot decide which version to keep, so it asks you to choose.

### How Do You Know You Have One?

Your Git application will show orange warning signs or a "conflict" message after a merge or pull.

### What Does a Conflict Look Like?

If you open the conflicted file in a text editor, you will see markers like this:

```
<<<<<<< HEAD:events/MD4_Init.txt
(your version of the code)
=======
(the other person's version of the code)
>>>>>>> master:events/MD_Init.txt
```

- Everything between `<<<<<<< HEAD` and `=======` is **your** code.
- Everything between `=======` and `>>>>>>>` is **their** code.

### How to Fix It

1. Look at both versions and decide which one to keep. Sometimes you need parts of both.
2. Delete the version you do not want.
3. Delete the conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`).
4. Save the file.
5. Check the rest of the file — there can be multiple conflicts in one file.
6. Once all conflicts are resolved, commit and push.

> For a video walkthrough, see the [Git Conflict Resolution guide](https://youtu.be/edoJhO7ZkCs).

---

## Pull Requests

A **pull request** (PR) is how your code gets merged into the master branch. Only submit a PR when your work is complete and not causing crashes or errors.

1. Go to the [Millennium Dawn repository](https://github.com/MillenniumDawn/Millennium-Dawn) on GitHub.
2. Click **Pull requests** > **New Pull Request**.
3. Set the **source** to your branch and the **target** to `master`.
4. Click **Create Pull Request**.
5. Fill out the title (a short summary) and description (what you changed and why).
6. Assign yourself and add any relevant labels or milestones.
7. Click **Submit**.

### What Happens Next

Two things must happen before your code is merged:

1. **CI validation** — An automated system scans your code for errors. If it passes, you see a green checkmark. If it fails (red X), click through to see what went wrong, fix it, and push a new commit. The check runs again automatically.
2. **Team review** — A team leader reviews your changes and either approves them or requests changes.

> Update your branch from master as often as possible. Stale branches cause more merge conflicts and make reviews harder.

---

## FAQ & Troubleshooting

**The mod loads as vanilla (no Millennium Dawn content).**
Make sure the `Millennium_Dawn.mod` file is in the `mod` folder (one level above the `Millennium_Dawn` folder). If it still does not work, try the [Irony Mod Manager](https://bcssov.github.io/IronyModManager/).

**Can I test someone else's branch?**
Yes. In your Git application, switch to their branch and pull. The files on your computer update instantly. Switch back to your own branch when you are done.

**I accidentally committed to the wrong branch.**
Let a team lead know. Changes can be reverted down to individual files. It is not the end of the world, but it saves everyone time if you double-check your branch before committing.

**The `python3` command is not found (Windows).**
Try using `python` instead. If that does not work either, you may have missed the "Add Python to PATH" checkbox during installation. Reinstall Python and make sure to check that box.

**Pre-commit hooks are failing and I do not understand the error.**
Ask in the Discord development channel. Include the error message — someone will help you sort it out.

**Hooks are not running when I commit in GitKraken or GitHub Desktop.**
GUI applications sometimes cannot find Python or pre-commit on your system. See the [How Hooks Work in Different Git Applications](#how-hooks-work-in-different-git-applications) section above. The quickest workaround is to run `pre-commit run --all-files` in a terminal before committing.

**I see "Did you forget to activate your virtualenv?" when committing.**
This means your Git application cannot find pre-commit. This is common on Windows with GitHub Desktop. Run `pre-commit run --all-files` in a terminal instead, or switch to GitKraken for better hook support.

---

## GitKraken Setup (for New Users or Migration from GitHub Desktop)

If you are setting up GitKraken for the first time or switching from GitHub Desktop:

1. Download [GitKraken Desktop](https://www.gitkraken.com/) (free) and install it.
2. Open GitKraken and click **Let's Open a repository!**
3. Confirm your name and email for commits, then click **Use These for Git Commits**.
4. Click **Open Repo**, browse to your Millennium Dawn folder, and select it.
5. Click **Pull** to make sure you have the latest files.
6. Go to **File** > **Preferences** and adjust these settings:
   - **Max commits in graph:** `500` (keeps the app responsive)
   - **Auto-Fetch Interval:** `10` minutes (checks for team changes regularly)
   - **External Editor:** Visual Studio Code (if not already set)
7. Close preferences. In the left sidebar, click **Local** under the branches list.
8. Select all local branches you do not need (hold Shift and click), then right-click and delete them. Keep only the branch you are working on.
