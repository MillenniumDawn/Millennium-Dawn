#!/usr/bin/env python3
"""
Generate a unified validation report from individual validation job outputs.
This script combines the results from multiple validation jobs into a single
markdown report for easy review and optionally posts it as a PR comment.
"""

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime
from pathlib import Path


def read_log_file(file_path):
    """Read a log file and return its contents."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None
    except Exception as e:
        return f"Error reading file: {e}"


def determine_status(content):
    """Determine the status based on log content."""
    if content is None:
        return "⚠️  **Status:** No output file found"

    content_lower = content.lower()

    # Check for failures/errors
    if any(marker in content_lower for marker in ["error", "failed", "✗"]):
        return "❌ **Status:** Failed"

    # Check for warnings
    if any(marker in content_lower for marker in ["warning", "⚠"]):
        return "⚠️  **Status:** Passed with warnings"

    # Assume passed
    return "✅ **Status:** Passed"


def count_issues(content):
    """Count the number of issues in the log content."""
    if content is None:
        return 0

    count = 0
    for line in content.split("\n"):
        if any(
            marker in line for marker in ["ERROR", "FAILED", "✗", "error:", "failed:"]
        ):
            count += 1

    return count


def add_section(title, file_path):
    """Generate a markdown section for a validation result."""
    content = read_log_file(file_path)
    status = determine_status(content)

    section = [
        f"## {title}",
        "",
        status,
        "",
    ]

    if content is not None and content.strip():
        section.extend(
            [
                "<details>",
                "<summary>View Details</summary>",
                "",
                "```",
                content,
                "```",
                "",
                "</details>",
            ]
        )

    section.append("")
    return "\n".join(section)


def generate_report(results_dir, pr_number=None, commit_sha=None):
    """Generate the full validation report."""
    report_lines = [
        "# Validation Report",
        "",
    ]

    # Add metadata if provided
    if pr_number:
        report_lines.append(f"**Pull Request:** #{pr_number}")
    if commit_sha:
        report_lines.append(f"**Commit:** `{commit_sha[:7]}`")

    report_lines.extend(
        [
            f"**Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            "---",
            "",
        ]
    )

    # Define validation sections
    validations = [
        (
            "Flags and Event Targets Validation",
            "validation-variables-results/validation-variables.log",
        ),
        (
            "Scripted Localisation Validation",
            "validation-scripted-localisation-results/validation-scripted-localisation.log",
        ),
        (
            "Cosmetic Tag Validation",
            "validation-cosmetic-tags-results/validation-cosmetic-tags.log",
        ),
        (
            "Decision Validation",
            "validation-decisions-results/validation-decisions.log",
        ),
        (
            "Localisation Validation",
            "validation-localisation-results/validation-localisation.log",
        ),
        (
            "Event Validation",
            "validation-events-results/validation-events.log",
        ),
        (
            "Unused Scripted Effects & Triggers Validation",
            "validation-unused-scripted-results/validation-unused-scripted.log",
        ),
    ]

    # Add each validation section
    total_issues = 0
    for title, log_file in validations:
        file_path = Path(results_dir) / log_file
        report_lines.append(add_section(title, file_path))

        # Count issues
        content = read_log_file(file_path)
        total_issues += count_issues(content)

    # Add summary
    report_lines.extend(
        [
            "---",
            "",
            "## Summary",
            "",
        ]
    )

    if total_issues == 0:
        report_lines.append("✅ All validations passed successfully!")
    else:
        report_lines.append(f"❌ Found {total_issues} issue(s) across validation jobs")

    report_lines.append("")

    return "\n".join(report_lines)


def post_pr_comment(repo_owner, repo_name, pr_number, report_content, github_token):
    """Post or update a PR comment with the validation report."""
    api_base = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    try:
        # Get existing comments
        comments_url = f"{api_base}/issues/{pr_number}/comments"
        req = urllib.request.Request(comments_url, headers=headers)

        with urllib.request.urlopen(req) as response:
            comments = json.loads(response.read().decode())

        # Find existing validation report comment
        existing_comment = None
        for comment in comments:
            if comment.get("user", {}).get(
                "type"
            ) == "Bot" and "Validation Report" in comment.get("body", ""):
                existing_comment = comment
                break

        # Update or create comment
        if existing_comment:
            # Update existing comment
            comment_id = existing_comment["id"]
            update_url = f"{api_base}/issues/comments/{comment_id}"
            data = json.dumps({"body": report_content}).encode("utf-8")

            req = urllib.request.Request(
                update_url, data=data, headers=headers, method="PATCH"
            )

            with urllib.request.urlopen(req) as response:
                print(
                    f"✅ Updated existing PR comment (ID: {comment_id})",
                    file=sys.stderr,
                )
        else:
            # Create new comment
            data = json.dumps({"body": report_content}).encode("utf-8")

            req = urllib.request.Request(comments_url, data=data, headers=headers)

            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode())
                print(
                    f"✅ Created new PR comment (ID: {result['id']})", file=sys.stderr
                )

        return True

    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else "No error details"
        print(f"❌ Failed to post PR comment: {e.code} - {error_body}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ Failed to post PR comment: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate unified validation report from validation job outputs"
    )
    parser.add_argument(
        "--results-dir",
        required=True,
        help="Directory containing validation results",
    )
    parser.add_argument(
        "--output",
        default="report.md",
        help="Output file for the report (default: report.md)",
    )
    parser.add_argument(
        "--pr-number",
        help="Pull request number",
    )
    parser.add_argument(
        "--commit-sha",
        help="Commit SHA",
    )
    parser.add_argument(
        "--print",
        action="store_true",
        help="Print report to stdout in addition to writing to file",
    )
    parser.add_argument(
        "--github-token",
        help="GitHub token for posting PR comments (required if --post-comment is used)",
    )
    parser.add_argument(
        "--github-repository",
        help="GitHub repository in format 'owner/repo' (required if --post-comment is used)",
    )
    parser.add_argument(
        "--post-comment",
        action="store_true",
        help="Post the report as a PR comment",
    )

    args = parser.parse_args()

    # Generate the report
    report = generate_report(
        results_dir=args.results_dir,
        pr_number=args.pr_number,
        commit_sha=args.commit_sha,
    )

    # Write to file
    try:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report written to {args.output}", file=sys.stderr)
    except Exception as e:
        print(f"Error writing report: {e}", file=sys.stderr)
        return 1

    # Print to stdout if requested
    if args.print:
        print(report)

    # Post PR comment if requested
    if args.post_comment:
        if not args.pr_number:
            print(
                "❌ Error: --pr-number is required when using --post-comment",
                file=sys.stderr,
            )
            return 1

        if not args.github_token:
            print(
                "❌ Error: --github-token is required when using --post-comment",
                file=sys.stderr,
            )
            return 1

        if not args.github_repository:
            print(
                "❌ Error: --github-repository is required when using --post-comment",
                file=sys.stderr,
            )
            return 1

        # Parse repository
        try:
            repo_owner, repo_name = args.github_repository.split("/")
        except ValueError:
            print(
                "❌ Error: --github-repository must be in format 'owner/repo'",
                file=sys.stderr,
            )
            return 1

        # Post comment
        success = post_pr_comment(
            repo_owner=repo_owner,
            repo_name=repo_name,
            pr_number=args.pr_number,
            report_content=report,
            github_token=args.github_token,
        )

        if not success:
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
