"""
AGENT TEACHER - Captura aprendizado do agente AI e passa pro RL

Quando o agente AI (eu) trabalha no chat:
- Erra  Tenta corrigir  Aprende estratgia
- Descobre padro  Salva como sucesso
- Adapta cdigo  RL aprende a adaptar tambm
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from utils.success_logger import get_logger as get_success_logger
from utils.recovery_logger import get_logger as get_recovery_logger

class AgentTeacher:
    """
    Sistema que captura aprendizado do agente AI enquanto trabalha
    e disponibiliza para RL aprender
    """

    def __init__(self, knowledge_base: str = "../barril!!/agent_learning"):
        self.knowledge_base = Path(knowledge_base)
        self.knowledge_base.mkdir(parents=True, exist_ok=True)

        # Usa loggers existentes (unificao!)
        self.success_logger = get_success_logger()
        self.recovery_logger = get_recovery_logger()

        # Cache para consultas rpidas
        self.patterns_file = self.knowledge_base / "agent_patterns.json"
        self.patterns = self._load_json(self.patterns_file, {})

        # INTEGRATION: Tambm carrega patterns do sistema principal (incluindo Claude!)
        self.main_patterns_file = Path("../barril!!/patterns_learned.json")
        self.main_patterns = self._load_json(self.main_patterns_file, {"patterns": {}})

    def log_win(self,
                 action: str,
                 strategy: str,
                 context: Dict = None,
                 result: str = None):
        """Loga win do agente - usa success_logger existente"""
        pattern = f"{action}_{strategy}"
        self.success_logger.log_success(
            action=action,
            context=context or {"strategy": strategy, "source": "agent_ai"},
            pattern=pattern,
            confidence=1.0,
            notes=result or f"Agente AI descobriu: {strategy}"
        )

    def log_recovery(self,
                    error: str,
                    failed_attempts: List[Dict],
                    successful_attempt: Dict,
                    learned_strategy: str):
        """Loga recovery do agente - usa recovery_logger existente"""
        action = successful_attempt.get("action", "unknown")
        self.recovery_logger.start_recovery(action, {"source": "agent_ai", "error": error})

        for attempt in failed_attempts:
            self.recovery_logger.log_attempt(
                attempt_num=attempt.get("attempt", 1),
                what_tried=attempt.get("strategy", ""),
                result="failed",
                error=attempt.get("error"),
                adjustment=learned_strategy
            )

        self.recovery_logger.log_attempt(
            attempt_num=successful_attempt.get("attempt", len(failed_attempts) + 1),
            what_tried=successful_attempt.get("strategy", learned_strategy),
            result="success"
        )

        self.recovery_logger.finish_recovery(success=True)

    def log_pattern(self,
                   pattern_name: str,
                   description: str,
                   code_example: str,
                   when_to_use: str):
        """
        Loga padro que agente AI descobriu

        Exemplo:
        - Padro: "Staging usa input para state, no select"
        - Descrio: "Em staging, propertyAddress.state  input field"
        - Cdigo: "page.get_by_test_id('state').fill('SP')"
        - Quando usar: "Quando ENVIRONMENT == 'staging'"
        """
        pattern = {
            "timestamp": datetime.now().isoformat(),
            "name": pattern_name,
            "description": description,
            "code_example": code_example,
            "when_to_use": when_to_use,
            "confidence": 1.0,
            "source": "agent_ai_chat",
            "usage_count": 0
        }

        self.patterns[pattern_name] = pattern
        self._save_json(self.patterns_file, self.patterns)
        print(f"AGENT PATTERN LOGGED: {pattern_name}")

    def get_recovery_strategy_for_error(self, error: str) -> Optional[Dict]:
        """RL consulta: busca em recovery_logger existente"""
        patterns = self.recovery_logger.extract_recovery_patterns()
        error_lower = error.lower()

        for pattern in patterns:
            for strategy in pattern.get("recovery_strategy", []):
                if strategy.get("error") and error_lower in strategy["error"].lower():
                    return {
                        "strategy": strategy.get("adjustment", ""),
                        "confidence": 0.9,
                        "source": "agent_ai"
                    }
        return None

    def get_strategy_for_action(self, action: str) -> Optional[List[Dict]]:
        """RL consulta: busca em success_logger existente"""
        patterns = self.success_logger.get_patterns_for_rl()
        relevant = [p for p in patterns if p["action"] == action or action in p["action"]]
        return relevant or None

    def get_pattern_for_context(self, context: Dict) -> Optional[Dict]:
        """
        RL chama isso: "Tenho este contexto, qual padro aplicar?"
        Busca primeiro nos patterns do agente, depois nos patterns principais
        """
        # Primeiro tenta nos patterns do agente
        for pattern_name, pattern in self.patterns.items():
            when_to_use = pattern.get("when_to_use", "").lower()

            # Exemplo: se when_to_use menciona "staging" e context tem staging
            if any(key in when_to_use for key in context.keys()):
                return pattern

        # Se no encontrou, busca nos patterns principais (Claude + Hunter)
        main_patterns = self.main_patterns.get("patterns", {})
        for pattern_name, pattern in main_patterns.items():
            # Match por contexto ou por nome do pattern
            if any(key.lower() in pattern_name.lower() for key in context.keys()):
                return pattern

        return None

    def export_for_rl(self) -> Dict:
        """Exporta conhecimento unificado dos loggers E patterns principais"""
        return {
            "wins": self.success_logger.get_patterns_for_rl(),
            "recoveries": self.recovery_logger.extract_recovery_patterns(),
            "agent_patterns": self.patterns,
            "main_patterns": self.main_patterns.get("patterns", {}),
            "stats": {
                "total_wins": len(self.success_logger.get_patterns_for_rl()),
                "total_recoveries": len(self.recovery_logger.extract_recovery_patterns()),
                "total_agent_patterns": len(self.patterns),
                "total_main_patterns": len(self.main_patterns.get("patterns", {})),
                "last_updated": datetime.now().isoformat()
            }
        }

    def _load_json(self, filepath: Path, default):
        """Carrega JSON"""
        if filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return default
        return default



