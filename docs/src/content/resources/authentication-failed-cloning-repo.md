---
title: Authentication Failed Cloning Repo
description: How to resolve 'Authentication failed' errors when cloning the repository from GitHub
---

If you get an "Authentication Failed" error when trying to clone the Millennium Dawn repository, follow the steps below.

## Option 1: Sign In via GitHub Desktop

The simplest fix is to sign into GitHub through the GitHub Desktop application:

1. Open GitHub Desktop.
2. Go to **File** > **Options** (Windows) or **GitHub Desktop** > **Settings** (macOS).
3. Click the **Accounts** tab.
4. Click **Sign In** next to GitHub.com and follow the browser-based authentication flow.
5. Once signed in, try cloning the repository again.

## Option 2: Create a Personal Access Token (PAT)

If GitHub Desktop sign-in does not resolve the issue, you can authenticate using a Personal Access Token:

1. Go to [github.com](https://github.com) and sign in.
2. Click your profile picture in the top right, then go to **Settings**.
3. Scroll down in the left sidebar and click **Developer settings**.
4. Click **Personal access tokens** > **Tokens (classic)**.
5. Click **Generate new token** > **Generate new token (classic)**.
6. Give the token a descriptive name (e.g., "Millennium Dawn Dev").
7. Set an expiration date (or select "No expiration" if you prefer, though an expiry is recommended for security).
8. Under **Select scopes**, check the **repo** checkbox (this grants full access to repositories).
9. Click **Generate token**.
10. **Copy the token immediately** — you will not be able to see it again after leaving the page.

> **Do not share your token with anyone.** A PAT functions as a password and could compromise your account.

When prompted for a password during cloning, paste your PAT instead of your GitHub password.

## Option 3: Use SSH Authentication

As an alternative to HTTPS, you can set up SSH keys:

1. Follow GitHub's guide to [generate a new SSH key](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent).
2. [Add the SSH key to your GitHub account](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account).
3. When cloning, use the **SSH** URL instead of HTTPS from the repository's **Code** dropdown.

## Still Having Issues?

If none of the above works, ask for help in the Discord development channel.
