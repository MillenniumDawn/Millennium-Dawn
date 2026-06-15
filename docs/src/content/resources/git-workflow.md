---
title: Git Workflow
description: Branching, commits, pull requests, and merge conflicts for Millennium Dawn development
---

This guide covers the Git workflow used by the Millennium Dawn team. It replaces the older Google Docs-based Git instructions and reflects the current GitHub-based process.

> **New to Git?** Git is a version control system that tracks every change to the codebase. Branches act as separate workspaces — you make changes on your branch, then merge them into `main` via a pull request.

---

# Core Concepts

| Term                  | What it means                                                                                                |
| --------------------- | ------------------------------------------------------------------------------------------------------------ |
| **Repository (repo)** | The project's codebase on GitHub, including full history of every change                                     |
| **Branch**            | An independent workspace for your changes. Each branch is a snapshot you can modify without affecting others |
| **Commit**            | A saved snapshot of your changes. Think of it as a checkpoint — you can always roll back to any commit       |
| **Push**              | Upload your local commits to GitHub so others can see them                                                   |
| **Pull**              | Download commits from GitHub that you don't have locally                                                     |
| **Merge**             | Combine changes from two branches. Git handles this automatically unless two people edited the same lines    |
| **Pull Request (PR)** | A request to merge your branch into `main`. Requires CI to pass and a team leader to approve                 |
| **Fork**              | Your personal copy of the repository (for outside contributors without write access)                         |

---

# Branching Strategy

- **`main`** is the stable, release-ready branch. Never commit directly to `main`.
- **Feature branches** are created for each piece of work: a focus tree, event chain, bug fix, etc.
- Branches are named descriptively: `ser-focus-tree`, `fix-election-event`, `ai-strategy-updates`.

## Creating a Branch

```bash
# Make sure you're on main and up to date
git checkout main
git pull origin main

# Create and switch to a new branch
git checkout -b my-feature
```

## Switching Branches

```bash
# Switch to an existing branch
git checkout other-branch

# List all branches
git branch -a
```

> **Important**: Always check which branch you're on before committing. The current branch is shown in your Git GUI or at the terminal prompt. Committing to the wrong branch causes problems for other team members.

---

# Making Changes

1. Edit files on your computer — use whatever text editor you prefer.
2. Test your changes in-game when possible.
3. When you're ready to save a checkpoint, create a commit.

## Staging and Committing

### GitHub Desktop

1. Open GitHub Desktop — your changed files appear in the left panel.
2. Select the files you want to include in this commit.
3. Write a short, descriptive summary (e.g., "Add Serbian election focus tree").
4. Click **Commit to my-feature**.

### Command Line

```bash
# See what changed
git status

# Stage specific files
git add common/national_focus/05_SER_focus.txt
git add localisation/english/MD_focus_SER_l_english.yml

# Or stage everything
git add -A

# Commit with a message
git commit -m "Add Serbian election focus tree"
```

### GitKraken

1. Click into the **//WIP** commit in the commit graph.
2. Click **Stage All Changes**.
3. Type your commit summary in the **Summary** field.
4. Click **Commit Changes**.

## Commit Messages

- Write a short summary (5-10 words) describing what changed.
- Use past tense: "Added", "Fixed", "Reworked".
- Be specific: "Fixed Serbian election focus prerequisite", not "Fixed stuff".
- Pre-commit hooks run automatically — fix any issues they flag before pushing.

---

# Pushing and Pulling

## Pushing

After committing, your changes are only stored locally. Push them to GitHub so others can see them:

```bash
git push origin my-feature
```

In GitHub Desktop or GitKraken, click the **Push** button.

## Pulling

Pull downloads any changes others have made to your branch:

```bash
git pull origin my-feature
```

In GitHub Desktop or GitKraken, click the **Pull** button.

> **Pull before you push** if others are working on the same branch. This reduces merge conflicts.

---

# Staying Up to Date with Main

Your branch will fall behind `main` as other PRs merge. Sync regularly to avoid large merge conflicts later:

## Merge (Recommended for Beginners)

```bash
# Fetch latest from remote
git fetch origin

# Switch to main and pull
git checkout main
git pull origin main

# Switch back to your branch and merge main in
git checkout my-feature
git merge main
```

## Rebase (Cleaner History)

```bash
git checkout my-feature
git rebase main
```

> **Rebase vs Merge**: Rebase replays your commits on top of `main`, giving a linear history. Merge creates a merge commit. Both work — use whichever your team prefers. If unsure, use merge.

