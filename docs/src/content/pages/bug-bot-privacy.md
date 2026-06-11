---
title: Bug Bot Privacy Policy
description: What the Millennium Dawn Bug Bot collects, how that data is used and shared, how long it is kept, and how to have it deleted.
permalink: /bug-bot-privacy/
last_updated: 2026-06-11
---

This policy covers the [Millennium Dawn Bug Bot](/bug-bot/), the Discord bot used in the Millennium Dawn community. The bot turns bug reports posted in our Discord forum into issues on our public GitHub tracker. This explains what it collects, how that data is used and shared, how long it is kept, and how to have it deleted.

Last updated: 2026-06-11.

## What the bot collects

When you post in a tracked forum channel, the bot reads and processes:

- The text and attachments of your report and your follow-up replies in the thread.
- Your Discord user id (the numeric id, not your username).
- Your mod version and checksum, when you provide them for a report.
- Your GitHub username, only if you choose to link it with `/register`.

The bot needs the Discord Message Content intent to read report text. It does not read messages outside the tracked forum channels, and it does not collect presence, your member list, or anything unrelated to filing bug reports.

## How it is used and shared

- **Public GitHub issues.** Your report text and attachments are published as an issue on our public GitHub repository so maintainers can track and fix the bug. Issues are attributed to "discord-sync". Your Discord username is not published. The issue links back to the Discord thread so maintainers can follow up.
- **AI triage.** Report text may be sent to a self-hosted AI model to suggest a title, severity, and likely cause. This runs on our own infrastructure. Message content is never used to train AI models.
- **Internal bookkeeping.** The bot keeps a local database that maps Discord threads to GitHub issues and records operational logs.

The bot does not sell your data, share it with advertisers or data brokers, or use it to build a profile of you. Data is only shared with GitHub (to host the issue) and our self-hosted AI model (to triage it), both as needed to run the tracker.

## How long it is kept

- **GitHub issues** stay on GitHub indefinitely. They are the record of the bug.
- **Operational and audit logs** (webhook deliveries, AI output, duplicate-check audits) are automatically deleted after 30 days.
- **Thread-to-issue mappings** are kept while the issue is active.

## Your choices

- Run **`/forget`** in Discord to delete the data the bot holds about you. This removes your `/register` entry and de-identifies your Discord id from stored reports and logs. Published GitHub issues already carry no username; the report text stays as the tracked bug. If you need an issue itself removed, ask a maintainer.

## Security

Local data is stored on access-restricted private infrastructure. We use commercially reasonable measures to protect it and will notify affected users of any unauthorized access as required by law.

## Changes

We may update this policy. The current version always lives on this page.
