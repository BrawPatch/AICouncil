import json
import urllib.request
import sys
import os

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
        print(f"\n❌ Error connecting to Ollama for model {model_name}: {e}")
        print("Make sure the Ollama application is running.")
        sys.exit(1)

def load_context_files(path):
    """Reads content from a specific file or all text files in a directory."""
    if not path:
        return ""
        
    path = os.path.expanduser(path.strip())
    
    if not os.path.exists(path):
        print(f"⚠️ Warning: Path '{path}' not found. Proceeding without extra context.")
        return ""
        
    combined_content = []
    
    # If it's a single file
    if os.path.isfile(path):
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return f"\n--- Reference File: {os.path.basename(path)} ---\n{f.read()}\n"
        except Exception as e:
            print(f"⚠️ Error reading file {path}: {e}")
            return ""
            
    # If it's a directory
    elif os.path.isdir(path):
        print("📂 Reading text files from directory...")
        valid_extensions = ('.txt', '.md', '.log', '.json')
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(valid_extensions):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            combined_content.append(f"\n--- Reference File: {file} ---\n{f.read()}\n")
                    except Exception as e:
                        print(f"⚠️ Skipping file {file} due to error: {e}")
                        
    return "".join(combined_content)

def run_council():
    print("=" * 60)
    print("      OLLAMA COUNCIL OF LLMs (Context-Aware Edition)    ")
    print("=" * 60)
    print("Models: Qwen2.5-Coder (7B) | Mistral (7B) | Llama3.1 (8B Chairman)")
    print("Type 'exit' or 'quit' to end the session.\n")

    while True:
        # 1. Main prompt input
        user_query = input("💬 Ask the Council: ").strip()
        
        if not user_query:
            continue
        
        if user_query.lower() in ['exit', 'quit']:
            print("\n👋 Council adjourned. Goodbye!")
            break

        # 2. File / Directory context path input
        context_path = input("📂 Enter file or directory path for reference context (or press Enter to skip): ").strip()
        
        # Load and parse files if provided
        context_data = load_context_files(context_path)
        
        # Build the final prompt payload with embedded context if it exists
        if context_data:
            print(f"📋 Loaded context successfully (~{len(context_data)} characters).")
            full_prompt = f"Use the following reference context to help answer the user prompt:\n\n[START OF REFERENCE CONTEXT]\n{context_data}\n[END OF REFERENCE CONTEXT]\n\nUser Prompt: {user_query}"
        else:
            full_prompt = user_query

        print("\n" + "-" * 40)
        
        # Stage 1: Parallel Generation
        print("⌛ Step 1: Gathering independent answers...")
        ans_qwen = query_local_llm("qwen2.5-coder:7b", full_prompt)
        ans_mistral = query_local_llm("mistral:7b", full_prompt)

        # Stage 2: Blind Peer Reviews
        print("⌛ Step 2: Executing blind peer reviews...")
        critique_prompt = "Review this solution to the prompt based on the provided query and context. Note its flaws, omissions, or errors without knowing who wrote it:\n\n"
        review_of_qwen = query_local_llm("mistral:7b", f"{critique_prompt} Answer: {ans_qwen}")
        review_of_mistral = query_local_llm("qwen2.5-coder:7b", f"{critique_prompt} Answer: {ans_mistral}")

        # Stage 3: Chairman Synthesis
        print("⌛ Step 3: Chairman synthesizing final verdict...")
        final_synthesis_prompt = f"""
You are the Council Chairman. Review the two responses to the user's prompt alongside their peer critiques. 
Synthesize them into the absolute best, most accurate, and comprehensive final answer based closely on any reference context provided.

User Prompt: {user_query}

Response A: {ans_qwen}
Critique of Response A: {review_of_qwen}

Response B: {ans_mistral}
Critique of Response B: {review_of_mistral}

Final Verdict:
"""
        final_verdict = query_local_llm("llama3.1:8b", final_synthesis_prompt)

        print("-" * 40)
        print("\n👑 FINAL COUNCIL VERDICT:")
        print(final_verdict)
        print("\n" + "=" * 60 + "\n")

if __name__ == "__main__":
    run_council()