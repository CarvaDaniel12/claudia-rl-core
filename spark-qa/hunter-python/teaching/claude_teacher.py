"""
CLAUDE TEACHER - Wrapper simples do AgentTeacher para EU usar durante exploration

USO: Quando EU exploro e descubro algo, logo aqui!
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from teaching.agent_teacher import AgentTeacher
import json
from datetime import datetime

class ClaudeTeacher:
    """
    Wrapper simples para EU (Claude) documentar descobertas durante exploration
    Salva em formato otimizado para Hunter (RLAIF - RL from AI Feedback)
    """

    def __init__(self):
        self.agent = AgentTeacher()
        self.teachings_file = Path("../barril!!/claude_teachings.json")
        self.teachings = self._load_teachings()

    def _load_teachings(self):
        """Carrega teachings existentes"""
        if self.teachings_file.exists():
            with open(self.teachings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "version": "1.0_rlaif",
            "created": datetime.now().isoformat(),
            "total_teachings": 0,
            "teachings": []
        }

    def teach(self,
              task: str,
              tried_failed: list,
              working_solution: str,
              code: str,
              reasoning: str,
              generalizable: bool = True):
        """
        EU chamo isso quando descubro algo durante exploration!

        Exemplo:
        claude.teach(
            task="Open lead modal",
            tried_failed=["menu click", "search button"],
            working_solution="addLeadButton",
            code="page.get_by_test_id('addLeadButton').click()",
            reasoning="Button is in top menu, always visible",
            generalizable=True
        )
        """

        teaching = {
            "id": f"teaching_{len(self.teachings['teachings']) + 1}",
            "timestamp": datetime.now().isoformat(),
            "discovered_by": "claude",

            # O que tentei
            "task": task,
            "tried_failed": tried_failed,

            # O que funcionou!
            "working_solution": working_solution,
            "code": code,
            "reasoning": reasoning,

            # Meta info
            "confidence": 1.0,  # Eu valdei manualmente!
            "generalizable": generalizable,
            "usage_count": 0,
            "validated_by_hunter": False
        }

        # Salva teaching
        self.teachings['teachings'].append(teaching)
        self.teachings['total_teachings'] = len(self.teachings['teachings'])
        self._save_teachings()

        # TAMBM loga no agent_teacher (integrao!)
        self.agent.log_recovery(
            error=f"Failed attempts: {', '.join(tried_failed)}",
            failed_attempts=[{"strategy": s, "error": "failed"} for s in tried_failed],
            successful_attempt={"strategy": working_solution, "action": task},
            learned_strategy=reasoning
        )

        print(f"\n[TEACHING LOGGED] {task}")
        print(f"  Failed: {', '.join(tried_failed)}")
        print(f"  Works: {working_solution}")
        print(f"  Saved to: {self.teachings_file}")
        print(f"  Total teachings: {self.teachings['total_teachings']}\n")

    def quick_success(self, task: str, solution: str, code: str):
        """Atalho para sucessos diretos (sem falhas antes)"""
        self.teach(
            task=task,
            tried_failed=[],
            working_solution=solution,
            code=code,
            reasoning=f"{solution} works directly",
            generalizable=True
        )

    def _save_teachings(self):
        """Salva teachings"""
        with open(self.teachings_file, 'w', encoding='utf-8') as f:
            json.dump(self.teachings, f, indent=2, ensure_ascii=False)

    def get_all_teachings(self):
        """Hunter chama isso para carregar meus teachings"""
        return self.teachings['teachings']

    def get_teaching_by_task(self, task: str):
        """Busca teaching por task"""
        for t in self.teachings['teachings']:
            if task.lower() in t['task'].lower():
                return t
        return None


# DEMO / TESTE
if __name__ == "__main__":
    print("\n" + "="*70)
    print("CLAUDE TEACHER - Demo")
    print("="*70)

    teacher = ClaudeTeacher()

    # Exemplo 1: Descoberta com falhas antes
    print("\nExample 1: Discovery with failed attempts")
    teacher.teach(
        task="Navigate to properties",
        tried_failed=["menu click (timeout)", "role link (invisible)"],
        working_solution="URL navigation",
        code="page.goto(base_url + '#/properties')",
        reasoning="Menu becomes invisible after agency selection",
        generalizable=True
    )

    # Exemplo 2: Sucesso direto
    print("\nExample 2: Direct success")
    teacher.quick_success(
        task="Click add property button",
        solution="get_by_test_id",
        code="page.get_by_test_id('add-property-button').click()"
    )

    # Ver todos teachings
    print("\n" + "="*70)
    print(f"Total teachings: {len(teacher.get_all_teachings())}")
    print("="*70)

    # Export para Hunter
    teachings = teacher.get_all_teachings()
    print(f"\nHunter can now learn from {len(teachings)} Claude teachings!")
    print(f"File: {teacher.teachings_file}")

