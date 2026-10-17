import json
import urllib.request
import sys
import os
import re
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/api/generate"

STORY_FORMAT_INSTRUCTIONS = """Each user story MUST use exactly this format:

### [Priority: Must/Should/Could/Won't] <Short Story Title>
**Story:** As a <Role>, I want <X>, in order to do <Y>.

**Acceptance Criteria:**
- Given <context>, when <action>, then <outcome>
- (add as many criteria as needed to make the story testable and unambiguous)

Rules:
- Use MoSCoW priority labels (Must / Should / Could / Won't) based on how critical the story is to the stated functional aims.
- Order stories within the backlog from highest to lowest priority (Must first, then Should, then Could, then Won't).
- Break large or vague requirements down into multiple small, independently deliverable stories.
- Do not invent roles, features or constraints that aren't implied by the reference requirements; where you must assume something, say so briefly in the acceptance criteria.
- Do not include any commentary outside of the story blocks other than a single top-level "# Product Backlog" heading.
"""


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
        print(f"\n❌ Error connecting to Ollama for model {model_name}: {e}")
        print("Make sure the Ollama application is running.")
        sys.exit(1)


def load_requirements(path):
    """Reads high-level functional requirements from a specific file or all text files in a directory."""
    if not path:
        return ""

    path = os.path.expanduser(path.strip())

    if not os.path.exists(path):
        print(f"⚠️ Warning: Path '{path}' not found.")
        return ""

    combined_content = []

    if os.path.isfile(path):
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return f"\n--- Requirements File: {os.path.basename(path)} ---\n{f.read()}\n"
        except Exception as e:
            print(f"⚠️ Error reading file {path}: {e}")
            return ""

    elif os.path.isdir(path):
        print("📂 Reading requirement files from directory...")
        valid_extensions = ('.txt', '.md', '.log')
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(valid_extensions):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            combined_content.append(f"\n--- Requirements File: {file} ---\n{f.read()}\n")
                    except Exception as e:
                        print(f"⚠️ Skipping file {file} due to error: {e}")

    return "".join(combined_content)


def build_drafting_prompt(requirements_text):
    return f"""You are a member of a Product Owner council. Read the high-level functional requirements below and
draft a set of User Stories for the product backlog.

{STORY_FORMAT_INSTRUCTIONS}

[START OF REQUIREMENTS]
{requirements_text}
[END OF REQUIREMENTS]

Produce your draft backlog now.
"""


def build_critique_prompt(draft_backlog, requirements_text):
    return f"""You are reviewing a colleague's draft product backlog, written as a set of User Stories with
acceptance criteria, based on the requirements below. Critique it without knowing who wrote it.

Check specifically for:
- Missing or unclear roles ("As a <Role>")
- Stories that aren't independently deliverable or testable
- Vague or missing acceptance criteria
- Incorrect or inconsistent MoSCoW prioritisation
- Gaps: requirements that weren't turned into any story
- Duplicate or overlapping stories

[START OF REQUIREMENTS]
{requirements_text}
[END OF REQUIREMENTS]

[START OF DRAFT BACKLOG]
{draft_backlog}
[END OF DRAFT BACKLOG]

List the flaws, omissions and errors you find.
"""


def build_chairman_prompt(requirements_text, draft_a, critique_a, draft_b, critique_b):
    return f"""You are the Product Owner Council Chairman. Two council members have each drafted a product backlog
of User Stories from the same requirements, and each draft has been critiqued by a peer. Synthesize a single,
final, prioritised product backlog that is the best of both drafts: incorporate valid critique points, remove
duplicates, fill gaps against the requirements, and ensure consistent MoSCoW prioritisation and formatting.

{STORY_FORMAT_INSTRUCTIONS}

[START OF REQUIREMENTS]
{requirements_text}
[END OF REQUIREMENTS]

Draft A:
{draft_a}

Critique of Draft A:
{critique_a}

Draft B:
{draft_b}

Critique of Draft B:
{critique_b}

Produce the final, synthesized, prioritised backlog now. Output ONLY the backlog in the specified format.
"""


def run_product_owner_council(requirements_path, output_path):
    print("=" * 60)
    print("      OLLAMA PRODUCT OWNER COUNCIL (Backlog Edition)    ")
    print("=" * 60)
    print("Models: Qwen2.5-Coder (7B) | Mistral (7B) | Llama3.1 (8B Chairman)\n")

    requirements_text = load_requirements(requirements_path)
    if not requirements_text:
        print("❌ No requirements loaded. Aborting.")
        sys.exit(1)

    print(f"📋 Loaded requirements (~{len(requirements_text)} characters).")
    print("-" * 40)

    # Stage 1: Parallel Drafting
    print("⌛ Step 1: Council members drafting independent backlogs...")
    drafting_prompt = build_drafting_prompt(requirements_text)
    draft_qwen = query_local_llm("qwen2.5-coder:7b", drafting_prompt)
    draft_mistral = query_local_llm("mistral:7b", drafting_prompt)

    # Stage 2: Blind Peer Reviews
    print("⌛ Step 2: Executing blind peer reviews...")
    review_of_qwen = query_local_llm(
        "mistral:7b", build_critique_prompt(draft_qwen, requirements_text)
    )
    review_of_mistral = query_local_llm(
        "qwen2.5-coder:7b", build_critique_prompt(draft_mistral, requirements_text)
    )

    # Stage 3: Chairman Synthesis
    print("⌛ Step 3: Chairman synthesizing final prioritised backlog...")
    final_prompt = build_chairman_prompt(
        requirements_text, draft_qwen, review_of_qwen, draft_mistral, review_of_mistral
    )
    final_backlog = query_local_llm("llama3.1:8b", final_prompt)

    print("-" * 40)
    print("\n👑 FINAL PRODUCT BACKLOG:\n")
    print(final_backlog)
    print("\n" + "=" * 60 + "\n")

    save_backlog(final_backlog, output_path)


def save_backlog(final_backlog, output_path):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    header = f"<!-- Generated by ProductOwner.py council on {timestamp} -->\n\n"
    content = final_backlog.strip()
    if not content.lstrip().startswith("#"):
        content = "# Product Backlog\n\n" + content

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(header + content + "\n")
        print(f"💾 Backlog saved to: {output_path}")
    except Exception as e:
        print(f"⚠️ Could not save backlog to {output_path}: {e}")


def default_output_path(requirements_path):
    base_dir = os.path.dirname(os.path.expanduser(requirements_path.strip())) or "."
    if os.path.isfile(os.path.expanduser(requirements_path.strip())):
        base_dir = os.path.dirname(os.path.expanduser(requirements_path.strip())) or "."
    return os.path.join(base_dir, "backlog.md")


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        req_path = sys.argv[1]
    else:
        req_path = input("📂 Enter path to requirements file or directory: ").strip()

    if len(sys.argv) >= 3:
        out_path = sys.argv[2]
    else:
        suggested = default_output_path(req_path) if req_path else "backlog.md"
        entered = input(f"💾 Enter output file path for backlog (or press Enter for '{suggested}'): ").strip()
        out_path = entered if entered else suggested

    run_product_owner_council(req_path, out_path)
