import json
import urllib.request
import sys
import os
import csv
import subprocess
import tkinter as tk
from tkinter import filedialog
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/api/generate"
MAX_REPAIR_ATTEMPTS = 5

SUPPORTED_LANGUAGES = {
    "1": {"name": "Python", "ext": ".py", "style": "PEP 8 snake_case conventions. Low-level components inside `src/`, unit tests matching `tests/*_test.py` naming standards.", "test_cmd": lambda out: ["python3", "-m", "unittest", "discover", "-s", out, "-p", "*_test.py"]},
    "2": {"name": "JavaScript", "ext": ".js", "style": "Standard camelCase nomenclature. Modular functions separated into `lib/`, unit tests stored under `tests/**/*.test.js` names.", "test_cmd": lambda out: ["node", "--test", f"{out}/**/*.test.js"]},
    "3": {"name": "TypeScript", "ext": ".ts", "style": "Strict camelCase standards. Structural interfaces inside `src/types/`, implementations under `src/`, test files in `src/__tests__/*.test.ts` format.", "test_cmd": lambda out: ["bun", "test", out] if os.path.exists(os.path.expanduser("~/.bun")) else ["npx", "jest", out]},
    "4": {"name": "Go", "ext": ".go", "style": "Idiomatic Go camelCase layout. Package files grouped logically in sub-directories matching purpose, matching file names with `_test.go` suffixes.", "test_cmd": lambda out: ["go", "test", f"{out}/..."]},
    "5": {"name": "Rust", "ext": ".rs", "style": "Rust snake_case architecture rules. Implementation items structured across standard `src/` modules, unit tests placed inside a `tests/` integration workspace layout.", "test_cmd": lambda out: ["cargo", "test", "--manifest-path", f"{out}/Cargo.toml"]},
    "6": {"name": "Swift", "ext": ".swift", "style": "Swift API Design Guidelines camelCase patterns. Logical grouping inside `Sources/[TargetName]/` folders, related structural tests inside `Tests/[TargetName]Tests/` trees.", "test_cmd": lambda out: ["swift", "test", "--package-path", out]}
}

def query_local_llm(model_name, prompt):
    payload = {"model": model_name, "prompt": prompt, "stream": False}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(OLLAMA_URL, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
            return res['response']
    except Exception as e:
        print(f"\n❌ Ollama connection failed for model '{model_name}': {e}")
        return f"Error: Failed to evaluate using {model_name}."

def select_input_file(title, ext_desc, ext):
    root = tk.Tk(); root.withdraw(); root.lift(); root.attributes("-topmost", True)
    print(f"📂 Select: {title}")
    return filedialog.askopenfilename(title=title, filetypes=[(ext_desc, ext)])

def select_directory(title):
    root = tk.Tk(); root.withdraw(); root.lift(); root.attributes("-topmost", True)
    print(f"📂 Select Folder: {title}")
    return filedialog.askdirectory(title=title)

def prompt_language_selection():
    print("\n🌐 Supported Languages Registry:")
    for key, lang in SUPPORTED_LANGUAGES.items():
        print(f"  [{key}] {lang['name']} ({lang['ext']})")
    choice = input("\n⌨️ Choose the stack number to develop in: ").strip()
    return SUPPORTED_LANGUAGES.get(choice, SUPPORTED_LANGUAGES["1"])

def prompt_database_configuration():
    print("\n🗄️ Database Architecture Configuration:")
    print("  Mock Database Fixtures / In-Memory (Default)")
    print("  Real Database Connection Layer")
    db_choice = input("\n⌨️ Select database strategy [1 or 2]: ").strip()
    if db_choice == "2":
        db_type = input("   Database Type (e.g., PostgreSQL, SQLite): ").strip() or "SQLite"
        db_conn = input("   Connection Details / URL: ").strip() or ":memory:"
        return {"mode": "REAL", "description": f"Real {db_type} database via connection: '{db_conn}'."}
    return {"mode": "MOCK", "description": "Strictly use isolated mock objects, fixtures, interfaces, or in-memory array structures."}

def setup_git_repository(project_dir):
    """Initialises the local Git repository and maps the secure GitHub remote origin profile."""
    if not os.path.exists(os.path.join(project_dir, ".git")):
        print("🐙 Initialising new local Git repository workspace...")
        subprocess.run(["git", "init", "-b", "main"], cwd=project_dir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "FirstDevBot"], cwd=project_dir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "bot@local.dev"], cwd=project_dir, capture_output=True)

    print("\n🐙 GitHub Secure Remote Setup:")
    print("   Provide your GitHub repository URL (e.g., git@github.com:username/repo.git or https://github.com...)")
    remote_url = input("🔗 GitHub Remote URL: ").strip()
    
    if remote_url:
        # Prevent collision errors on subsequent runs by resetting the origin mapping cleanly
        subprocess.run(["git", "remote", "remove", "origin"], cwd=project_dir, capture_output=True)
        result = subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=project_dir, capture_output=True)
        if result.returncode == 0:
            print("✅ Linked remote 'origin' configuration mapping successfully.")
            return True
        else:
            print("⚠️ Critical: Could not execute remote origin tracking command hooks.")
    return False

