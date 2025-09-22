---
layout: default
title: "Authentication Failed Cloning Repo"
description: "How to resolve 'Authentication failed' errors when cloning a repository from GitLab"
---

If you have the error screen "Authentication failed" like below:

![authentication_error](/uploads/8d096bf6646b04ea1c7643f9ea54cf6a/authentication_error.png)

The way to fix it is pretty simple, first you need to be on gitlab.com (if you're here, you've done this already)

Then you need to go to your profile, up at the top right of the page, like so:

![where_profile](/uploads/ae3343a8144effec238d456e7f78bf89/where_profile.png)

Then to "Edit profile", which is right here:

![where_edit_profile](/uploads/361fdf1ba17dd43ee9c78410c2ac0ab2/where_edit_profile.png)

This will take you to your profile settings page, on the left of the screen you will see this menu, go to "Access Tokens" as shown:

![where_access_tokens](/uploads/ec51af57fe1e9d43d075a99eae119efe/where_access_tokens.png)

This is where you will need to create a "Personal Access Token" or PAT for short.
1. This is where you name your PAT, this can be anything you like it to be, I've called it "Guide" for this example.
2. This is where you can set an expiration date on your PAT, for security reasons, leaving it blank will have this PAT be usable indefinitely, so it's up to you what you want to pick.
3. This is the only one of these you need to tick, it's so your PAT works for everything a password normally would, think of it as changing from "read-only" to "editing privileges", it is important to not forget this step.

![PAT_settings](/uploads/ec635a2cf04ea13c49efd4465cee5336/PAT_settings.png)

Then you need to click "Create personal access token", like so:

![what_push_make_token](/uploads/bcd7bb6ac041484545cfcc0acae220c9/what_push_make_token.png)

This will create a string of characters above the settings you have chosen, it is **VITAL** you do not share this with anyone, as this could result in your account being compromised, this PAT can be used instead of a password. Click the clipboard icon to copy it as shown:

![how_copy_token](/uploads/7d07c1edf70a1012f3a352ac8aafeef3/how_copy_token.png)

Sign in as normal but instead of using your password in the password field, paste your PAT code in there, your username is just your regular username, hopefully this method will get you on the go and ready to clone as normal!
