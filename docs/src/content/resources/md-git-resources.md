---
title: "Git & GitHub Desktop"
description: "Clone Millennium Dawn with GitHub Desktop, commit and push changes, and open a pull request. Environment setup lives in Developer Setup; the full Git process is in Git Workflow."
---

This guide is the GitHub Desktop quick start for Millennium Dawn. Use it alongside the
two maintained references below so each procedure has a single home:

- [Developer Setup](/dev-resources/developer-setup/): install the tools, connect the mod to the launcher, and run pre-commit hooks.
- [Git Workflow](/dev-resources/git-workflow/): branches, commits, merge conflicts, and pull requests in detail.

New to Git? Git tracks every change to the codebase. Branches are separate workspaces; you
make changes on your branch, then merge them into `main` through a pull request.

## Install GitHub Desktop

Download and install [GitHub Desktop](https://desktop.github.com/download/). Sign in with
the GitHub account that has access to the repository. GitHub Desktop is the recommended Git
GUI for this project: it is free, simple, and connects directly to GitHub.

## Clone the Mod

**Outside contributors**: fork the repository first (see [Git Workflow: Outside Contributors (Fork)](/dev-resources/git-workflow/#outside-contributors-fork)), then clone your fork instead of the main repo.

1. Open [github.com/MillenniumDawn/Millennium-Dawn](https://github.com/MillenniumDawn/Millennium-Dawn).
2. Click **Code** and copy the **HTTPS** URL. Do not use the SSH or GitHub CLI options; they are not set up for this workflow.

   ![Millennium Dawn](/assets/images/git-resources/image-1.png)

3. In GitHub Desktop, choose **Clone a repository from the Internet** and paste the URL.

   ![Copy the HTTPS clone URL](/assets/images/git-resources/image-2.png)

4. Set the local path to your HOI4 mod folder (the drive where Paradox stores files):

   `C:\Users\<name>\Documents\Paradox Interactive\Hearts of Iron IV\mod`

   ![GitHub Desktop clone settings](/assets/images/git-resources/image-3.png)

   ![GitHub Desktop cloning the repository](/assets/images/git-resources/image-4.png)

   If cloning fails with an "Authentication failed" message, follow the
   **[authentication failed cloning repo](/dev-resources/authentication-failed-cloning-repo/)**
   guide. If the cloned `Millennium_Dawn` file shows as a video or unknown type, open it in Notepad or Notepad++.

5. Wait for the clone to finish. A slow connection (under 200 KB/s) can cause it to fail; retry, or use a shallow clone with `git clone --depth 1`.

For connecting the cloned mod to the launcher and enabling the Developer Version, see
[Developer Setup: Setting Up the Mod for Testing](/dev-resources/developer-setup/#setting-up-the-mod-for-testing).

## Make a Commit and Push

1. Edit the mod files in your text editor as usual.
2. In GitHub Desktop, your changed files appear in the left panel.
3. Select the files for this commit, or stage all changes.
4. Write a short, descriptive summary (for example "Add Serbian election focus tree").
5. Click **Commit to `<your-branch>`**.
6. Click **Push** to upload your commit to GitHub.

Commit messages should be specific and in past tense: "Fixed Serbian election focus
prerequisite", not "Fixed stuff". Pre-commit hooks run automatically and flag issues
before you push. See [Git Workflow: Making Changes](/dev-resources/git-workflow/#making-changes)
for message conventions.

## Pull and Stay Up to Date

- Click **Pull** in GitHub Desktop to download changes others made to your branch.
- Keep your branch synced with `main` to avoid large merge conflicts. Switch to `main`, pull, switch back to your branch, then merge `main` in.

See [Git Workflow: Staying Up to Date with Main](/dev-resources/git-workflow/#staying-up-to-date-with-main).

## Merge Conflicts

When Git cannot combine two edits to the same lines, it marks a conflict. GitHub Desktop
shows a **Resolve conflicts** button, and the conflicted file shows markers:

```
<<<<<<< HEAD
your changes on the current branch
=======
changes from the branch being merged in
>>>>>>> main
```

Delete the markers and keep the correct code, then commit. A file can have several
conflicts, so search for `<<<<<<<` to find them all. See
[Git Workflow: Merge Conflicts](/dev-resources/git-workflow/#merge-conflicts).

## Open a Pull Request

1. Push your branch to GitHub.
2. On the repository page, click **Compare & pull request**.
3. Set the base branch to `main` and the compare branch to your feature branch.
4. Add a title and a description of what changed and why.
5. Submit. CI validates your PR automatically; a team leader reviews and merges.

See [Git Workflow: Pull Requests](/dev-resources/git-workflow/#pull-requests) and the
[Contributing Guide](/dev-resources/contributing/).
