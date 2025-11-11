"""
 FAST LEARNER - Aprendizado acelerado com tcnicas inteligentes

TCNICAS USADAS (simples mas efetivas):
1.  Experience Replay (aprende com runs passados)
2.  Transfer Learning (patterns de flows similares)
3.  Bayesian Optimization (explora melhor)
4.  Pattern Evolution (combina patterns que funcionam)
5.  Meta-Learning (aprende a aprender)

SEM PRECISAR: PyTorch, GPU, milhares de samples!
COM: Numpy, estatstica inteligente, heursticas
"""
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
from collections import defaultdict

class FastLearner:
    """
    Aprende RPIDO usando tcnicas inteligentes sem deep learning
    """
    
    def __init__(self, patterns_file: str = "barril!!/patterns_learned.json"):
        self.patterns_file = Path(patterns_file)
        self.patterns = self._load_patterns()
        
        # Experience Replay Buffer
        self.experience_buffer = []
        self.max_buffer_size = 1000
        
        # PRIORITIZED EXPERIENCE REPLAY (NEW)
        # Experiences with high TD-error (prediction error) get sampled more
        self.experience_priorities = {}  # experience_id -> priority (TD-error)
        self.alpha_priority = 0.6  # How much to use prioritization (0=uniform, 1=full priority)
        self.beta_importance = 0.4  # Importance sampling correction
        
        # CRITICAL: Load previous experiences!
        self._load_experience_buffer()
        
        # Meta-learning stats
        self.meta_stats = {
            "success_patterns": [],
            "failure_patterns": [],
            "timing_data": defaultdict(list),
            "selector_reliability": defaultdict(lambda: {"success": 0, "fail": 0})
        }
    
    def _load_patterns(self) -> Dict:
        """Carrega patterns"""
        if self.patterns_file.exists():
            with open(self.patterns_file, 'r') as f:
                return json.load(f)
        return {"patterns": {}}
    
    def _load_experience_buffer(self):
        """Carrega experience buffer de runs anteriores"""
        buffer_file = Path("../barril!!/experience_buffer.json")
        if buffer_file.exists():
            try:
                with open(buffer_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.experience_buffer = data.get('experiences', [])
                    print(f"[FastLearner] Loaded {len(self.experience_buffer)} experiences from previous runs!")
            except Exception as e:
                print(f"[FastLearner] Could not load experience buffer: {e}")
                self.experience_buffer = []
        else:
            print(f"[FastLearner] No previous experience buffer found (starting fresh)")
    
    def sample_prioritized_batch(self, batch_size: int = 32) -> List[Dict]:
        """
        Sample batch with prioritization (high TD-error experiences more likely)
        
        Returns:
            List of experiences sampled according to priority
        """
        if not self.experience_buffer:
            return []
        
        # Get priorities for all experiences
        priorities = []
        valid_experiences = []
        
        for exp in self.experience_buffer:
            exp_id = exp.get("id", "")
            if exp_id in self.experience_priorities:
                priorities.append(self.experience_priorities[exp_id])
                valid_experiences.append(exp)
        
        if not priorities:
            # Fallback to random sampling if no priorities
            import random
            return random.sample(self.experience_buffer, min(batch_size, len(self.experience_buffer)))
        
        # Convert priorities to sampling probabilities
        # P(i) = priority(i)^alpha / sum(priority(j)^alpha)
        import numpy as np
        priorities_array = np.array(priorities)
        priorities_alpha = priorities_array ** self.alpha_priority
        probs = priorities_alpha / priorities_alpha.sum()
        
        # Sample according to probabilities
        batch_size = min(batch_size, len(valid_experiences))
        indices = np.random.choice(len(valid_experiences), size=batch_size, replace=False, p=probs)
        
        sampled = [valid_experiences[i] for i in indices]
        
        return sampled
    
    def save_experience_buffer(self):
        """Salva experience buffer em disco (CRITICAL for learning persistence!)"""
        buffer_file = Path("../barril!!/experience_buffer.json")
        
        data = {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "total_experiences": len(self.experience_buffer),
            "experiences": self.experience_buffer
        }
        
        try:
            with open(buffer_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[FastLearner]  Saved {len(self.experience_buffer)} experiences to {buffer_file}")
            return True
        except Exception as e:
            print(f"[FastLearner]  Failed to save experience buffer: {e}")
            return False
    
    def add_experience(
        self,
        flow_name: str,
        actions: List[Dict],
        success: bool,
        duration: float,
        context: Dict = None,
        td_error: float = None
    ):
        """
        Adiciona experincia ao buffer (Prioritized Experience Replay)
        
        Args:
            td_error: Temporal Difference error (prediction error)
                     High TD-error = more to learn from this experience
        """
        experience = {
            "id": f"{flow_name}_{datetime.now().timestamp()}",
            "timestamp": datetime.now().isoformat(),
            "flow_name": flow_name,
            "actions": actions,
            "success": success,
            "duration": duration,
            "context": context or {}
        }
        
        self.experience_buffer.append(experience)
        
        # PRIORITIZED REPLAY: Assign priority based on TD-error
        # If no TD-error provided, use success as proxy (failures more important)
        if td_error is not None:
            priority = abs(td_error) + 0.01  # Small epsilon to avoid 0
        else:
            # Heuristic: failures have higher priority (more to learn)
            priority = 0.5 if success else 1.0
        
        self.experience_priorities[experience["id"]] = priority
        
        # Limita tamanho do buffer (keep most recent)
        if len(self.experience_buffer) > self.max_buffer_size:
            removed = self.experience_buffer.pop(0)
            # Remove priority too
            if removed.get("id") in self.experience_priorities:
                del self.experience_priorities[removed["id"]]
        
        # Atualiza meta-stats
        self._update_meta_stats(experience)
    
    def _update_meta_stats(self, experience: Dict):
        """Atualiza estatsticas meta (aprende sobre o aprendizado)"""
        flow_name = experience['flow_name']
        
        # Registra padres de sucesso/falha
        if experience['success']:
            self.meta_stats['success_patterns'].append({
                "flow": flow_name,
                "duration": experience['duration'],
                "num_actions": len(experience['actions'])
            })
        else:
            self.meta_stats['failure_patterns'].append({
                "flow": flow_name,
                "duration": experience['duration']
            })
        
        # Timing data
        self.meta_stats['timing_data'][flow_name].append(experience['duration'])
        
        # Selector reliability
        for action in experience['actions']:
            selector = action.get('selector')
            if selector:
                if experience['success']:
                    self.meta_stats['selector_reliability'][selector]['success'] += 1
                else:
                    self.meta_stats['selector_reliability'][selector]['fail'] += 1
    
    def suggest_next_action(
        self,
        current_state: str,
        available_actions: List[str],
        use_prioritized: bool = True
    ) -> Tuple[str, float]:
        """
        Sugere prxima ao usando experincias passadas (PRIORITIZED REPLAY)
        
        Args:
            use_prioritized: If True, samples high-priority experiences more
        
        Returns: (action, confidence)
        """
        # 1. Sample experiences (prioritized if enabled)
        if use_prioritized and len(self.experience_priorities) > 0:
            # Use prioritized sampling (high TD-error first)
            sample_size = min(100, len(self.experience_buffer))
            sampled_experiences = self.sample_prioritized_batch(sample_size)
        else:
            # Use all experiences
            sampled_experiences = self.experience_buffer
        
        # 2. Checa sampled experiences
        action_scores = defaultdict(lambda: {"success": 0, "fail": 0, "avg_time": 0})
        
        for exp in sampled_experiences:
            if exp['success']:
                for action in exp['actions']:
                    action_name = action.get('action', '')
                    if action_name in available_actions:
                        action_scores[action_name]['success'] += 1
        
        # 2. Calcula scores (Bayesian-inspired)
        best_action = None
        best_score = -1
        
        for action in available_actions:
            scores = action_scores[action]
            total = scores['success'] + scores['fail'] + 1  # +1 para evitar div by zero
            
            # Beta distribution (Bayesian)
            # Mais confivel com mais amostras
            success_rate = (scores['success'] + 1) / (total + 2)
            confidence = min(1.0, total / 10)  # Mais amostras = mais confiana
            
            score = success_rate * confidence
            
            if score > best_score:
                best_score = score
                best_action = action
        
        # Se no tem dados, retorna aleatrio
        if best_action is None:
            best_action = available_actions[0] if available_actions else "unknown"
            best_score = 0.5
        
        return best_action, best_score
    
    def transfer_learning(self, source_flow: str, target_flow: str) -> Dict:
        """
        Transfer Learning: Usa conhecimento de flow similar
        """
        print(f"\n Transfer Learning: {source_flow}  {target_flow}")
        
        # Acha experincias do source flow
        source_experiences = [
            exp for exp in self.experience_buffer
            if exp['flow_name'] == source_flow and exp['success']
        ]
        
        if not source_experiences:
            print(f"     No successful experiences from {source_flow}")
            return {}
        
        # Extrai patterns comuns
        common_actions = defaultdict(int)
        for exp in source_experiences:
            for action in exp['actions']:
                action_name = action.get('action', '')
                common_actions[action_name] += 1
        
        # Cria pattern sugerido para target
        suggested_pattern = {
            "flow_name": target_flow,
            "confidence": 0.6,  # Comea com 60% (transferred knowledge)
            "actions": [
                {"action": action, "frequency": count}
                for action, count in sorted(
                    common_actions.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
            ],
            "transferred_from": source_flow,
            "source_samples": len(source_experiences)
        }
        
        print(f"    Transferred {len(suggested_pattern['actions'])} action patterns")
        print(f"    Based on {len(source_experiences)} successful runs")
        
        return suggested_pattern
    
    def evolve_patterns(self) -> List[Dict]:
        """
        Pattern Evolution: Combina patterns que funcionam bem
        """
        print("\n Evolving patterns...")
        
        # Separa experincias bem-sucedidas
        successful = [exp for exp in self.experience_buffer if exp['success']]
        
        if len(successful) < 2:
            print("     Need at least 2 successful runs to evolve")
            return []
        
        # Agrupa por flow
        by_flow = defaultdict(list)
        for exp in successful:
            by_flow[exp['flow_name']].append(exp)
        
        evolved_patterns = []
        
        for flow_name, experiences in by_flow.items():
            if len(experiences) < 2:
                continue
            
            # Encontra "genes" comuns (aes que aparecem em todos)
            common_genes = self._find_common_actions(experiences)
            
            # Encontra "genes" vencedores (correlacionados com sucesso rpido)
            winner_genes = self._find_winner_actions(experiences)
            
            # Combina
            evolved_pattern = {
                "flow_name": flow_name,
                "confidence": 0.8,  # Alta confiana (baseado em mltiplos sucessos)
                "common_actions": common_genes,
                "optimized_actions": winner_genes,
                "evolved_from": len(experiences),
                "avg_duration": np.mean([e['duration'] for e in experiences])
            }
            
            evolved_patterns.append(evolved_pattern)
            
            print(f"    {flow_name}: Evolved from {len(experiences)} runs")
        
        return evolved_patterns
    
    def _find_common_actions(self, experiences: List[Dict]) -> List[str]:
        """Encontra aes que aparecem em TODAS experincias"""
        if not experiences:
            return []
        
        # Pega aes do primeiro
        first_actions = set(a.get('action', '') for a in experiences[0]['actions'])
        
        # Interseco com todos outros
        for exp in experiences[1:]:
            exp_actions = set(a.get('action', '') for a in exp['actions'])
            first_actions &= exp_actions
        
        return list(first_actions)
    
    def _find_winner_actions(self, experiences: List[Dict]) -> List[Dict]:
        """Encontra aes correlacionadas com sucesso RPIDO"""
        # Ordena por durao (mais rpido = melhor)
        sorted_exp = sorted(experiences, key=lambda x: x['duration'])
        
        # Pega top 30%
        top_30_percent = max(1, len(sorted_exp) // 3)
        winners = sorted_exp[:top_30_percent]
        
        # Conta aes nos winners
        action_counts = defaultdict(int)
        for exp in winners:
            for action in exp['actions']:
                action_name = action.get('action', '')
                if action_name:
                    action_counts[action_name] += 1
        
        # Retorna aes mais frequentes nos winners
        return [
            {"action": action, "win_rate": count / len(winners)}
            for action, count in sorted(
                action_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )
        ]
    
    def meta_learn(self) -> Dict:
        """
        Meta-Learning: Aprende SOBRE o aprendizado
        
        Responde perguntas tipo:
        - Que tipo de aes geralmente falham?
        - Quanto tempo geralmente leva?
        - Quais seletores so mais confiveis?
        """
        print("\n Meta-Learning Analysis...")
        
        insights = {
            "most_reliable_selectors": [],
            "common_failure_points": [],
            "optimal_timing": {},
            "success_factors": []
        }
        
        # 1. Seletores mais confiveis
        for selector, stats in self.meta_stats['selector_reliability'].items():
            total = stats['success'] + stats['fail']
            if total >= 3:  # Pelo menos 3 usos
                reliability = stats['success'] / total
                if reliability >= 0.8:
                    insights['most_reliable_selectors'].append({
                        "selector": selector,
                        "reliability": reliability,
                        "samples": total
                    })
        
        # 2. Timing timo por flow
        for flow, times in self.meta_stats['timing_data'].items():
            if len(times) >= 3:
                insights['optimal_timing'][flow] = {
                    "median": float(np.median(times)),
                    "best": float(np.min(times)),
                    "std": float(np.std(times))
                }
        
        # 3. Fatores de sucesso
        if self.meta_stats['success_patterns']:
            avg_success_duration = np.mean([
                p['duration'] for p in self.meta_stats['success_patterns']
            ])
            avg_success_actions = np.mean([
                p['num_actions'] for p in self.meta_stats['success_patterns']
            ])
            
            insights['success_factors'] = {
                "avg_duration": float(avg_success_duration),
                "avg_actions": float(avg_success_actions),
                "sample_size": len(self.meta_stats['success_patterns'])
            }
        
        print(f"    Found {len(insights['most_reliable_selectors'])} reliable selectors")
        print(f"     Timing data for {len(insights['optimal_timing'])} flows")
        print(f"    Success patterns: {len(self.meta_stats['success_patterns'])} samples")
        
        return insights
    
    def get_learning_boost_report(self) -> str:
        """Gera report de quanto o sistema est aprendendo"""
        report = []
        report.append("\n" + ""*35)
        report.append("FAST LEARNER - Boost Report")
        report.append(""*35 + "\n")
        
        report.append(f" Experience Buffer: {len(self.experience_buffer)} samples")
        
        success_count = sum(1 for e in self.experience_buffer if e['success'])
        if self.experience_buffer:
            success_rate = (success_count / len(self.experience_buffer)) * 100
            report.append(f" Success Rate: {success_rate:.1f}%")
        
        report.append(f"\n Meta-Learning:")
        report.append(f"    Reliable selectors found: {len([s for s in self.meta_stats['selector_reliability'].values() if s['success'] > s['fail']])}")
        report.append(f"    Flows with timing data: {len(self.meta_stats['timing_data'])}")
        
        report.append("\n" + "="*70)
        
        return "\n".join(report)


# Demo
if __name__ == "__main__":
    print(" FAST LEARNER DEMO\n")
    
    learner = FastLearner()
    
    # Simula algumas experincias
    learner.add_experience(
        "PropertyCreation",
        [{"action": "login"}, {"action": "navigate"}, {"action": "fill_form"}],
        success=True,
        duration=27.5
    )
    
    learner.add_experience(
        "PropertyCreation",
        [{"action": "login"}, {"action": "navigate"}, {"action": "fill_form"}],
        success=True,
        duration=25.2
    )
    
    # Sugere ao
    next_action, confidence = learner.suggest_next_action(
        "after_login",
        ["navigate", "logout", "search"]
    )
    
    print(f"Suggested action: {next_action} (confidence: {confidence:.0%})")
    
    # Meta-learning
    insights = learner.meta_learn()
    
    # Report
    print(learner.get_learning_boost_report())

