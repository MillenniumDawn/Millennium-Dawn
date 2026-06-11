---
title: Bug Bot
description: What the Millennium Dawn Bug Bot is, what it does, and how to use it to report bugs.
permalink: /bug-bot/
last_updated: 2026-06-11
---

The Millennium Dawn Bug Bot connects our Discord bug-report forum to the [GitHub issue tracker](https://github.com/MillenniumDawn/Millennium-Dawn/issues). When you post a report on Discord, the bot files it as a GitHub issue so the team can track and fix it, then keeps the two in sync.

## What it does

- **Turns forum posts into GitHub issues.** Your report becomes a tracked issue with the right labels and type.
- **Checks reports are complete.** Before filing, it asks for your game and mod version and your mod checksum. Incomplete reports are held until you add the missing details.
- **Triages with AI.** A self-hosted model suggests a title, severity, and likely cause to help maintainers prioritize.
- **Syncs the conversation.** Your follow-up replies are mirrored to the GitHub issue, and status changes flow back to the thread.
- **Flags duplicates** so the same bug is not filed twice.

## How to report a bug

1. Post in the bug-report forum on [Discord](https://discord.gg/millenniumdawn).
2. Include your **game + mod version** (e.g. HOI4 1.16.4, Millennium Dawn 1.13) and your **mod checksum** (shown on the launcher / main menu).
3. Describe the bug and attach screenshots or save files if you have them.

The bot replies in your thread with a link to the GitHub issue once it is filed.

## Useful commands

- `/register` — link your GitHub username to your Discord account.
- `/forget` — delete the data the bot holds about you.
- `/privacy` — a short summary of what is collected and how it is used.
- `/whoami` — show your linked GitHub username.

## Privacy

The bot reads your report text and republishes it to a public GitHub issue. Your Discord username is not published. For the full details on what is collected, how it is shared, how long it is kept, and how to have it deleted, see the **[Bug Bot Privacy Policy](/bug-bot-privacy/)**.
