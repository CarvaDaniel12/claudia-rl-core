"""
 AGENT TRAINING SUPERVISOR - Agente como Professor

O AGENTE (Copilot/Claude) supervisiona o treinamento:
1. Roda N runs
2. Analisa logs em TEMPO REAL
3. Identifica problemas
4. D feedback estruturado
5. Consolida conhecimento
6. Repete!

CICLO COMPLETO:

 FASE 1: 15 runs                                      
  Analisa resultados                                 
  D feedback: "Lead creation est lento"           
  Consolida: "Otimize seletor X"                    

 FASE 2: 20 runs                                      
  Analisa: "Lead creation melhorou!"                
  D feedback: "Property cleanup falhou 3x"         
  Consolida: "Use strategy Y para cleanup"          

 FASE 3: 30 runs                                      
  Analisa: "Cleanup resolvido!"                     
  D feedback: "Inbox exploration ausente"          
  Consolida: "Adicione Inbox ao golden path"        

 FASE 4: 40 runs                                      
  Analisa: "Sistema completo!"                      
  Feedback final: "95% success rate alcanado"      
  Consolida: MASTER KNOWLEDGE                       


USO:
    python agent_training_supervisor.py --cycles 4

    Vai rodar:
    - 15 runs  feedback  consolidao
    - 20 runs  feedback  consolidao
    - 30 runs  feedback  consolidao
    - 40 runs  feedback  consolidao

    Total: 105 runs com superviso ativa!
"""
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List


