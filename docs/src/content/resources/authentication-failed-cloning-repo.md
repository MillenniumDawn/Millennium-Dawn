---
title: Authentication Failed Cloning Repo
description: How to resolve 'Authentication failed' errors when cloning a repository from GitLab
---

If you have the error screen "Authentication Failed" like below:

[Image unavailable: authentication error screenshot]

The way to fix it is pretty simple, first you need to be on gitlab.com (if you're here, you've done this already)

Then you need to go to your profile, up at the top right of the page, like so:

[Image unavailable: profile menu screenshot]

Then to "Edit profile", which is right here:

[Image unavailable: edit profile screenshot]

This will take you to your profile settings page, on the left of the screen you will see this menu, go to "Access Tokens" as shown:

[Image unavailable: access tokens screenshot]

This is where you will need to create a "Personal Access Token" or PAT for short.

1. This is where you name your PAT, this can be anything you like it to be, I've called it "Guide" for this example.
2. This is where you can set an expiration date on your PAT, for security reasons, leaving it blank will have this PAT be usable indefinitely, so it's up to you what you want to pick.
3. This is the only one of these you need to tick, it's so your PAT works for everything a password normally would, think of it as changing from "read-only" to "editing privileges", it is important to not forget this step.

[Image unavailable: PAT settings screenshot]

Then you need to click "Create personal access token", like so:

[Image unavailable: create token screenshot]

This will create a string of characters above the settings you have chosen, it is **VITAL** you do not share this with anyone, as this could result in your account being compromised, this PAT can be used instead of a password. Click the clipboard icon to copy it as shown:

[Image unavailable: copy token screenshot]

Sign in as normal but instead of using your password in the password field, paste your PAT code in there, your username is just your regular username, hopefully this method will get you on the go and ready to clone as normal!
