---
title: Bug Bot Terms of Service
description: The terms under which the Millennium Dawn Bug Bot is provided to the community. Covers acceptable use, what the team promises, and the limits of liability.
permalink: /bug-bot-terms/
last_updated: 2026-06-16
---

These terms cover the [Millennium Dawn Bug Bot](/bug-bot/), the Discord bot used in the Millennium Dawn community to turn bug reports and suggestions posted in our Discord forum into issues on our public GitHub tracker. The bot is operated by the Millennium Dawn team, a volunteer, non-profit mod project. In these terms, "we" means that team and "you" means anyone who uses the bot or posts in a tracked forum channel.

These terms are a usage agreement, not a contract for paid services. The bot is free, the mod is free, and we do not enter into a commercial relationship with you by your use of the bot. If these terms are not acceptable to you, do not post in tracked channels or use the bot's commands.

For what the bot collects, how that data is used, and how to have it deleted, see the **[Bug Bot Privacy Policy](/bug-bot-privacy/)**. This page covers everything else.

## What the bot does

The bot reads posts and replies in tracked forum channels on our Discord server, processes the text, and publishes it as an issue on our public [GitHub repository](https://github.com/MillenniumDawn/Millennium-Dawn/issues). A self-hosted AI model on our infrastructure may be used to suggest a title, severity, and likely cause for the report before the issue is filed. The bot also accepts a small set of commands: `/register` to link your GitHub username, `/whoami` to show that link, `/privacy` for a short data summary, and `/forget` to delete the data the bot holds about you.

Beyond the report you post, the only personal identifier the bot keeps is your public Discord user ID (the numeric account ID, not your username), kept solely so the team can ping you on the issue thread for follow-ups. Linking a GitHub username with `/register` is opt-in, added by the team for ease of tracking reports, not to profile you. The bot does not collect your email, presence, member list, or anything else unrelated to filing a report. For the full list of what is collected and how long it is kept, see the [privacy policy](/bug-bot-privacy/).

The full description of the bot's behavior is in the [Bug Bot overview](/bug-bot/). The overview and the [privacy policy](/bug-bot-privacy/) describe what the bot actually does; if anything on this page conflicts with them, those pages control.

## Acceptable use

By using the bot or posting in a tracked channel you agree to:

- **Post only content you have the right to share.** Do not post copyrighted material, private information about other people, or content posted under someone else's name. Do not include personal information in screenshots, save files, or other attachments you upload.
- **Keep reports on-topic.** Tracked channels are for bug reports and suggestions for the mod. Off-topic posts, spam, advertising, and unrelated discussion are not welcome and may be removed.
- **Do not attempt to abuse the bot.** This includes but is not limited to: filing the same report repeatedly to bypass the duplicate check, scripting against the bot's commands, attempting to extract data through rate-limit probing, or any action intended to make the bot unavailable to other users.
- **Do not post content that is unlawful, harassing, hateful, threatening, sexually explicit, or that encourages violence against any person or group.** We may remove such content and disable the bot for the responsible user without notice.
- **Follow the Discord [Terms of Service](https://discord.com/terms) and [Community Guidelines](https://discord.com/guidelines).** Your use of Discord is covered by Discord, not us.

We may refuse, edit, or remove any post, and may disable the bot for any user, at our discretion. We try to act in good faith and to be consistent, but we cannot guarantee a specific outcome for any individual report.

## What we promise

We will operate the bot in line with the [privacy policy](/bug-bot-privacy/) and these terms. We will try to keep the bot available, but we cannot guarantee uninterrupted service. The bot is provided on an as-available basis.

We will:

- Process only the data described in the privacy policy.
- Not sell or share your data with advertisers or data brokers.
- Honor `/forget` and equivalent email requests to delete the data the bot holds about you, subject to the limits below.
- Notify affected users of any unauthorized access to bot-stored data, as required by law.

## What we do not promise

The mod and the bot are community efforts, not commercial products. To the maximum extent permitted by law:

- The bot and any AI-generated triage (title, severity, likely cause) are provided **as is** and **as available**, with no warranty of any kind. We do not warrant that triage is correct, complete, or useful.
- We are not liable for any indirect, incidental, special, consequential, or punitive damage arising from your use of the bot, including but not limited to loss of data, lost time, or emotional distress, even if we have been advised of the possibility of such damage.
- Our total liability to you for any claim relating to the bot is limited to the amount you have paid us in the twelve months before the claim. Because the bot is free, that amount is zero.

Nothing in these terms excludes or limits liability that cannot be excluded or limited under applicable law (for example, liability for death or personal injury caused by negligence, or for fraud).

## The bot and its code

The Bug Bot is a single instance we host and run on our own infrastructure. It is a service we operate for our community, not software we distribute. We own its source code; it is not released, licensed, sold, or shipped to anyone, and using the bot grants you no rights to that code. You cannot add the bot to another server or run your own copy. These terms cover your use of the one instance we run, nothing more.

## Your content and our rights

You retain all rights to the text and attachments you post. By posting in a tracked channel you grant us a non-exclusive, worldwide, royalty-free license to publish that content as a GitHub issue, mirror your follow-up replies back to the issue, and use the content for the operation of the bot. This license ends when the content is deleted from both Discord and GitHub, except that GitHub issues already published may be retained for the historical record of the bug or suggestion.

You confirm that you have the rights needed to grant this license. If you do not, do not post in tracked channels.

## Deleting your data and closing the loop

- Run **`/forget`** in Discord to delete the data the bot holds about you. This removes your `/register` entry and de-identifies your Discord ID from stored reports and logs. Published GitHub issues already carry no Discord username; the report text stays as the tracked bug. If you need an issue itself removed, ask a maintainer.
- If you can no longer use Discord commands (for example, you left the server), email us at <millenniumdawnmod@gmail.com> and we will do the same on request.
- For the full data-handling details, including the 30-day automatic deletion of operational and audit logs, see the [Bug Bot Privacy Policy](/bug-bot-privacy/).

## Changes to these terms

We may update these terms. The current version always lives on this page, with the `last_updated` date at the top. Material changes will be announced in our Discord server before they take effect. Continued use of the bot after a change takes effect constitutes acceptance of the new terms.

## Contact

Questions, concerns, or takedown requests: <millenniumdawnmod@gmail.com>.

For privacy-specific questions, the [Bug Bot Privacy Policy](/bug-bot-privacy/) is the right starting point.

---

These terms are provided for the convenience of the community and do not create any contractual relationship beyond what is permitted by applicable law. The Millennium Dawn team is a volunteer project.
