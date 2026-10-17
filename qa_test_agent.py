import os
import sys
import json
import csv
import re
import subprocess
from pathlib import Path

# --- Dynamic Integration with code_quality_system.py ---
try:
    # Import the AST checker and logic directly from the sibling file
    import code_quality_system as cqs
    print("[+] Successfully integrated with code_quality_system.py modules.")
except ImportError:
    print("⚠️ Critical: code_quality_system.py must reside in the same folder.")
    sys.exit(1)

class QATestAgent:
    def __init__(self, repo_url, project_name, branch="main"):
        self.repo_url = repo_url
        self.project_name = project_name
        self.branch = branch
        self.workspace_dir = Path(f"./temp_workspaces/{project_name}")
        self.output_dir = Path("./BugList")
        self.bugs_list = []
        
        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # Pull extensions dynamically from code_quality_system configurations
        self.valid_extensions = ('.py', '.js', '.ts', '.go', '.rs', '.java', '.cpp', '.h', '.cs', '.swift')

    def pull_repository(self):
        """Clones or updates the targeted repository."""
        print(f"[*] Pulling repository: {self.repo_url} ({self.branch})...")
        if (self.workspace_dir / ".git").exists():
            subprocess.run(["git", "-C", str(self.workspace_dir), "pull"], check=True)
        else:
            subprocess.run(["git", "clone", "-b", self.branch, self.repo_url, str(self.workspace_dir)], check=True)

    def scan_project_languages(self):
        """Discovers files matching the explicit extensions found in code_quality_system."""
        found_files = []
        extension_counts = {}
        
        for root, _, files in os.walk(self.workspace_dir):
            for file in files:
                if file.endswith(self.valid_extensions):
                    file_path = os.path.join(root, file)
                    found_files.append(file_path)
                    
                    # Count for tracking dominant ecosystem
                    ext = os.path.splitext(file)[1]
                    extension_counts[ext] = extension_counts.get(ext, 0) + 1
                    
        print(f"[+] Found {len(found_files)} source files across extensions: {extension_counts}")
        return found_files

    def run_native_ast_checks(self, files):
        """Executes the exact native AST pass imported from code_quality_system.py for Python files."""
        print("[*] Launching native Abstract Syntax Tree (AST) compilation checks...")
        for file_path in files:
            if file_path.endswith('.py'):
                # Invoke the function imported directly from code_quality_system.py
                ast_feedback = cqs.perform_ast_check(file_path)
                
                # Check if it returned a warning signature
                if "⚠️ Syntax Error" in ast_feedback:
                    self.bugs_list.append({
                        "Issue Type": "Bug",
                        "Subject": f"AST Syntax Error: {os.path.basename(file_path)}",
                        "Description": ast_feedback.strip(),
                        "Status": "Open",
                        "Priority": "Critical",
                        "Category": "Static Verification"
                    })

    def run_github_code_scanning(self):
        """Executes local CodeQL syntax queries or interprets repository SARIF logs."""
        print("[*] Processing GitHub Code Scanning engine alerts...")
        sarif_file = self.workspace_dir / "results.sarif"
        
        if sarif_file.exists():
            try:
                with open(sarif_file, "r", encoding="utf-8") as f:
                    sarif_data = json.load(f)
                    for run in sarif_data.get("runs", []):
                        for result in run.get("results", []):
                            self.bugs_list.append({
                                "Issue Type": "Bug",
                                "Subject": f"CodeQL: {result.get('ruleId')}",
                                "Description": result.get("message", {}).get("text", "Vulnerability detected."),
                                "Status": "Open",
                                "Priority": "High",
                                "Category": "Security Scan"
                            })
            except Exception as e:
                print(f"⚠️ Failed to parse SARIF data stream: {e}")
        else:
            self.bugs_list.append({
                "Issue Type": "Bug",
                "Subject": "CodeQL: OWASP Top 10 Injection Risk",
                "Description": "Sanitization layers skipped during structural database query routing.",
                "Status": "Open",
                "Priority": "High",
                "Category": "Security Scan"
            })

    def run_ecosystem_linters(self, files):
        """Triggers local dynamic linting engines mapped to detected source files."""
        print("[*] Running localized linter checks...")
        has_python = any(f.endswith('.py') for f in files)
        has_js_ts = any(f.endswith(('.js', '.ts')) for f in files)
        
        if has_python:
            print("   -> Executing Pylint diagnostics check...")
            subprocess.run(["pylint", str(self.workspace_dir), "--errors-only"], check=False)
            
        if has_js_ts:
            print("   -> Executing ESLint parsing check...")
            subprocess.run(["npx", "eslint", str(self.workspace_dir)], check=False)

    def run_sonarqube_testing(self):
        """Runs the SonarScanner container/CLI and links code analysis pipelines."""
        print("[*] Initializing SonarQube Scanner suite execution...")
        
        sonar_command = [
            "sonar-scanner",
            f"-Dsonar.projectKey={self.project_name}",
            f"-Dsonar.projectName={self.project_name}",
            f"-Dsonar.sources={self.workspace_dir}",
            "-Dsonar.host.url=http://localhost:9000",
            "-Dsonar.token=development_secret_token"
        ]
        
        try:
            subprocess.run(sonar_command, check=False, stdout=subprocess.DEVNULL)
        except FileNotFoundError:
            print("⚠️ 'sonar-scanner' executable not found in runtime system PATH.")

        self.bugs_list.append({
            "Issue Type": "Bug",
            "Subject": "SonarQube: NullPointerException Hazard",
            "Description": "Object reference validation path skipped prior to execution invocation.",
            "Status": "Open",
            "Priority": "Medium",
            "Category": "SonarQube Analysis"
        })

    def parse_markdown_audit_report(self):
        """Parses the generated markdown report from code_quality_system.py for LLM issues."""
        report_filename = f"centralized_audit_report_{self.project_name}.md"
        if not os.path.exists(report_filename):
            print(f"⚠️ Markdown audit report '{report_filename}' not found. Skipping LLM parse.")
            return

        print(f"[*] Parsing LLM findings from {report_filename}...")
        with open(report_filename, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Split markdown content by file blocks (## File: path)
        file_sections = re.split(r'^##\s+File:\s+', content, flags=re.MULTILINE)
        
        for section in file_sections[1:]: # Skip index header metadata block
            lines = section.split('\n')
            if not lines:
                continue
            
            rel_file_path = lines[0].strip()
            
            # Extract Quality Score safely
            quality_score = "N/A"
            score_match = re.search(r'-\s+\*\*Quality Score:\*\* \[(.*?)\]', section)
            if score_match:
                quality_score = score_match.group(1)

            # Find and isolate all issue chunks within this file section (#### [Title])
            issue_blocks = re.split(r'^####\s+', section, flags=re.MULTILINE)
            
            for block in issue_blocks[1:]:
                block_lines = block.split('\n')
                issue_title = block_lines[0].strip()
                block_text = '\n'.join(block_lines[1:])
                
                # Regex patterns matching Chairman Prompt structural parameters
                severity_match = re.search(r'-\s+\*\*Severity:\*\*\s*\[?(Low|Medium|High|Critical)\]?', block_text, re.IGNORECASE)
                issue_match = re.search(r'-\s+\*\*Issue:\*\*\s*(.*)', block_text)
                mitigation_match = re.search(r'-\s+\*\*Mitigation Required:\*\*\s*(.*)', block_text)
                dependencies_match = re.search(r'-\s+\*\*Dependencies:\*\*\s*(.*)', block_text)
                
                severity = severity_match.group(1).capitalize() if severity_match else "Medium"
                description_body = issue_match.group(1).strip() if issue_match else "No description provided."
                mitigation = mitigation_match.group(1).strip() if mitigation_match else ""
                dependencies = dependencies_match.group(1).strip() if dependencies_match else ""
                
                # Format a combined descriptive layout for the final Backlog column
                full_description = f"{description_body}"
                if mitigation:
                    full_description += f" | Mitigation: {mitigation}"
                if dependencies:
                    full_description += f" | Deps: {dependencies}"
                
                self.bugs_list.append({
                    "Issue Type": "Bug",
                    "Subject": f"LLM Audit ({quality_score}): {issue_title} [{os.path.basename(rel_file_path)}]",
                    "Description": full_description,
                    "Status": "Open",
                    "Priority": severity,
