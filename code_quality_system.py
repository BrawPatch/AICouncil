import json
import urllib.request
import sys
import os
import ast
import tkinter as tk
from tkinter import filedialog
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/api/generate"

def query_local_llm(model_name, prompt):
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(OLLAMA_URL, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
            return res['response']
    except Exception as e:
        print(f"\n❌ Ollama connection failed for model '{model_name}': {e}")
        return f"Error: Failed to evaluate using {model_name}."

def perform_ast_check(file_path):
    """Performs a quick static analysis pass using Python's native parser."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()
        ast.parse(source)
        return "Passed basic AST compilation syntax check.\n"
    except SyntaxError as se:
        return f"⚠️ Syntax Error found by AST parser on line {se.lineno}: {se.msg}\n"
    except Exception as e:
        return f"Could not complete local AST pass: {e}\n"

def get_project_folder():
    """Opens a native OS folder picker dialogue window."""
    root = tk.Tk()
    root.withdraw()  # Hide the main small blank tkinter window
    root.lift()
    root.attributes("-topmost", True)  # Bring window to front on macOS
    
    print("📂 Opening folder picker... Please select your project directory.")
    selected_dir = filedialog.askdirectory(title="Select Project Directory to Audit")
    return selected_dir

def run_project_audit():
    project_path = get_project_folder()
    
    if not project_path:
        print("❌ Audit cancelled: No folder was selected.")
        return
        
    print(f"🎯 Target Project Selected: {project_path}")
    
    # Supported code extensions to parse (Swift added here)
    valid_extensions = ('.py', '.js', '.ts', '.go', '.rs', '.java', '.cpp', '.h', '.cs', '.swift')
    files_to_audit = []
    
    for root, _, files in os.walk(project_path):
        for file in files:
            if file.endswith(valid_extensions):
                files_to_audit.append(os.path.join(root, file))
                
    if not files_to_audit:
        print("❌ No valid code files found in the chosen directory.")
        return
        
    print(f"📚 Found {len(files_to_audit)} files to audit. Initialising council pipeline...")
    
    # Initialise centralized markdown report metadata
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    project_name = os.path.basename(project_path)
    report_filename = f"centralized_audit_report_{project_name}.md"
    
    markdown_content = f"""# Centralized Code Quality Audit Report
- **Project Folder:** `{project_path}`
- **Date Audited:** {timestamp}
- **Total Files Audited:** {len(files_to_audit)}

## Table of Contents
"""
    # Build Table of Contents links dynamically
    for file_path in files_to_audit:
        rel_path = os.path.relpath(file_path, project_path)
        anchor = rel_path.lower().replace(" ", "-").replace("/", "").replace(".", "")
        markdown_content += f"- [{rel_path}](#{anchor})\n"
        
    markdown_content += "\n---\n"

    # Process each code file sequentially
    for idx, file_path in enumerate(files_to_audit, 1):
        rel_path = os.path.relpath(file_path, project_path)
        print(f"\n🔬 [{idx}/{len(files_to_audit)}] Auditing: {rel_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code_content = f.read()
        except Exception as e:
            print(f"⚠️ Failed to read {rel_path}: {e}")
            continue

        # Truncate content slightly if file is massive to keep inside local context limits
        if len(code_content) > 30000:
            code_content = code_content[:30000] + "\n\n... [Code truncated due to file size limits] ..."

        ast_feedback = perform_ast_check(file_path) if file_path.endswith('.py') else "AST check only supported natively for Python source files."

        # Stage 1: Parallel Insights
        print("   ⌛ Step 1: Running parallel model inspections...")
        qwen_prompt = f"Analyze this source code structure file for language-specific logical flaws, performance bottlenecks, and dependency inefficiencies:\n\n{code_content}"
        ans_qwen = query_local_llm("qwen2.5-coder:7b", qwen_prompt)

        mistral_prompt = f"Analyze this source code file for architectural anti-patterns, missing exception handling, safety risks, and structural clarity flags:\n\n{code_content}"
        ans_mistral = query_local_llm("mistral:7b", mistral_prompt)

        # Stage 2: Peer Review Pass
        print("   ⌛ Step 2: Processing blind critiques...")
        critique_prompt = "Review this independent analysis of the file. Note errors, missing mitigations, or over-critical declarations made without seeing the system architecture:\n\n"
        review_of_qwen = query_local_llm("mistral:7b", f"{critique_prompt} Assessment: {ans_qwen}")
        review_of_mistral = query_local_llm("qwen2.5-coder:7b", f"{critique_prompt} Assessment: {ans_mistral}")

        # Stage 3: Unified Chairman Synthesis
        print("   ⌛ Step 3: Compiling structured file report...")
        chairman_prompt = f"""
You are the Technical Quality Assurance Lead. Review the code analysis documents for this project file.
Provide your output as structured markdown sections matching the template constraints below.

File Relative Path: {rel_path}
Local Static Check: {ast_feedback}

--- Inspector Transcripts ---
Inspector Qwen: {ans_qwen}
Peer Critique of Qwen: {review_of_qwen}
Inspector Mistral: {ans_mistral}
Peer Critique of Mistral: {review_of_mistral}
-----------------------------

Strictly adhere to this format layout for your response. Maintain clear headers:

## File: {rel_path}
- **Quality Score:** [X/100]
- **Static Status:** {ast_feedback.strip()}

### Logged Issues

#### [Issue Title 1]
- **Severity:** [Low | Medium | High | Critical]
- **Issue:** [Description of target problem]
- **Mitigation Required:** [Actionable adjustment or code fix pattern]
- **Dependencies:** [Affected code blocks, modules, runtime environment details, or framework impacts]

#### [Issue Title 2]
- **Severity:** ...
- **Issue:** ...
- **Mitigation Required:** ...
- **Dependencies:** ...
"""
        file_report = query_local_llm("llama3.1:8b", chairman_prompt)
        
        # Append this file's result to the central registry data array
        markdown_content += f"\n{file_report}\n\n---\n"

    # Write out the completed centralized report document
    try:
        with open(report_filename, 'w', encoding='utf-8') as rf:
            rf.write(markdown_content)
        print(f"\n✨ **Project Audit Complete!** Unified report created: `{report_filename}`\n")
    except Exception as e:
        print(f"❌ Failed to build centralized markdown file: {e}")

if __name__ == "__main__":
    run_project_audit()