def update_changelog(project_dir, story_id, description, criteria):
    changelog_path = os.path.join(project_dir, "CHANGELOG.md")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    entry_content = f"""
### [{story_id}] - {timestamp}
- **Description:** {description}
- **Acceptance Criteria Met:** *{criteria}*
- **Status:** `Verified & Deployed via TDD Harness`
"""
    
    if not os.path.exists(changelog_path):
        header = f"# Changelog\nAll notable changes to this project will be documented in this file automatically.\n\n## - Initial Development Run\n"
        with open(changelog_path, "w", encoding="utf-8") as f:
            f.write(header + entry_content)
    else:
        with open(changelog_path, "r", encoding="utf-8") as f:
            current_data = f.read()
        
        split_marker = "documented in this file automatically.\n"
        if split_marker in current_data:
            parts = current_data.split(split_marker)
            updated_data = parts[0] + split_marker + entry_content + parts[1]
        else:
            updated_data = current_data + "\n" + entry_content
            
        with open(changelog_path, "w", encoding="utf-8") as f:
            f.write(updated_data)
    print("📝 Centralised CHANGELOG.md log entry appended.")

def execute_secure_git_push(project_dir, story_id, description, push_enabled):
    """Stages files, commits code transformations, and runs the automated git push command block hook."""
    print(f"📦 Staging code modifications and running local Git commit tracking...")
    subprocess.run(["git", "add", "."], cwd=project_dir, capture_output=True)
    
    commit_msg = f"feat({story_id.lower()}): {description[:50]}\n\nAutomated validation release by FirstDevBot."
    subprocess.run(["git", "commit", "-m", commit_msg], cwd=project_dir, capture_output=True)
    
    if push_enabled:
        print(f"📤 Triggering git push command hook downstream target... (`main` branch)")
        
        # Explicit push block tracking setup targeting primary default main branches
        push_res = subprocess.run(["git", "push", "-u", "origin", "main"], cwd=project_dir, capture_output=True, text=True)
        
        if push_res.returncode == 0:
            print("🚀 Secure Git Push Hook Execution: Successfully synchronised changes upstream with GitHub repo!")
        else:
            print("\n⚠️ Push Hook warning: Local codebase passed verification, but sync out failed.")
            print("   Check your local Mac SSH-agent keys (`ssh-add -l`) or network context profiles.")
            print(f"   Git Error Trace: {push_res.stderr.strip()}")

def write_generated_files(output_dir, structure_raw):
    lines = structure_raw.split('\n')
    current_file_path = None
    current_content = []
    created_files = []

    for line in lines:
        if line.startswith("=== FILE:") or line.startswith("FILE:"):
            if current_file_path and current_content:
                full_path = os.path.join(output_dir, current_file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write("\n".join(current_content).strip())
                created_files.append(full_path)
            current_file_path = line.replace("=== FILE:", "").replace("===", "").replace("FILE:", "").strip()
            current_content = []
        elif current_file_path is not None:
            if line.strip() != "```" and not line.strip().startswith("```"):
                current_content.append(line)

    if current_file_path and current_content:
        full_path = os.path.join(output_dir, current_file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(current_content).strip())
        created_files.append(full_path)
    return created_files

def run_automated_tests(output_dir, lang_config):
    cmd = lang_config['test_cmd'](output_dir)
    print(f"🚀 Harness executing unit tests: `{' '.join(cmd)}`")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=output_dir, timeout=30)
        passed = (result.returncode == 0)
        logs = result.stdout + "\n" + result.stderr
        return passed, logs
    except Exception as e:
        return False, f"Harness execution failure running test suite framework: {str(e)}"

def start_dev_bot():
