---
title: Git Setup & Usage Guide
description: Guide to setting up Git, GitHub Desktop/GitKraken, and contributing to Millennium Dawn
---

This guide provides clear instructions on how to use Git and GitHub for contributions of any kind. Please read this guide thoroughly if you are not familiar with Git. If you have experience, skip to the sections relevant to you.

## How to Set Up the Millennium Dawn Dev Version

Before we begin with Git instructions, you need to properly configure your accounts with GitHub.

1. Log into [GitHub.com](https://github.com) and create an account.
2. Log into the email you used and enter the verification code you received.
3. Choose the option "Just me", then choose the free account.
4. Give your GitHub account name to **TheBrokenDroid** or **XCezor** if you are a dev (AngriestBird if they are unavailable). **Playtesters can skip this step.**
5. Download the [GitHub Desktop](https://desktop.github.com/download/) application.

### Cloning the Repository

Once you have been added (playtesters do not need to wait for this step):

1. Go to [https://github.com/MillenniumDawn/Millennium-Dawn](https://github.com/MillenniumDawn/Millennium-Dawn).
2. Click the dropdown called **Code** and copy the **HTTPS** link. Do not use the SSH or GitHub CLI options.
3. Open the GitHub Desktop application and click **Clone a repository from the Internet**.
4. Fill in the URL using the HTTPS link you copied.
5. Change your local path to your mod directory:
   - **Windows:** `C:\Users\YOUR_USERNAME\Documents\Paradox Interactive\Hearts of Iron IV\mod`
   - **Linux:** `~/.local/share/Paradox Interactive/Hearts of Iron IV/mod`
   - **macOS:** `~/Documents/Paradox Interactive/Hearts of Iron IV/mod`
6. Click the blue **Clone** button.

> If you get an error saying "Authentication failed", follow the [Authentication Failed guide](/dev-resources/authentication-failed-cloning-repo).

> The `Millennium_Dawn` file might appear as a strange file type. Change it to open in Notepad or Notepad++.

Wait until cloning is finished. If downloading at less than 200 KB/s, it may fail.

### Enabling the Mod

1. Open your file explorer and navigate to `Documents/Paradox Interactive/Hearts of Iron IV/mod/Millennium_Dawn`.
2. Find the file called `Millennium_Dawn.mod`, copy it, and go back to the `mod` folder.
3. Paste it so you now have the `.mod` file in both the `Millennium_Dawn` folder and the `mod` folder.
4. Launch HOI4 and in the Paradox Launcher, click **Playsets**, then **Add more mods**, and enable Millennium Dawn Dev.

If your game works, you are done with setup.

### Note for Playtesters

You will need to change your branch in GitHub Desktop to the specific branch when you begin testing, as each piece of content is hosted on a different branch.

Click the **Current branch** button and search for the branch specified in the tester task.

**Playtester instructions end here.** Developers continue below.

---

## Developer Environment Setup

After cloning, run the setup script to install pre-commit hooks and tool dependencies. This is a one-time step:

```bash
python3 tools/setup.py
```

You can verify your environment at any time with:

```bash
python3 tools/setup.py --check
```

If you are also working on the docs site, add the `--docs` flag. See [CONTRIBUTING.md](https://github.com/MillenniumDawn/Millennium-Dawn/blob/main/CONTRIBUTING.md) for full details.

---

## What is Git?

Git is a version control system. We use GitHub as our Git hosting platform.

In Git there are **branches**. The way we use them, they act as different versions/builds of the mod. Branches are set up based on the project you are assigned to. For example, Iranian content would be in a branch named `iranian-content` or `development`.

When making changes on your branch, you mod as normal - editing text files, images, or whatever in your text editor. When you are done for the day or feel you have reached a point worth sharing, you use the Git application.

You will need to make a **commit** and then **push** your changes to the server so everyone else can download them.

### Key Concepts

**Commit:** Think of commits like entries in a journal. You make changes to the mod and then create a new entry noting what you did. Commits let everyone else know what you changed and act as save points. We can roll back thousands of commits and view every single change made to a file. This allows for easy troubleshooting, statistics, and depth. An example commit message: _"Fixed all the bugs in the Argentina Focus tree"_.

**Syncing (Push & Pull):**

- **Pushing** uploads your commits to the server so others can see them. Until you push, commits are only stored on your PC.
- **Pulling** downloads any changes made to that branch that you do not have on your PC.

**Merging:** Merging combines changes from two branches. Instead of sending files back and forth, a merge combines both sets of changes into one version. This is mostly automated.

> Make sure you are always using your own branch. In the Git app, there is a section to select your current branch. No one wants to sync and find their branch broken because someone committed a WIP or broken file to the wrong branch.

> You can run and modify anyone's branch. If someone is working on GFX and you want to test it, switch to their branch, pull, and launch the game. Git handles the file changes seamlessly in the background.

### Shared Branches

In addition to individual feature branches, the team maintains several communal branches:

- **master / main** — The current most up-to-date branch prior to release. Content is merged here only through approved pull requests.
- **gfx-input** — All graphics are committed here, regardless of what content they support. See the [Art Standards](/dev-resources/art-standards/) for details.
- **bug-fixes** — Shared branch for general bug fixes. Most bug fixes should be done here unless otherwise noted.
- **map-work** — Shared branch for map-related changes.

Work on your own feature branch unless you are contributing to one of these specific workflows. Do not commit to shared branches without coordination.

---

## Making a Commit & Pushing

Now that you have GitHub set up, how do you share your work?

1. Mod the files on your computer as if Git was not there.
2. When finished, open the GitKraken application.
3. Click into the **//WIP** commit in the commit graph.
4. Click **Stage All Changes**.
5. Once all files are staged, type the title of your commit in the **Summary** field. You can provide a description, but it is not required.
6. Click **Commit Changes**.
7. Click **Push to Remote**.

## Pulling the Local Branch

Once you have pushed your commit, other team members can pull your changes and update their local copy.

1. Select the desired branch.
2. Click the **Pull** option from the top bar.

GitKraken automatically fetches in the background, ensuring you are notified of remote branches not present locally.

## Updating from Master

You need to constantly update your branch with changes from the master branch. This ensures your branch has the most recent changes and prevents you from editing old files, which causes merge conflicts.

To update your branch:

1. Switch to **master** and pull to make sure you have all the latest commits.
2. Switch back to your branch.
3. Right-click your branch and select the merge option (e.g., "Merge master into your-branch-name").

---

## Merge Conflicts

A merge conflict occurs when Git cannot automatically merge two files because they both changed in the same place. Git leaves it to the user to decide which version is correct.

### Example

Two people edit an event file at the same time. Both start with Version 1, but each makes different changes. If Version 2 gets merged into master and you (using Version 3) try to update from master, you will get a merge conflict because Git could not automatically reconcile the overlapping changes.

### How to Identify a Merge Conflict

Orange warning signs in the Git app indicate a merge conflict.

### How to Resolve a Merge Conflict

When you open the conflicted file, you will see something like this:

```
<<<<<<< HEAD:events/MD4_Init.txt
(your branch's code)
=======
(master's code)
>>>>>>> master:events/MD_Init.txt
```

Everything between `<<<<<<< HEAD` and `=======` is code from your current branch. Everything between `=======` and `>>>>>>> master` is code from the branch you are merging in.

To resolve:

1. Compare the two blocks of code.
2. Decide which changes to keep (sometimes it is a mix of both).
3. Delete the conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`).
4. Check the entire file carefully - there can be several merge conflicts in one file.

Once all conflicts are resolved, the Git app should allow you to commit and push.

---

## Pull Requests

How do you get your code into the master branch? You should only make a pull request when you have completed something noteworthy that is not crashing or causing issues.

1. Go to the repository on GitHub and select **New Pull Request**.
2. Set the **source branch** to your branch.
3. Ensure the **target branch** is `master`.
4. Select **Compare branches and continue**.
5. Fill out the title, description, assignee (you), milestone, and labels.
6. Click **Submit Pull Request**.

### CI Validation

For your code to be merged, two things are required:

1. **It must pass CI validation**, which scans your code for errors. If it passes, you will see a green checkmark. If you get a red X, click through to see the error details, fix the issue, and push a new commit. A new test will run automatically.
2. **A team leader must review and approve** your pull request before it is merged.

> Update from master as often as possible, or you will cause yourself a ton of issues.

---

## FAQ & Notes

- You can view all commits and changes on the repository's commit history page.
- Changes can always be reverted down to a single file if someone modifies the wrong branch. It is not the end of the world, but keeping things tidy saves everyone time.
- **The mod runs as vanilla?** In the `Millennium_Dawn` folder there is a `Millennium_Dawn.mod` file. Copy it and paste it in `Hearts of Iron IV/mod/`. You should now be able to enable the mod in the launcher. If you continue to have issues, you may use the [Irony Mod Manager](https://bcssov.github.io/IronyModManager/) as an alternative launcher.
- You can also move the `Millennium_Dawn` folder to another drive and edit the file path in the `.mod` file to match the new location. Make sure the path does not contain Cyrillic characters.

---

## Visual Studio Code Workspace Instructions

For anyone interested in using Visual Studio Code as an IDE:

### How to Use the Workspace

1. Open VSCode.
2. Go to **File** > **Open Workspace**.
3. Navigate to the mod folder, then `.vscode`, then `hoi4_millennium_dawn.code-workspace`.
4. Confirm the popup to install recommended extensions.

### What is Configured?

1. Two extensions for Paradox syntax with syntax highlighting, snippets, and automatic problem scanning.
2. An extension that highlights and automatically deletes trailing spaces on save. Trailing spaces bloat git diffs and introduce unnecessary merge conflicts.
3. Extensions for Markdown, line sorting (F9), CODEOWNERS, and EditorConfig for cross-IDE configuration.
4. Workspace folders configured for easier access and better hierarchy in search results.

### Why Use a Workspace Instead of Personal Configuration?

If you or someone else finds an extension or configuration that is useful for everyone, it can be committed to the workspace file and then everyone gets it automatically. Opinionated personal settings (e.g., font size, color theme) should stay in your own user configuration rather than the shared workspace.

---

## GitHub Desktop to GitKraken Migration

1. Download [GitKraken Desktop](https://www.gitkraken.com/) (free) and install it.
2. Click **Let's Open a repository!**
3. Confirm the commit information and click **Use These for Git Commits**.
4. Click **Open Repo** and navigate to your Millennium Dawn install via the **Browse** option.
5. Select **Millennium Dawn**.
6. Click **Pull** to ensure you are up to date.
7. Go to **File** > **Preferences** and update the following:
   - Reduce **Initial commits in graph** to `500`.
   - Set **Auto-Fetch Interval** to `10`.
   - Set **External Editor** to Visual Studio Code (if not already set).
8. Exit preferences and click **Local** in the branches menu.
9. Shift-click all local branches (except the one you are currently on) and right-click to delete them.