class AgentTrainingSupervisor:
    """
    Supervisor que OBSERVA o treinamento e D FEEDBACK

    Como um professor observando aluno:
    - Assiste execuo
    - Identifica pontos fracos
    - D conselhos especficos
    - Consolida aprendizado
    """

    def __init__(self):
        self.barril_path = Path("../barril!!")
        self.cycles_completed = []
        self.total_runs = 0

        print("\n" + "="*70)
        print(" AGENT TRAINING SUPERVISOR")
        print("="*70)
        print()
        print("Role: AI Agent as Teacher")
        print()
        print("Process:")
        print("  1. Run N training iterations")
        print("  2. Analyze logs and results")
        print("  3. Identify issues and wins")
        print("  4. Give structured feedback")
        print("  5. Consolidate knowledge")
        print("  6. REPEAT!")
        print()
        print("="*70)
        print()

    def supervise_training_cycles(self, run_counts: List[int]):
        """
        Supervisiona mltiplos ciclos de treinamento

        Args:
            run_counts: Lista com nmero de runs por ciclo
                       Ex: [15, 20, 30, 40]
        """
        print(f" Training Plan:")
        print(f"   Cycles: {len(run_counts)}")
        print(f"   Runs per cycle: {run_counts}")
        print(f"   Total runs: {sum(run_counts)}")
        print()

        input("Press ENTER to start supervised training...")
        print()

        for cycle_num, run_count in enumerate(run_counts, 1):
            print("\n" + "="*70)
            print(f" CYCLE {cycle_num}/{len(run_counts)}")
            print("="*70)
            print(f"   Runs: {run_count}")
            print()

            # 1. RUN TRAINING
            self._run_training_phase(run_count, cycle_num)

            # 2. ANALYZE RESULTS
            analysis = self._analyze_results(cycle_num)

            # 3. GIVE FEEDBACK
            feedback = self._give_feedback(analysis, cycle_num)

            # 4. CONSOLIDATE KNOWLEDGE
            self._consolidate_knowledge(feedback, cycle_num)

            # 5. SAVE CYCLE REPORT
            self._save_cycle_report(cycle_num, run_count, analysis, feedback)

            self.cycles_completed.append({
                'cycle': cycle_num,
                'runs': run_count,
                'analysis': analysis,
                'feedback': feedback
            })

            self.total_runs += run_count

            print("\n" + "="*70)
            print(f" CYCLE {cycle_num} COMPLETE!")
            print("="*70)
            print()

            if cycle_num < len(run_counts):
                print(f"Next cycle: {run_counts[cycle_num]} runs")
                print()
                time.sleep(2)

        self._print_final_summary()

    def _run_training_phase(self, run_count: int, cycle_num: int):
        """
        Executa fase de treinamento

        Roda train_ultimate.py e OBSERVA output em tempo real
        """
        print(f" Starting training: {run_count} runs...")
        print(f"   Timestamp: {datetime.now().strftime('%H:%M:%S')}")
        print()

        # Run training
        cmd = f"python train_ultimate.py --runs {run_count}"

        print(f" Running: {cmd}")
        print()
        print(""*70)

        # Execute and capture output
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        # Print output in real-time
        for line in process.stdout:
            print(line, end='')

        process.wait()

        print(""*70)
        print()

        if process.returncode == 0:
            print(f" Training phase completed successfully!")
        else:
            print(f" Training phase completed with errors (code {process.returncode})")

        print()

    def _analyze_results(self, cycle_num: int) -> Dict:
        """
        Analisa resultados do ciclo

        L arquivos gerados:
        - ultimate_report.json
        - experience_buffer.json
        - healing_memory.json
        - patterns_learned.json

        Returns anlise estruturada
        """
        print(f" Analyzing cycle {cycle_num} results...")
        print()

        analysis = {
            'timestamp': datetime.now().isoformat(),
            'cycle': cycle_num,
            'success_rate': 0.0,
            'avg_duration': 0.0,
            'total_reward': 0.0,
            'experience_count': 0,
            'healing_elements': 0,
            'patterns_count': 0,
            'issues_found': [],
            'wins': []
        }

        try:
            # Read ultimate_report.json
            report_path = self.barril_path / "ultimate_report.json"
            if report_path.exists():
                with open(report_path, 'r', encoding='utf-8') as f:
                    report = json.load(f)

                stats = report.get('stats', {})
                analysis['success_rate'] = stats.get('success_rate', 0.0)
                analysis['avg_duration'] = stats.get('avg_duration', 0.0)
                analysis['total_reward'] = stats.get('total_reward', 0.0)

                print(f"   Success Rate: {analysis['success_rate']:.1f}%")
                print(f"   Avg Duration: {analysis['avg_duration']:.1f}s")
                print(f"   Total Reward: {analysis['total_reward']:+.1f}")

            # Read experience_buffer.json
            exp_path = self.barril_path / "experience_buffer.json"
            if exp_path.exists():
                with open(exp_path, 'r', encoding='utf-8') as f:
                    experiences = json.load(f)
                analysis['experience_count'] = len(experiences)
                print(f"   Experience Buffer: {analysis['experience_count']} samples")

            # Read healing_memory.json
            healing_path = self.barril_path / "healing_memory.json"
            if healing_path.exists():
                with open(healing_path, 'r', encoding='utf-8') as f:
                    healing = json.load(f)
                analysis['healing_elements'] = len(healing.get('selectors', {}))
                print(f"   Healing Elements: {analysis['healing_elements']}")

            # Read patterns_learned.json
            patterns_path = Path("patterns_learned.json")
            if patterns_path.exists():
                with open(patterns_path, 'r', encoding='utf-8') as f:
                    patterns = json.load(f)
                analysis['patterns_count'] = len(patterns.get('patterns', {}))
                print(f"   Patterns Learned: {analysis['patterns_count']}")

        except Exception as e:
            print(f"    Analysis error: {e}")

        print()
        return analysis

    def _give_feedback(self, analysis: Dict, cycle_num: int) -> Dict:
        """
         D FEEDBACK baseado na anlise

        Como um professor:
        - Identifica o que est indo bem
        - Identifica o que precisa melhorar
        - D conselhos especficos e acionveis

        Returns feedback estruturado
        """
        print(f" Generating feedback for cycle {cycle_num}...")
        print()

        feedback = {
            'cycle': cycle_num,
            'timestamp': datetime.now().isoformat(),
            'wins': [],
            'issues': [],
            'recommendations': [],
            'priorities': []
        }

        # Analyze success rate
        success_rate = analysis['success_rate']

        if success_rate >= 90:
            feedback['wins'].append({
                'area': 'Overall Performance',
                'message': f'Excellent success rate: {success_rate:.1f}%',
                'impact': 'high'
            })
        elif success_rate >= 70:
            feedback['wins'].append({
                'area': 'Overall Performance',
                'message': f'Good success rate: {success_rate:.1f}%',
                'impact': 'medium'
            })
        else:
            feedback['issues'].append({
                'area': 'Overall Performance',
                'message': f'Low success rate: {success_rate:.1f}%',
                'severity': 'high'
            })
            feedback['recommendations'].append({
                'area': 'Stability',
                'action': 'Review error logs to identify most common failures',
                'priority': 'high'
            })

        # Analyze experience growth
        exp_count = analysis['experience_count']
        if cycle_num == 1:
            if exp_count > 85:
                feedback['wins'].append({
                    'area': 'Learning',
                    'message': f'Good experience accumulation: {exp_count} samples',
                    'impact': 'medium'
                })
        else:
            # Compare with previous cycle
            prev_cycle = self.cycles_completed[-1] if self.cycles_completed else None
            if prev_cycle:
                prev_exp = prev_cycle['analysis']['experience_count']
                growth = exp_count - prev_exp
                if growth > 0:
                    feedback['wins'].append({
                        'area': 'Learning',
                        'message': f'Experience buffer growing: +{growth} samples',
                        'impact': 'medium'
                    })
                else:
                    feedback['issues'].append({
                        'area': 'Learning',
                        'message': 'Experience buffer not growing',
                        'severity': 'medium'
                    })
                    feedback['recommendations'].append({
                        'area': 'Experience Replay',
                        'action': 'Ensure new experiences are being saved correctly',
                        'priority': 'medium'
                    })

        # Analyze healing memory
        healing_count = analysis['healing_elements']
        if healing_count >= 10:
            feedback['wins'].append({
                'area': 'Self-Healing',
                'message': f'Strong self-healing: {healing_count} elements',
                'impact': 'high'
            })
        elif healing_count >= 6:
            feedback['wins'].append({
                'area': 'Self-Healing',
                'message': f'Good self-healing: {healing_count} elements',
                'impact': 'medium'
            })
        else:
            feedback['recommendations'].append({
                'area': 'Self-Healing',
                'action': f'Expand healing memory (currently {healing_count} elements)',
                'priority': 'low'
            })

        # Analyze patterns
        patterns_count = analysis['patterns_count']
        if patterns_count >= 50:
            feedback['wins'].append({
                'area': 'Pattern Recognition',
                'message': f'Rich pattern library: {patterns_count} patterns',
                'impact': 'high'
            })
        else:
            feedback['recommendations'].append({
                'area': 'Pattern Learning',
                'action': f'Continue learning patterns (currently {patterns_count})',
                'priority': 'low'
            })

        # Set priorities for next cycle
        if success_rate < 80:
            feedback['priorities'].append('Improve stability and success rate')
        if exp_count < 100:
            feedback['priorities'].append('Accumulate more experience samples')
        if healing_count < 10:
            feedback['priorities'].append('Expand self-healing coverage')

        # Print feedback
        self._print_feedback(feedback)

        return feedback

    def _print_feedback(self, feedback: Dict):
        """Print feedback in readable format"""
        print(" FEEDBACK SUMMARY:")
        print()

        if feedback['wins']:
            print(" WINS:")
            for win in feedback['wins']:
                print(f"    {win['area']}: {win['message']}")
            print()

        if feedback['issues']:
            print(" ISSUES:")
            for issue in feedback['issues']:
                print(f"    {issue['area']}: {issue['message']}")
            print()

        if feedback['recommendations']:
            print(" RECOMMENDATIONS:")
            for rec in feedback['recommendations']:
                print(f"    {rec['area']}: {rec['action']} [Priority: {rec['priority']}]")
            print()

        if feedback['priorities']:
            print(" PRIORITIES FOR NEXT CYCLE:")
            for priority in feedback['priorities']:
                print(f"    {priority}")
            print()

    def _consolidate_knowledge(self, feedback: Dict, cycle_num: int):
        """
        Consolida conhecimento aps ciclo

        Cria arquivo de "teachings" do agente para o Hunter
        """
        print(f" Consolidating knowledge from cycle {cycle_num}...")
        print()

        # Create teaching file
        teaching = {
            'cycle': cycle_num,
            'timestamp': datetime.now().isoformat(),
            'feedback': feedback,
            'lessons': []
        }

        # Extract lessons from feedback
        for win in feedback.get('wins', []):
            teaching['lessons'].append({
                'type': 'success_pattern',
                'area': win['area'],
                'lesson': win['message'],
                'apply': 'Continue this approach'
            })

        for rec in feedback.get('recommendations', []):
            teaching['lessons'].append({
                'type': 'improvement',
                'area': rec['area'],
                'lesson': rec['action'],
                'apply': f"Priority: {rec['priority']}"
            })

        # Save teaching
        teaching_path = self.barril_path / f"agent_teaching_cycle_{cycle_num}.json"
        with open(teaching_path, 'w', encoding='utf-8') as f:
            json.dump(teaching, f, indent=2, ensure_ascii=False)

        print(f"    Teaching saved: {teaching_path.name}")
        print(f"   Lessons: {len(teaching['lessons'])}")
        print()

    def _save_cycle_report(self, cycle_num: int, run_count: int,
                          analysis: Dict, feedback: Dict):
        """Save detailed cycle report"""
        report = {
            'cycle': cycle_num,
            'runs': run_count,
            'timestamp': datetime.now().isoformat(),
            'analysis': analysis,
            'feedback': feedback
        }

        report_path = self.barril_path / f"supervised_cycle_{cycle_num}_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f" Cycle report saved: {report_path.name}")
        print()

    def _print_final_summary(self):
        """Print final summary of all cycles"""
        print("\n" + "="*70)
        print(" SUPERVISED TRAINING COMPLETE!")
        print("="*70)
        print()

        print(f" OVERALL STATS:")
        print(f"   Total Cycles: {len(self.cycles_completed)}")
        print(f"   Total Runs: {self.total_runs}")
        print()

        print(" CYCLE PROGRESSION:")
        for cycle in self.cycles_completed:
            analysis = cycle['analysis']
            print(f"   Cycle {cycle['cycle']}: {cycle['runs']} runs - "
                  f"Success: {analysis['success_rate']:.1f}% - "
                  f"Exp: {analysis['experience_count']} - "
                  f"Healing: {analysis['healing_elements']}")
        print()

        # Final recommendations
        last_cycle = self.cycles_completed[-1]
        last_feedback = last_cycle['feedback']

        if last_feedback.get('priorities'):
            print(" FINAL RECOMMENDATIONS:")
            for priority in last_feedback['priorities']:
                print(f"    {priority}")
            print()

        print("="*70)
        print()

        # Save master summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_cycles': len(self.cycles_completed),
            'total_runs': self.total_runs,
            'cycles': self.cycles_completed
        }

        summary_path = self.barril_path / "supervised_training_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f" Master summary saved: {summary_path.name}")
        print()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Agent Training Supervisor - AI as Teacher"
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=4,
        help="Number of training cycles (default: 4)"
    )
    parser.add_argument(
        "--runs",
        type=str,
        default="15,20,30,40",
        help="Runs per cycle, comma-separated (default: 15,20,30,40)"
    )

    args = parser.parse_args()

    # Parse run counts
    run_counts = [int(x.strip()) for x in args.runs.split(',')]

    if len(run_counts) != args.cycles:
        print(f"Error: --runs must have {args.cycles} values (one per cycle)")
        return

    # Start supervision
    supervisor = AgentTrainingSupervisor()
    supervisor.supervise_training_cycles(run_counts)


if __name__ == "__main__":
    main()
