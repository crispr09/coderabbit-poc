#!/usr/bin/env python3
import os
import sys
import argparse
import re
from github import Github

SIMPLE_PATTERNS = [
    (re.compile(r"\bprint\(|console\.log\(|pdb\.set_trace\(|debugger\b"), "Debug/print statement detected."),
    (re.compile(r"TODO"), "TODO found."),
]

def get_changed_files(pr):
    return list(pr.get_files())

def run_checks(content):
    findings = []
    for pat, msg in SIMPLE_PATTERNS:
        if pat.search(content):
            findings.append(msg)
    if len(content.splitlines()) > 400:
        findings.append(f"File is long ({len(content.splitlines())} lines). Consider splitting.")
    return findings

def post_comment(pr, body):
    pr.create_issue_comment(body)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--repo', required=True)
    p.add_argument('--pr', required=True, type=int)
    args = p.parse_args()

    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print('GITHUB_TOKEN required')
        sys.exit(1)

    gh = Github(token)
    repo = gh.get_repo(args.repo)
    pr = repo.get_pull(args.pr)

    files = get_changed_files(pr)
    report = []
    for f in files:
        if f.patch is None:
            continue
        try:
            content = repo.get_contents(f.filename, ref=pr.head.ref).decoded_content.decode('utf-8', errors='ignore')
        except Exception:
            content = ''
        findings = run_checks(content)
        for fm in findings:
            report.append(f"- `{f.filename}`: {fm}")

    if not report:
        body = 'CodeRabbit Simple POC: No issues found by heuristics.'
    else:
        body = 'CodeRabbit Simple POC found the following:\n' + '\n'.join(report[:50])

    post_comment(pr, body)
    print('Posted review summary')

if __name__ == "__main__":
    main()
