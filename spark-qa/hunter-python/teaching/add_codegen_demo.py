#!/usr/bin/env python3
"""
ADD CODEGEN DEMO - Helper script to add Playwright codegen demonstrations

WORKFLOW:
1. Run: playwright codegen https://staging.hostfully.com
2. Record interaction
3. Copy generated code
4. Run this script with the code snippet

USAGE:
    python add_codegen_demo.py

Then follow prompts to paste your codegen and describe what it does.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from claude_teacher import ClaudeTeacher
import json

def add_interactive_demo():
    """Interactive prompt to add a codegen demo"""
    print("\n" + "="*70)
    print("ADD CODEGEN DEMO - Imitation Learning Helper")
    print("="*70 + "\n")
    
    teacher = ClaudeTeacher()
    
    # Get task description
    print("What does this demo do? (e.g., 'Click property kebab menu')")
    task = input("> ").strip()
    
    # Get what was tried before (optional)
    print("\nWhat failed before? (comma-separated, or press Enter to skip)")
    tried_failed_input = input("> ").strip()
    tried_failed = [x.strip() for x in tried_failed_input.split(",")] if tried_failed_input else []
    
    # Get solution name
    print("\nWhat's the working solution? (e.g., 'data-testid selector')")
    solution = input("> ").strip()
    
    # Get codegen snippet
    print("\nPaste Playwright codegen code (end with empty line):")
    code_lines = []
    while True:
        line = input()
        if not line.strip():
            break
        code_lines.append(line)
    
    code = "\n".join(code_lines)
    
    # Get reasoning
    print("\nWhy does this work? (brief explanation)")
    reasoning = input("> ").strip()
    
    # Is it generalizable?
    print("\nCan this be reused for similar tasks? (y/n)")
    generalizable = input("> ").lower().strip() == 'y'
    
    # Log teaching
    teacher.teach(
        task=task,
        tried_failed=tried_failed,
        working_solution=solution,
        code=code,
        reasoning=reasoning,
        generalizable=generalizable
    )
    
    print("\n" + "="*70)
    print("[OK] Demo added successfully!")
    print(f"Total teachings: {len(teacher.get_all_teachings())}")
    print("\nNext steps:")
    print("1. Run more training cycles to let RL learn from this")
    print("2. Teaching will be loaded in PHASE 4.7 of atomic_loop")
    print("="*70 + "\n")


def add_batch_demos(demos_file: str):
    """Add multiple demos from a JSON file"""
    print(f"\n[INFO] Loading demos from {demos_file}...")
    
    with open(demos_file, 'r', encoding='utf-8') as f:
        demos = json.load(f)
    
    teacher = ClaudeTeacher()
    
    for demo in demos['demos']:
        teacher.teach(
            task=demo['task'],
            tried_failed=demo.get('tried_failed', []),
            working_solution=demo['solution'],
            code=demo['code'],
            reasoning=demo.get('reasoning', ''),
            generalizable=demo.get('generalizable', True)
        )
    
    print(f"\n[OK] Added {len(demos['demos'])} demos")
    print(f"Total teachings: {len(teacher.get_all_teachings())}\n")


def show_examples():
    """Show example demo format"""
    print("\n" + "="*70)
    print("EXAMPLE CODEGEN DEMO FORMAT")
    print("="*70 + "\n")
    
    example = {
        "task": "Click property kebab menu",
        "tried_failed": ["role button click", "text selector"],
        "solution": "data-testid selector",
        "code": "page.get_by_test_id('kebab-menu').click()",
        "reasoning": "Kebab menu has stable test-id, more reliable than role",
        "generalizable": True
    }
    
    print("Single demo example:")
    print(json.dumps(example, indent=2))
    
    print("\n\nBatch file format (demos.json):")
    batch_example = {
        "demos": [example]
    }
    print(json.dumps(batch_example, indent=2))
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--batch":
            if len(sys.argv) < 3:
                print("[ERROR] Usage: python add_codegen_demo.py --batch demos.json")
                sys.exit(1)
            add_batch_demos(sys.argv[2])
        elif sys.argv[1] == "--examples":
            show_examples()
        else:
            print("[ERROR] Unknown argument. Use --batch <file> or --examples")
            sys.exit(1)
    else:
        add_interactive_demo()

