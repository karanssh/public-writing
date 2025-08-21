#!/usr/bin/env python3
"""
Deploy helper: copies posts, runs hugo, updates the public repo,
updates the source repo, and updates the repo that contains this script.

Defaults (used when you pass no args):
  source-dir: /home/karan/projects/karanssh-site-v2
  public-dir: /home/karan/projects/karanssh.github.io
  deploy-dir: /home/karan/projects/public-writing
  branch: main (for public + deploy)
  source-branch: master (for karanssh-site-v2)
"""

import argparse
import datetime
import subprocess
import sys
import shutil
from pathlib import Path

# Hardcoded defaults
DEFAULT_SOURCE_DIR = Path("/home/karan/projects/karanssh-site-v2")
DEFAULT_PUBLIC_DIR = Path("/home/karan/projects/karanssh.github.io")
DEFAULT_DEPLOY_DIR = Path("/home/karan/projects/public-writing")
DEFAULT_BRANCH = "main"
DEFAULT_SOURCE_BRANCH = "master"


def run(cmd, cwd=None, check=True):
    """Run command, print stdout/stderr, raise on non-zero if check=True."""
    cwd_display = cwd or Path.cwd()
    print(f"\n> Running: {' '.join(cmd)} (cwd={cwd_display})")
    try:
        completed = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            check=check,
        )
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit {e.returncode}")
        if e.stdout:
            print("stdout:")
            print(e.stdout)
        if e.stderr:
            print("stderr:")
            print(e.stderr)
        raise
    else:
        if completed.stdout:
            print("stdout:")
            print(completed.stdout)
        if completed.stderr:
            print("stderr:")
            print(completed.stderr)
        return completed


def has_working_changes(repo_dir: Path) -> bool:
    """Return True if git status --porcelain shows changes."""
    res = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(repo_dir),
        capture_output=True,
        text=True,
        check=False,
    )
    return bool(res.stdout.strip())


def maybe_commit_and_push(repo_dir: Path, message: str, branch: str, dry_run: bool):
    """git add -A; git commit -m message if changes; git push origin branch."""
    print(f"\n--- Processing repo: {repo_dir}")
    if dry_run:
        print(f"[dry-run] Would run: git add -A (cwd={repo_dir})")
    else:
        run(["git", "add", "-A"], cwd=str(repo_dir))

    if dry_run:
        print(f"[dry-run] Would check for changes in {repo_dir}")
        changes = True
    else:
        changes = has_working_changes(repo_dir)

    if not changes:
        print(f"No changes to commit in {repo_dir}. Skipping commit/push.")
        return

    if dry_run:
        print(f"[dry-run] Would run: git commit -m '{message}' (cwd={repo_dir})")
        print(f"[dry-run] Would run: git push origin {branch} (cwd={repo_dir})")
    else:
        run(["git", "commit", "-m", message], cwd=str(repo_dir))
        run(["git", "push", "origin", branch], cwd=str(repo_dir))


def copy_posts(deploy_dir: Path, source_dir: Path):
    """Copy all files/folders from deploy_dir into source_dir/content/post,
    skipping .git and deploy.py."""
    dest = source_dir / "content" / "post"
    dest.mkdir(parents=True, exist_ok=True)

    for item in deploy_dir.iterdir():
        if item.name == ".git" or item.name == "deploy.py":
            continue
        target = dest / item.name

        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)
    print(f"Copied content from {deploy_dir} → {dest}")


def main():
    parser = argparse.ArgumentParser(description="Hugo build + git deploy helper (3 repos)")
    parser.add_argument("--source-dir", default=DEFAULT_SOURCE_DIR, type=Path)
    parser.add_argument("--public-dir", default=DEFAULT_PUBLIC_DIR, type=Path)
    parser.add_argument("--deploy-dir", default=DEFAULT_DEPLOY_DIR, type=Path)
    parser.add_argument("--branch", default=DEFAULT_BRANCH, help="Branch for public + deploy repos")
    parser.add_argument("--source-branch", default=DEFAULT_SOURCE_BRANCH, help="Branch for source repo")
    parser.add_argument("--commit-prefix-source", default="Update source at")
    parser.add_argument("--commit-prefix-public", default="Deploy site at")
    parser.add_argument("--commit-prefix-deploy", default="Update deploy script at")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    source_dir = Path(args.source_dir).expanduser().resolve()
    public_dir = Path(args.public_dir).expanduser().resolve()
    deploy_dir = Path(args.deploy_dir).expanduser().resolve()

    print("Configuration:")
    print(f"  source_dir: {source_dir}")
    print(f"  public_dir: {public_dir}")
    print(f"  deploy_dir: {deploy_dir}")
    print(f"  branch (public+deploy): {args.branch}")
    print(f"  source_branch: {args.source_branch}")
    print(f"  dry_run: {args.dry_run}")

    # Ensure unique list of repos (avoid duplicate commits if paths overlap)
    unique_repos = []
    for p in (public_dir, source_dir, deploy_dir):
        if p not in unique_repos:
            unique_repos.append(p)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

    try:
        # Step 1: Copy posts from deploy_dir → source_dir/content/post
        copy_posts(deploy_dir, source_dir)

        # Step 2: Run hugo in source_dir, output to public_dir
        hugo_cmd = ["hugo", "--destination", str(public_dir)]
        if args.dry_run:
            print(f"[dry-run] Would run: {' '.join(hugo_cmd)} (cwd={source_dir})")
        else:
            run(hugo_cmd, cwd=str(source_dir))

        # Step 3: For the public repo: checkout branch & pull
        if args.dry_run:
            print(f"[dry-run] Would: git checkout {args.branch} && git pull origin {args.branch} (cwd={public_dir})")
        else:
            run(["git", "checkout", args.branch], cwd=str(public_dir))
            run(["git", "pull", "origin", args.branch], cwd=str(public_dir))

        # Step 4: Commit/push each repo as needed
        public_commit_msg = f"{args.commit_prefix_public} {timestamp}"
        source_commit_msg = f"{args.commit_prefix_source} {timestamp}"
        deploy_commit_msg = f"{args.commit_prefix_deploy} {timestamp}"

        msg_map = {
            str(public_dir): public_commit_msg,
            str(source_dir): source_commit_msg,
            str(deploy_dir): deploy_commit_msg,
        }

        branch_map = {
            str(public_dir): args.branch,
            str(source_dir): args.source_branch,
            str(deploy_dir): args.branch,
        }

        for repo_path in unique_repos:
            repo_msg = msg_map.get(str(repo_path), f"Update repo at {timestamp}")
            repo_branch = branch_map.get(str(repo_path), args.branch)
            maybe_commit_and_push(repo_path, repo_msg, repo_branch, args.dry_run)

        print("\nDone.")
    except Exception as exc:
        print("\nError during deployment:")
        print(exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
