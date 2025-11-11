#!/usr/bin/env python3
"""
Regenerate Teaching Files with Corrected Metrics
================================================

This script regenerates agent_teaching_cycle_N.json files with CORRECT metrics
after fixing the bug that read success_rate from wrong JSON path.

Bug fixed: Was reading report['success_rate'] (doesn't exist)
Now reads: report['stats']['successful_runs'] / report['stats']['total_runs']
"""

import json
from pathlib import Path
from datetime import datetime


def analyze_cycle_corrected(cycle_num: int) -> dict:
    """Analyze cycle with CORRECTED metrics"""
    barril_path = Path("../barril!!")

    analysis = {
        'cycle': cycle_num,
        'timestamp': datetime.now().isoformat(),
        'success_rate': 0.0,
        'total_reward': 0.0,
        'experience_count': 0,
        'healing_elements': 0,
        'patterns_count': 0
    }

    # Read ultimate_report.json (from cycle checkpoint if available)
    checkpoint_path = barril_path / f"checkpoint_ultimate_{cycle_num * 10}.json"
    if checkpoint_path.exists():
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
    else:
        report_path = barril_path / "ultimate_report.json"
        if report_path.exists():
            with open(report_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
        else:
            return analysis

    # CORRECTED: Calculate success_rate from stats
    stats = report.get('stats', {})
    total_runs = stats.get('total_runs', 0)
    successful_runs = stats.get('successful_runs', 0)
    failed_runs = stats.get('failed_runs', 0)

    if total_runs > 0:
        analysis['success_rate'] = (successful_runs / total_runs) * 100
    else:
        analysis['success_rate'] = 0.0

    analysis['total_runs'] = total_runs
    analysis['successful_runs'] = successful_runs
    analysis['failed_runs'] = failed_runs
    analysis['total_reward'] = stats.get('total_reward', 0.0)

    # Read experience_buffer.json
    exp_path = barril_path / "experience_buffer.json"
    if exp_path.exists():
        with open(exp_path, 'r', encoding='utf-8') as f:
            experiences = json.load(f)
        analysis['experience_count'] = len(experiences)

    # Read healing_memory.json
    healing_path = barril_path / "healing_memory.json"
    if healing_path.exists():
        with open(healing_path, 'r', encoding='utf-8') as f:
            healing = json.load(f)
        analysis['healing_elements'] = len(healing.get('selectors', {}))

    # Read patterns_learned.json
    patterns_path = barril_path / "patterns_learned.json"
    if patterns_path.exists():
        with open(patterns_path, 'r', encoding='utf-8') as f:
            patterns = json.load(f)
        analysis['patterns_count'] = len(patterns.get('patterns', {}))

    return analysis


def generate_corrected_feedback(analysis: dict, cycle_num: int) -> dict:
    """Generate CORRECTED feedback"""
    feedback = {
        'cycle': cycle_num,
        'timestamp': datetime.now().isoformat(),
        'wins': [],
        'issues': [],
        'recommendations': [],
        'corrected': True,  # Flag to indicate this is corrected data
        'original_bug': 'Was reading success_rate from wrong JSON path'
    }

    success_rate = analysis['success_rate']
    total_runs = analysis.get('total_runs', 0)
    successful_runs = analysis.get('successful_runs', 0)
    failed_runs = analysis.get('failed_runs', 0)

    # Analyze success rate (CORRECTED)
    if success_rate >= 95:
        feedback['wins'].append({
            'area': 'Stability',
            'message': f'EXCELLENT success rate: {success_rate:.1f}% ({successful_runs}/{total_runs})',
            'evidence': f'{successful_runs} successful runs out of {total_runs} total'
        })
    elif success_rate >= 80:
        feedback['wins'].append({
            'area': 'Stability',
            'message': f'Good success rate: {success_rate:.1f}% ({successful_runs}/{total_runs})',
            'evidence': f'{successful_runs} successful runs, {failed_runs} failures'
        })
    elif success_rate >= 60:
        feedback['issues'].append({
            'area': 'Stability',
            'message': f'Moderate success rate: {success_rate:.1f}% ({successful_runs}/{total_runs})',
            'severity': 'medium'
        })
    else:
        feedback['issues'].append({
            'area': 'Stability',
            'message': f'Low success rate: {success_rate:.1f}% ({successful_runs}/{total_runs})',
            'severity': 'high'
        })

    # Check performance consistency
    if 'meta_insights' in analysis and 'optimal_timing' in analysis.get('meta_insights', {}):
        timing = analysis['meta_insights']['optimal_timing']
        if 'std_dev' in timing:
            std_dev = timing['std_dev']
            if std_dev < 5.0:
                feedback['wins'].append({
                    'area': 'Performance',
                    'message': f'Very stable performance (std dev: {std_dev:.2f}s)',
                    'evidence': 'Low variance indicates consistent execution'
                })

    # Generate recommendations
    if success_rate >= 90:
        feedback['recommendations'].append({
            'priority': 'low',
            'action': 'Continue current approach - system is performing excellently'
        })
    elif success_rate >= 70:
        feedback['recommendations'].append({
            'priority': 'medium',
            'action': 'Review failed runs to identify common failure patterns'
        })
    else:
        feedback['recommendations'].append({
            'priority': 'high',
            'action': 'Investigate root causes of failures - success rate needs improvement'
        })

    # Learning progress
    exp_count = analysis.get('experience_count', 0)
    patterns_count = analysis.get('patterns_count', 0)
    healing_count = analysis.get('healing_elements', 0)

    if exp_count > 0:
        feedback['wins'].append({
            'area': 'Learning',
            'message': f'Experience buffer growing: {exp_count} samples',
            'evidence': 'System is accumulating execution experience'
        })

    if patterns_count > 0:
        feedback['wins'].append({
            'area': 'Learning',
            'message': f'Pattern recognition active: {patterns_count} patterns learned',
            'evidence': 'System is identifying reusable patterns'
        })

    if healing_count > 0:
        feedback['wins'].append({
            'area': 'Self-Healing',
            'message': f'Self-healing strategies: {healing_count} selectors',
            'evidence': 'System has fallback strategies for common failures'
        })

    return feedback


def generate_corrected_lessons(feedback: dict, cycle_num: int) -> list:
    """Generate corrected lessons"""
    lessons = []

    # From wins
    for win in feedback.get('wins', []):
        lessons.append({
            'type': 'success',
            'area': win['area'],
            'lesson': win['message'],
            'cycle': cycle_num
        })

    # From issues
    for issue in feedback.get('issues', []):
        lessons.append({
            'type': 'improvement',
            'area': issue['area'],
            'lesson': f"Need to improve: {issue['message']}",
            'cycle': cycle_num
        })

    return lessons


def regenerate_all_teaching_files():
    """Regenerate all teaching files with corrected data"""
    barril_path = Path("../barril!!")

    print(" Regenerating Teaching Files with Corrected Metrics")
    print("=" * 70)

    cycles_data = []

    for cycle_num in [1, 2, 3]:
        print(f"\n Cycle {cycle_num}:")
        print("-" * 70)

        # Analyze with corrected metrics
        analysis = analyze_cycle_corrected(cycle_num)

        print(f"    Success Rate: {analysis['success_rate']:.1f}% "
              f"({analysis.get('successful_runs', 0)}/{analysis.get('total_runs', 0)})")
        print(f"    Experiences: {analysis.get('experience_count', 0)}")
        print(f"    Patterns: {analysis.get('patterns_count', 0)}")
        print(f"    Healing: {analysis.get('healing_elements', 0)}")

        # Generate corrected feedback
        feedback = generate_corrected_feedback(analysis, cycle_num)

        # Generate corrected lessons
        lessons = generate_corrected_lessons(feedback, cycle_num)

        # Create corrected teaching file
        teaching_data = {
            'cycle': cycle_num,
            'timestamp': datetime.now().isoformat(),
            'corrected': True,
            'original_bug_fixed': 'success_rate now read from stats.successful_runs/stats.total_runs',
            'analysis': analysis,
            'feedback': feedback,
            'lessons': lessons,
            'meta': {
                'regenerated_at': datetime.now().isoformat(),
                'reason': 'Bug fix: success_rate was read from wrong JSON path',
                'impact': 'All previous teaching files had incorrect success_rate (0% when actually 100%)'
            }
        }

        # Save corrected teaching file
        output_path = barril_path / f"agent_teaching_cycle_{cycle_num}_CORRECTED.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(teaching_data, f, indent=2, ensure_ascii=False)

        print(f"    Saved: {output_path.name}")

        cycles_data.append(teaching_data)

    # Generate summary
    print("\n" + "=" * 70)
    print(" CORRECTED SUMMARY:")
    print("=" * 70)

    for cycle_data in cycles_data:
        cycle_num = cycle_data['cycle']
        analysis = cycle_data['analysis']
        feedback = cycle_data['feedback']

        print(f"\nCycle {cycle_num}:")
        print(f"  Success: {analysis['success_rate']:.1f}% "
              f"({analysis.get('successful_runs', 0)}/{analysis.get('total_runs', 0)})")
        print(f"  Wins: {len(feedback['wins'])}")
        print(f"  Issues: {len(feedback['issues'])}")
        print(f"  Lessons: {len(cycle_data['lessons'])}")

    print("\n All teaching files regenerated with corrected metrics!")
    print(f" Location: {barril_path.absolute()}")


if __name__ == "__main__":
    regenerate_all_teaching_files()