In GitKraken: right-click your branch → **Rebase on main** (or **Merge main into my-feature**).

---

# Merge Conflicts

A merge conflict happens when Git can't automatically combine two changes to the same file at the same location. You need to manually choose which version to keep.

## How to Identify

- GitKraken shows orange warning signs on conflicted files.
- GitHub Desktop shows a **Resolve conflicts** button.
- The command line shows `CONFLICT` in the merge output.

## How to Read

Open the conflicted file. You'll see markers like this:

```
<<<<<<< HEAD:events/MD_Init.txt
your changes on the current branch
=======
changes from the branch being merged in (e.g., main)
>>>>>>> master:events/MD_Init.txt
```

- Everything between `<<<<<<< HEAD` and `=======` is **your version**.
- Everything between `=======` and `>>>>>>> master` is **the other version**.
- Decide which to keep (or combine both), then delete the markers.

## How to Resolve

1. Open the conflicted file and find all conflict markers.
2. Edit the file to keep the correct code.
3. Delete the `<<<<<<<`, `=======`, and `>>>>>>>` markers.
4. Save the file.
5. In your Git GUI, mark the conflict as resolved and commit.

> **Check carefully** — a file can have multiple conflicts. Search for `<<<<<<<` to find them all.

---

# Pull Requests

When your work is ready for review, open a pull request (PR) to merge your branch into `main`.

## When to Open a PR

- You've completed a meaningful piece of work (a focus tree, event chain, bug fix, etc.).
- Your changes don't crash or break the mod.
- Pre-commit hooks pass without errors.
- You've tested in-game if possible.

## How to Open

1. Push your branch to GitHub.
2. Go to [github.com/MillenniumDawn/Millennium-Dawn](https://github.com/MillenniumDawn/Millennium-Dawn).
3. Click **Compare & pull request** (or go to **Pull requests** → **New pull request**).
4. Set the base branch to `main` and the compare branch to your feature branch.
5. Fill in:
   - **Title**: Short summary of what the PR does.
   - **Description**: What changed and why. Mention if AI was used substantially.
6. Submit the PR.

## What Happens Next

1. **CI validation** runs automatically — checks for style issues, encoding problems, common mistakes.
   - If CI fails, check the logs, fix the issues, commit, and push. CI re-runs automatically.
2. **Team leader review** — a team leader reviews your code and either approves or requests changes.
3. **Merge** — once approved and CI passes, your branch is merged into `main`.

## PR Best Practices

- Keep PRs focused on a single feature or fix.
- Update [Changelog.txt](https://github.com/MillenniumDawn/Millennium-Dawn/blob/main/Changelog.txt) under the current version heading.
- Add yourself to [AUTHORS.md](https://github.com/MillenniumDawn/Millennium-Dawn/blob/main/docs/src/content/misc/authors.md) if this is your first contribution.
- Respond to review feedback promptly.

---

# Worktree Workflow (Advanced)

For developers working on multiple features simultaneously, Git worktrees let you have multiple branches checked out at the same time in separate directories:

```bash
# Create a worktree for a second feature
git worktree add ../Millennium-Dawn-feature2 my-other-branch

# List worktrees
git worktree list

# Remove when done
git worktree remove ../Millennium-Dawn-feature2
```

This avoids the overhead of switching branches and re-compiling assets.

---

# FAQ

**The mod is running as vanilla?**
Copy the `Millennium_Dawn.mod` file from the repo into `Hearts of Iron IV/mod/`. Enable it in the launcher.

**How do I revert a commit?**
Ask a team leader — they can revert changes down to a single file. It's not the end of the world, but saves time if caught early.

**Can I work on someone else's branch?**
Yes. Switch to their branch, sync, and make changes. Be careful not to break their work — coordinate on Discord first.

**What if my download speed is very slow?**
The repo is large. If cloning fails, try a shallow clone: `git clone --depth 1 https://github.com/MillenniumDawn/Millennium-Dawn.git`

**GitHub Desktop vs GitKraken?**
Both work. GitHub Desktop is simpler and free. GitKraken has more features (commit graph, interactive rebase) but the free tier has limitations. Pick whichever you prefer.

---

# Related Resources

- [Developer Setup](/dev-resources/developer-setup/) — Environment setup, tools, pre-commit hooks
- [Contributing Guide](/dev-resources/contributing/) — What we accept, fork workflow, AI policy
- [Code Stylization Guide](/dev-resources/code-stylization-guide/) — Formatting and code structure
- [GitHub Repository](https://github.com/MillenniumDawn/Millennium-Dawn)
