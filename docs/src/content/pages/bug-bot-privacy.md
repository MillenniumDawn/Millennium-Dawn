---
title: Bug Bot Privacy Policy
description: What the Millennium Dawn Bug Bot collects, how that data is used and shared, how long it is kept, and how to have it deleted.
permalink: /bug-bot-privacy/
last_updated: 2026-11-09
---

This policy covers the [Millennium Dawn Bug Bot](/bug-bot/), the Discord bot used in the Millennium Dawn community. The bot turns bug reports or suggestions posted in our Discord forum into issues on our public GitHub tracker. This explains what it collects, how that data is used and shared, how long it is kept, and how to have it deleted.

The bot is operated by the Millennium Dawn team, a volunteer, non-profit mod project. In this policy, "we" means that team.

For what you agree to when using the bot, see the [Bug Bot Terms of Service](/bug-bot-terms/). This page covers the data side only.

## What the bot collects

When you post in a tracked forum channel, the bot reads and processes:

- The text and attachments of your report and your follow-up replies in the thread.
- Your Discord user ID (the numeric ID, not your username).
- Your mod version and checksum, when you provide them for a report.
- Your GitHub username, only if you choose to link it with `/register`.
- For registered users, one Discord display name: your server nickname, otherwise your global name, otherwise your username.
- For attachments, the URLs, filenames, media types, and sizes needed to recover an interrupted upload.

The bot needs the Discord Message Content intent to read report text. It does not read messages outside the tracked forum channels, and it does not collect presence, your member list, or anything unrelated to filing bug reports or providing suggestions for the mod. Members who are not registered are not added to the display-name cache.

## How it is used and shared

- **Public GitHub issues.** Your report text and attachments are published as an issue on our public GitHub repository so maintainers can track and fix the bug. Issues are attributed to "discord-sync". Your Discord username is not part of the issue, but the issue links back to the Discord thread so maintainers can follow up, and your username is visible there to anyone in the server. Attachments are republished as part of the issue, so do not include personal information in screenshots or files you attach.
- **AI triage.** Report text may be sent to an AI model to suggest a title, severity, and likely cause. It runs either self-hosted on our own infrastructure, or on Ollama's cloud, which processes the text transiently, does not retain it beyond fulfilling the request, and does not use it to train models.
- **GitHub account linking.** If you run `/register`, the bot stores the link between your Discord account and your GitHub username so commands like `/whoami` can show it. The link is kept until you run `/forget`. For registered users, the bot also caches one Discord display name so maintainers can find you in `/assign` autocomplete. It refreshes that name daily.
- **Internal bookkeeping.** The bot keeps a local database that maps Discord threads to GitHub issues and records operational logs. It stores accepted GitHub webhook payloads locally so it can recover from a crash, and temporarily stores attachment metadata so it can recover an interrupted upload.

The bot does not sell your data, share it with advertisers or data brokers, or use it to build a profile of you. The only third parties that receive your data are GitHub (to host the issue) and Ollama (when cloud triage is used), both only as needed to run the tracker. Data shared with GitHub is subject to [GitHub's privacy statement](https://docs.github.com/en/site-policy/privacy-policies/github-privacy-statement); cloud triage is subject to [Ollama's privacy policy](https://ollama.com/privacy); your use of Discord is covered by [Discord's privacy policy](https://discord.com/privacy).

## Legal basis (GDPR)

If you are in the EU or UK, we process your data on two bases:

- **Legitimate interest** in running the bug tracker. Filing your report as a GitHub issue, keeping your Discord ID for follow-ups, and triaging the report all serve that interest, and you post in a tracked channel voluntarily.
- **Consent** for anything optional. Linking your GitHub username with `/register` is opt-in: you consent by running the command and can withdraw it any time with `/forget`.

## How long it is kept

Retention cleanup runs on a local retention window, which defaults to 30 days.

- **GitHub issues** stay on GitHub indefinitely. They are the record of the bug or the suggestion the user reported.
- **Operational and audit logs** (AI output, duplicate-check audits) are deleted after one retention window.
- **Webhook payloads.** Unprocessed payloads are erased after one window, and expired work cannot be replayed. A failed or interrupted delivery may stay available for manual replay until a window has passed since its last status change; a manual replay restarts that period. After a payload is erased, a content-free record (delivery ID, event type, and issue number) stays for one more window to prevent duplicate processing.
- **Attachment-recovery data.** Stalled recovery payloads are erased after one window. A content-free record that the payload was erased or expired stays for one more window. Files already published to GitHub follow the tracker's own attachment retention.
- **Cached display names** are cleared when you are confirmed to have left the server, or after a full window with no successful refresh.
- **Thread-to-issue mappings** are kept while the issue is active.
- **`/register` links** are kept until you run `/forget`.
- **Backups** have their own retention. Retention cleanup and `/forget` do not rewrite historical backups.

## Your choices

- Run **`/forget`** in Discord to delete the data the bot holds about you. This removes your `/register` entry and cached display name, erases pending webhook and attachment-recovery payloads for your reports, and de-identifies your Discord ID from stored reports and logs. It cannot retract files already published to GitHub or recall requests already sent to another service. Published GitHub issues already carry no username; the report text stays as the tracked bug. If you need an issue itself removed, ask a maintainer.
- Email us at <millenniumdawnmod@gmail.com> to ask what data the bot holds about you, to have it deleted, or to object to how it is used. Use this route if you can no longer run Discord commands (for example, you left the server); we will act on the request the same way.

## Children's privacy

Discord requires users to be at least 13 (older in some countries). The bot is not intended for children under 13, and we do not knowingly collect their data. If we learn that we have, we will delete it. Contact us at <millenniumdawnmod@gmail.com> if you believe a child has used the bot.

## Security

Local data is stored in the United States, on access-restricted private infrastructure we run for the mod. If you are in the EU or UK, this means your data is processed in the United States. We use reasonable technical and organizational measures to protect it and will notify affected users of any unauthorized access as required by law.

## Changes

We may update this policy. The current version always lives on this page.

## Contact Us

If you have any questions or concerns about this Privacy Policy, please contact us at <millenniumdawnmod@gmail.com>.
