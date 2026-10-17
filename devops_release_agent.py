import os
import sys
import csv
import re
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

class DevOpsReleaseAgent:
    def __init__(self, project_name, repo_dir, build_target=None):
        self.project_name = project_name
        self.repo_dir = Path(repo_dir)
        self.bug_list_dir = Path("./BugList")
        self.target_csv = self.bug_list_dir / f"{self.project_name}_bugList.csv"
        
        self.build_target = build_target
        self.sonar_url = "http://localhost:9000"
        
        # Git structural branches target setup
        self.dev_branch = "dev-branch"
        
        self.resolved_signatures = ["closed", "resolved", "verified", "complete", "done"]
        # Dev environment allows low/medium issues to pass, Test/Production are strict gatekeepers
        self.blocking_priorities = ["critical", "high"] if build_target != "dev" else ["critical"]

    def request_environment_configurations(self):
        """Prompts the user interactively for required variables if not supplied by the host pipeline."""
        print("\n--- 🛠️ DevOps Agent Deployment Configuration Wizard ---")
        
        if not self.build_target:
            print("Select Build Target Environment Option:")
            print(" 1) Development (Dev) -> Target: Git Dev Branch")
            print(" 2) Testing (Test)     -> Target: Git Dev Branch")
            print(" 3) Production (Prod)  -> Target: GitHub Main Release")
            choice = input("Enter index choice [1-3]: ").strip()
            
            mapping = {"1": "dev", "2": "test", "3": "production"}
            self.build_target = mapping.get(choice, "dev")
            
        print(f"Target Environment initialized to: [{self.build_target.upper()}]")
        
        custom_url = input(f"Provide SonarQube Base API URL Target [{self.sonar_url}]: ").strip()
        if custom_url:
            self.sonar_url = custom_url

    def verify_backlog_readiness(self):
        """Scans the backlog tracking metrics sheet for incomplete tasks."""
        print(f"[*] Analyzing backlog quality parameters for: {self.target_csv}...")
        if not self.target_csv.exists():
            print(f"❌ Aborting: Target release backlog file '{self.target_csv}' does not exist.")
            return False, []

        resolved_issues = []
        open_blockers = []

        with open(self.target_csv, mode="r", newline="", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                issue_id = row.get("ID", "UNKNOWN")
                subject = row.get("Subject", "No Subject")
                status = row.get("Status", "").strip().lower()
                priority = row.get("Priority", "").strip().lower()
                category = row.get("Category", "General")

                is_resolved = any(sig in status for sig in self.resolved_signatures)
                if is_resolved:
                    resolved_issues.append({"id": issue_id, "subject": subject, "category": category})
                else:
                    if any(prio in priority for prio in self.blocking_priorities):
                        open_blockers.append(f"[{issue_id}] ({row.get('Priority')}) {subject}")

        if open_blockers:
            print(f"\n❌ Release Pipeline Blocked for {self.build_target.upper()}: Unresolved items remain:")
            for blocker in open_blockers:
                print(f"   - {blocker}")
            return False, []

        return True, resolved_issues

    def calculate_next_version(self):
        """Calculates dynamic release syntax metadata tags matching current deployment tier rules."""
        base_tag = "v1.0.0"
        try:
            result = subprocess.run(
                ["git", "-C", str(self.repo_dir), "describe", "--tags", "--abbrev=0"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
            )
            base_tag = result.stdout.strip()
        except Exception:
            pass

        if self.build_target == "dev":
            return f"{base_tag}-dev-{datetime.now().strftime('%H%M')}"
        elif self.build_target == "test":
            return f"{base_tag}-rc-{datetime.now().strftime('%d%m')}"
        
        match = re.match(r'v?(\d+)\.(\d+)\.(\d+)', base_tag)
        if match:
            major, minor, patch = map(int, match.groups())
            return f"v{major}.{minor}.{patch + 1}"
        return "v1.0.1"

    def generate_and_save_release_notes(self, resolved_items, version):
        """Constructs and saves a persistent RELEASE_NOTES.md asset to the repository root."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        markdown = f"# Release Artifact: {version}\n"
        markdown += f"- **Deployment Target Environment:** `{self.build_target.upper()}`\n"
        markdown += f"- **Timestamp Verified:** {timestamp}\n"
        markdown += f"- **SonarQube Quality Source Registry:** {self.sonar_url}\n\n"
        markdown += "## 🛠️ Resolved Build Changelog Components\n"

        categories = {}
        for item in resolved_items:
            cat = item["category"]
            categories.setdefault(cat, []).append(f"**{item['id']}**: {item['subject']}")

        for cat, items in categories.items():
            markdown += f"\n### {cat}\n"
            for line in items:
                markdown += f"- {line}\n"

        notes_path = self.repo_dir / "RELEASE_NOTES.md"
        with open(notes_path, "w", encoding="utf-8") as f:
            f.write(markdown)
            
        print(f"[+] Release Notes documentation asset written locally to: {notes_path}")
        return notes_path

    def ensure_git_user_configured(self):
        """Checks for existing git user identity config and populates defaults if missing."""
        print("[*] Validating runner workspace Git user configurations...")
        try:
            # Query username
            name_check = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True, cwd=str(self.repo_dir))
            # Query email
            email_check = subprocess.run(["git", "config", "user.email"], capture_output=True, text=True, cwd=str(self.repo_dir))
            
            if not name_check.stdout.strip():
                print("   -> 'user.name' missing. Setting up fallback runner profile identifier...")
                subprocess.run(["git", "config", "local", "user.name", "DevOps Agent"], check=True, cwd=str(self.repo_dir))
                
            if not email_check.stdout.strip():
                print("   -> 'user.email' missing. Setting up fallback runner profile contact...")
                subprocess.run(["git", "config", "local", "user.email", "devops-agent@ci.local"], check=True, cwd=str(self.repo_dir))
                
            print("✔ Git user metadata constraints satisfied.")
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Non-blocking error verified during identity parsing initialization setup: {e}")

    def update_development_branch(self, version, notes_path):
        """Pushes the generated release notes onto a separate Git tracking branch for dev/test verification."""
        print(f"[*] Diverting deployment payload to local Git tracking branch: '{self.dev_branch}'...")
        try:
            # Enforce configuration initialization safety policies
            self.ensure_git_user_configured()
            
            # 1. Fetch latest changes from remote tracking records
            subprocess.run(["git", "fetch", "origin"], check=True, cwd=str(self.repo_dir))
            
            # 2. Check if the target branch exists locally, otherwise track it from remote or build fresh
            branch_check = subprocess.run(["git", "show-ref", f"refs/heads/{self.dev_branch}"], capture_output=True, text=True, cwd=str(self.repo_dir))
            
            if branch_check.returncode == 0:
                subprocess.run(["git", "checkout", self.dev_branch], check=True, cwd=str(self.repo_dir))
                subprocess.run(["git", "pull", "origin", self.dev_branch], check=False, cwd=str(self.repo_dir))
            else:
                # Build branch fresh if it doesn't exist
                subprocess.run(["git", "checkout", "-b", self.dev_branch], check=True, cwd=str(self.repo_dir))
            
            # 3. Stage and commit the Release Notes asset document
            subprocess.run(["git", "add", "RELEASE_NOTES.md"], check=True, cwd=str(self.repo_dir))
            commit_message = f"chore(release): update {self.build_target.upper()} notes for version {version}"
            subprocess.run(["git", "commit", "-m", commit_message], check=True, cwd=str(self.repo_dir))
            
            # 4. Push updates to remote development ecosystem branch tracking parameters
            subprocess.run(["git", "push", "origin", self.dev_branch], check=True, cwd=str(self.repo_dir))
            print(f"✨ Successfully updated Git development branch '{self.dev_branch}' with version build details.")
            
            # Return to main working tree branch to leave context clean
            subprocess.run(["git", "checkout", "-"], check=False, cwd=str(self.repo_dir))
        except subprocess.CalledProcessError as e:
            print(f"❌ Error operating internal Git branch lifecycle loops: {e}")

    def publish_github_release(self, version, notes_path):
        """Publishes production builds directly to GitHub Releases using native system CLI parameters."""
        print(f"[*] Dispatching production GitHub Release configuration for version '{version}'...")
        try:
            subprocess.run([
                "gh", "release", "create", version,
                "--title", f"[PRODUCTION] Release {version}",
                "--notes-file", str(notes_path),
                "--target", "main"
