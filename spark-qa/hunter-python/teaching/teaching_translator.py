"""
TEACHING TRANSLATOR - Traduz descobertas do Claude para linguagem RL

PROBLEMA: Claude salva em formato narrativo (texto)
SOLUO: Traduz para action_sequence que RL entende

FORMATO ENTRADA (Claude):
{
  "task": "Navigate to properties",
  "tried_failed": ["menu click"],
  "working_solution": "URL navigation",
  "code": "page.goto('#/properties')",
  "reasoning": "Menu invisible"
}

FORMATO SADA (RL):
{
  "pattern": "navigate_properties",
  "action_sequence": [
    {"step": 1, "action": "goto", "params": {"url": "#/properties"}, "selector": null}
  ],
  "confidence": 1.0
}
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class TeachingTranslator:
    """
    Traduz Claude teachings para formato que RL entende e pode executar
    """

    def __init__(self):
        self.teachings_file = Path("../barril!!/claude_teachings.json")
        self.translated_file = Path("../barril!!/claude_teachings_rl_format.json")

        # Mapeamento de cdigo Python  action + params
        self.code_patterns = {
            r"page\.goto\(['\"](.+?)['\"]\)": {"action": "goto", "param_key": "url"},
            r"page\.goto\(f?['\"](.+?)['\"]\)": {"action": "goto", "param_key": "url"},  # f-string support
            r"page\.get_by_test_id\(['\"](.+?)['\"]\)\.click\(\)": {"action": "click_testid", "param_key": "testid"},
            r"page\.get_by_role\(['\"](.+?)['\"],\s*name=['\"](.+?)['\"]\)\.click\(\)": {"action": "click_role", "param_key": "role"},
            r"page\.locator\(['\"](.+?)['\"]\)\.fill\(['\"](.+?)['\"]\)": {"action": "fill", "param_key": "selector"},
            r"page\.locator\(['\"](.+?)['\"]\)\.select_option\(['\"](.+?)['\"]\)": {"action": "select", "param_key": "selector"},
            r"page\.get_by_test_id\(['\"](.+?)['\"]\)\.select_option\(['\"](.+?)['\"]\)": {"action": "select_testid", "param_key": "testid"},  # NEW: testid select
            r"page\.keyboard\.press\(['\"](.+?)['\"]\)": {"action": "keyboard", "param_key": "key"},
            r"page\.wait_for_timeout\((\d+)\)": {"action": "wait", "param_key": "ms"},
            r"page\.goto\(f?['\"]\{(.+?)\}#/(.+?)['\"]\)": {"action": "goto_hash", "param_key": "section"},  # NEW: base_url + hash
        }

    def translate_teaching(self, teaching: Dict) -> Dict:
        """
        Traduz 1 teaching de Claude para formato RL

        Claude format:
        {
          "task": "Navigate to properties",
          "code": "page.goto('#/properties')",
          "reasoning": "..."
        }

        RL format:
        {
          "pattern_name": "navigate_properties",
          "action_sequence": [
            {"step": 1, "action": "goto", "params": {"url": "#/properties"}}
          ],
          "confidence": 1.0
        }
        """

        # Parse cdigo para extrair actions
        code = teaching.get('code', '')
        actions = self._parse_code_to_actions(code)

        # Cria pattern name do task
        task = teaching.get('task', 'unknown')
        pattern_name = task.lower().replace(' ', '_').replace('-', '_')

        rl_pattern = {
            "pattern_name": pattern_name,
            "original_task": task,
            "action_sequence": actions,

            # Metadata do Claude
            "confidence": teaching.get('confidence', 1.0),
            "discovered_by": "claude",
            "timestamp": teaching.get('timestamp'),
            "reasoning": teaching.get('reasoning', ''),

            # Info adicional
            "tried_failed": teaching.get('tried_failed', []),
            "generalizable": teaching.get('generalizable', True),

            # RL metadata
            "total_executions": 0,  # Hunter ainda no usou
            "successful_executions": 0,
            "success_rate": 0.0,
            "avg_reward": 0.0,

            # Teaching origin
            "source": "claude_teaching",
            "validated_by_hunter": False
        }

        return rl_pattern

    def _parse_code_to_actions(self, code: str) -> List[Dict]:
        """
        Parse cdigo Python/Playwright para action sequence

        Input: "page.goto('#/properties')"
        Output: [{"step": 1, "action": "goto", "params": {"url": "#/properties"}}]
        """
        actions = []
        step_num = 1

        # Split por linhas se tiver mltiplas
        code_lines = [line.strip() for line in code.split('\n') if line.strip() and not line.strip().startswith('#')]

        for line in code_lines:
            # Tenta cada pattern
            for pattern, config in self.code_patterns.items():
                match = re.search(pattern, line)
                if match:
                    action = {
                        "step": step_num,
                        "action": config["action"],
                        "params": {},
                        "original_code": line
                    }

                    # Extrai parmetros do match
                    if config["action"] == "goto":
                        action["params"]["url"] = match.group(1)
                        action["selector"] = None

                    elif config["action"] == "click_testid":
                        action["params"]["testid"] = match.group(1)
                        action["selector"] = f'[data-testid="{match.group(1)}"]'

                    elif config["action"] == "click_role":
                        action["params"]["role"] = match.group(1)
                        action["params"]["name"] = match.group(2)
                        action["selector"] = f'role={match.group(1)} name={match.group(2)}'

                    elif config["action"] in ["fill", "select"]:
                        action["params"]["selector"] = match.group(1)
                        action["params"]["value"] = match.group(2) if len(match.groups()) > 1 else ""
                        action["selector"] = match.group(1)

                    elif config["action"] == "keyboard":
                        action["params"]["key"] = match.group(1)
                        action["selector"] = None

                    elif config["action"] == "wait":
                        action["params"]["ms"] = int(match.group(1))
                        action["selector"] = None

                    elif config["action"] == "select_testid":
                        action["params"]["testid"] = match.group(1)
                        action["params"]["value"] = match.group(2)
                        action["selector"] = f'[data-testid="{match.group(1)}"]'

                    elif config["action"] == "goto_hash":
                        action["params"]["base_var"] = match.group(1)
                        action["params"]["section"] = match.group(2)
                        action["selector"] = None

                    actions.append(action)
                    step_num += 1
                    break

        return actions

    def translate_all(self) -> Dict:
        """
        Traduz TODOS os Claude teachings para formato RL
        """
        if not self.teachings_file.exists():
            print("[WARN] No claude_teachings.json found")
            return {"patterns": {}}

        # Carrega teachings
        with open(self.teachings_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        teachings = data.get('teachings', [])
        print(f"\n[TRANSLATOR] Found {len(teachings)} Claude teachings to translate")

        # Traduz cada um
        rl_patterns = {}
        for teaching in teachings:
            rl_pattern = self.translate_teaching(teaching)
            pattern_name = rl_pattern['pattern_name']
            rl_patterns[pattern_name] = rl_pattern
            print(f"  [OK] Translated: {pattern_name} ({len(rl_pattern['action_sequence'])} actions)")

        # Estrutura final para RL
        rl_format = {
            "version": "1.0_from_claude",
            "translated_at": datetime.now().isoformat(),
            "total_patterns": len(rl_patterns),
            "patterns": rl_patterns,
            "meta": {
                "source": "claude_teachings.json",
                "translation_method": "code_parsing",
                "confidence_all": 1.0  # Claude validou todos!
            }
        }

        # Salva
        with open(self.translated_file, 'w', encoding='utf-8') as f:
            json.dump(rl_format, f, indent=2, ensure_ascii=False)

        print(f"\n[SAVE] Translated teachings saved: {self.translated_file}")
        print(f"[INFO] Hunter can now USE {len(rl_patterns)} Claude patterns directly!")

        return rl_format

    def merge_with_existing_patterns(self, patterns_file: str = "../barril!!/patterns_learned.json"):
        """
        Merge Claude teachings com patterns existentes do Hunter
        Claude teachings tm PRIORIDADE (confidence 1.0!)
        """
        patterns_path = Path(patterns_file)

        # Load existing
        if patterns_path.exists():
            with open(patterns_path, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        else:
            existing = {"patterns": {}}

        # Load translated Claude teachings
        translated = self.translate_all()

        # Merge (Claude tem prioridade!)
        merged = existing.copy()
        for pattern_name, claude_pattern in translated['patterns'].items():
            if pattern_name in merged['patterns']:
                print(f"[MERGE] Pattern '{pattern_name}' exists - Claude version takes priority!")
            merged['patterns'][pattern_name] = claude_pattern

        # Salva merged
        with open(patterns_path, 'w', encoding='utf-8') as f:
            json.dump(merged, f, indent=2, ensure_ascii=False)

        print(f"\n[MERGE] Patterns merged: {len(merged['patterns'])} total")
        print(f"   From Claude: {len(translated['patterns'])}")
        print(f"   From Hunter: {len(existing.get('patterns', {}))}")

        return merged


# DEMO
if __name__ == "__main__":
    print("\n" + "="*70)
    print("TEACHING TRANSLATOR - Demo")
    print("="*70)

    translator = TeachingTranslator()

    # Translate all
    result = translator.translate_all()

    print("\n" + "="*70)
    print("TRANSLATION COMPLETE!")
    print("="*70)

    # Show 1 example
    if result['patterns']:
        first_pattern = list(result['patterns'].values())[0]
        print(f"\nExample Pattern:")
        print(f"  Name: {first_pattern['pattern_name']}")
        print(f"  Actions: {len(first_pattern['action_sequence'])}")
        print(f"  Confidence: {first_pattern['confidence']}")
        print(f"\n  Action Sequence:")
        for action in first_pattern['action_sequence']:
            print(f"    Step {action['step']}: {action['action']} {action.get('params', {})}")

