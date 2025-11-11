"""
CODEGEN DEMO PROCESSOR - Extrai padrões de navegação de demos gravadas

Input: Arquivo .py com codegen do Playwright
Output: State-action pairs que RL pode usar para Imitation Learning

Extrai:
- Sequências de navegação (Properties -> Calendar -> Analytics)
- Padrões de preenchimento (fill fields, select options)
- Interações modais (open, fill, save, close)
- Explorações (tabs, filters, toggles)
"""

import re
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

class CodegenDemoProcessor:
    """
    Processa demo gravada com playwright codegen
    Extrai padrões de navegação para Imitation Learning
    """
    
    def __init__(self, demo_file: str):
        self.demo_file = Path(demo_file)
        self.actions = []
        self.patterns = []
        
    def parse_demo(self) -> List[Dict]:
        """Lê arquivo .py e extrai todas as ações Playwright"""
        with open(self.demo_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extrai linhas dentro da função run()
        if 'def run(' not in content:
            print("[ERROR] Could not find run() function")
            return []
        
        # Pega tudo entre "def run(" e "with sync_playwright"
        start_idx = content.find('def run(')
        end_idx = content.find('with sync_playwright')
        if end_idx == -1:
            end_idx = content.find('# -----', start_idx)
        if end_idx == -1:
            end_idx = len(content)
        
        code = content[start_idx:end_idx]
        # Remove a linha de definição da função
        code = '\n'.join(code.split('\n')[1:])
        lines = [l.strip() for l in code.split('\n') if l.strip() and not l.strip().startswith('#')]
        
        # Parse cada linha
        step = 1
        for line in lines:
            action = self._parse_action_line(line, step)
            if action:
                self.actions.append(action)
                step += 1
        
        print(f"[PARSE] Extracted {len(self.actions)} actions from demo")
        return self.actions
    
    def _parse_action_line(self, line: str, step: int) -> Dict:
        """Parse uma linha de código Playwright para action dict"""
        
        # Patterns comuns
        patterns = {
            'goto': r'page\.goto\("([^"]+)"\)',
            'click_testid': r'page\.get_by_test_id\("([^"]+)"\)\.click\(\)',
            'fill_testid': r'page\.get_by_test_id\("([^"]+)"\)\.fill\("([^"]*)"\)',
            'select_testid': r'page\.get_by_test_id\("([^"]+)"\)\.select_option\("([^"]*)"\)',
            'click_role': r'page\.get_by_role\("([^"]+)",\s*name="([^"]+)"\)\.click\(\)',
            'check_radio': r'page\.get_by_role\("radio",\s*name="([^"]+)"\)\.check\(\)',
            'click_text': r'page\.get_by_text\("([^"]+)"\)\.click\(\)',
            'press_key': r'page\.get_by_test_id\("([^"]+)"\)\.press\("([^"]+)"\)',
            'locator_click': r'page\.locator\("([^"]+)"\)\.click\(\)',
            'frame_action': r'page\.locator\(\[data-testid="legacy-page-frame"\]\)\.content_frame',
        }
        
        action = {
            'step': step,
            'original_code': line,
        }
        
        # Goto
        if match := re.search(patterns['goto'], line):
            action.update({
                'type': 'navigate',
                'action': 'goto',
                'params': {'url': match.group(1)}
            })
        
        # Click testid
        elif match := re.search(patterns['click_testid'], line):
            action.update({
                'type': 'interact',
                'action': 'click',
                'target': 'testid',
                'params': {'testid': match.group(1)}
            })
        
        # Fill testid
        elif match := re.search(patterns['fill_testid'], line):
            action.update({
                'type': 'input',
                'action': 'fill',
                'target': 'testid',
                'params': {'testid': match.group(1), 'value': match.group(2)}
            })
        
        # Select testid
        elif match := re.search(patterns['select_testid'], line):
            action.update({
                'type': 'input',
                'action': 'select',
                'target': 'testid',
                'params': {'testid': match.group(1), 'value': match.group(2)}
            })
        
        # Click role
        elif match := re.search(patterns['click_role'], line):
            action.update({
                'type': 'interact',
                'action': 'click',
                'target': 'role',
                'params': {'role': match.group(1), 'name': match.group(2)}
            })
        
        # Check radio
        elif match := re.search(patterns['check_radio'], line):
            action.update({
                'type': 'input',
                'action': 'check_radio',
                'params': {'name': match.group(1)}
            })
        
        # Click text
        elif match := re.search(patterns['click_text'], line):
            action.update({
                'type': 'interact',
                'action': 'click',
                'target': 'text',
                'params': {'text': match.group(1)}
            })
        
        # Press key
        elif match := re.search(patterns['press_key'], line):
            action.update({
                'type': 'keyboard',
                'action': 'press',
                'params': {'testid': match.group(1), 'key': match.group(2)}
            })
        
        # Legacy frame (ignore for now)
        elif 'legacy-page-frame' in line:
            return None
        
        # Generic locator click
        elif match := re.search(patterns['locator_click'], line):
            action.update({
                'type': 'interact',
                'action': 'click',
                'target': 'locator',
                'params': {'selector': match.group(1)}
            })
        
        else:
            # Unknown action
            return None
        
        return action
    
    def extract_patterns(self) -> List[Dict]:
        """Agrupa ações em padrões semânticos de alto nível"""
        if not self.actions:
            self.parse_demo()
        
        patterns = []
        i = 0
        
        while i < len(self.actions):
            action = self.actions[i]
            
            # LOGIN pattern (testid=email, password, submit)
            if action.get('params', {}).get('testid') == 'email':
                pattern = self._extract_login_pattern(i)
                if pattern:
                    patterns.append(pattern)
                    i += pattern['length']
                    continue
            
            # NAVIGATION pattern (nav-item-common.*)
            if 'nav-item-common' in action.get('params', {}).get('testid', ''):
                pattern = self._extract_navigation_pattern(i)
                if pattern:
                    patterns.append(pattern)
                    i += pattern['length']
                    continue
            
            # FORM FILL pattern (multiple fills in sequence)
            if action.get('action') in ['fill', 'select']:
                pattern = self._extract_form_pattern(i)
                if pattern:
                    patterns.append(pattern)
                    i += pattern['length']
                    continue
            
            # MODAL OPEN pattern (modal-form, button-submit)
            if 'button' in action.get('params', {}).get('testid', ''):
                pattern = self._extract_modal_pattern(i)
                if pattern:
                    patterns.append(pattern)
                    i += pattern['length']
                    continue
            
            # TAB NAVIGATION (property-settings-tab-*)
            if 'tab' in action.get('params', {}).get('testid', ''):
                pattern = self._extract_tab_pattern(i)
                if pattern:
                    patterns.append(pattern)
                    i += pattern['length']
                    continue
            
            # FILTER pattern (filter-icon, submit-filters)
            if 'filter' in action.get('params', {}).get('testid', ''):
                pattern = self._extract_filter_pattern(i)
                if pattern:
                    patterns.append(pattern)
                    i += pattern['length']
                    continue
            
            i += 1
        
        print(f"[EXTRACT] Found {len(patterns)} high-level patterns")
        self.patterns = patterns
        return patterns
    
    def _extract_login_pattern(self, start: int) -> Dict:
        """Extrai padrão de login"""
        actions = []
        i = start
        
        # email, password, submit
        while i < len(self.actions) and i < start + 5:
            a = self.actions[i]
            testid = a.get('params', {}).get('testid', '')
            if testid in ['email', 'password', 'submit-button']:
                actions.append(a)
                i += 1
                if testid == 'submit-button':
                    break
            else:
                break
        
        if len(actions) >= 2:
            return {
                'pattern_type': 'login',
                'name': 'user_login',
                'actions': actions,
                'length': len(actions),
                'metadata': {
                    'critical': True,
                    'repeatable': True
                }
            }
        return None
    
    def _extract_navigation_pattern(self, start: int) -> Dict:
        """Extrai padrão de navegação entre páginas"""
        action = self.actions[start]
        nav_item = action.get('params', {}).get('testid', '').replace('nav-item-common.', '')
        
        return {
            'pattern_type': 'navigation',
            'name': f'navigate_to_{nav_item}',
            'actions': [action],
            'length': 1,
            'metadata': {
                'target_page': nav_item,
                'critical': False,
                'repeatable': True
            }
        }
    
    def _extract_form_pattern(self, start: int) -> Dict:
        """Extrai padrão de preenchimento de formulário"""
        actions = []
        i = start
        
        # Coleta fills/selects consecutivos
        while i < len(self.actions) and i < start + 20:
            a = self.actions[i]
            if a.get('action') in ['fill', 'select', 'check_radio']:
                actions.append(a)
                i += 1
            else:
                break
        
        if len(actions) >= 2:
            # Identifica qual form baseado nos testids
            testids = [a.get('params', {}).get('testid', '') for a in actions]
            form_name = 'unknown_form'
            
            if any('property' in t for t in testids):
                form_name = 'property_form'
            elif any('lead' in t or 'guest' in t for t in testids):
                form_name = 'lead_form'
            elif any('price' in t or 'fee' in t for t in testids):
                form_name = 'pricing_form'
            
            return {
                'pattern_type': 'form_fill',
                'name': form_name,
                'actions': actions,
                'length': len(actions),
                'metadata': {
                    'field_count': len(actions),
                    'critical': True,
                    'repeatable': True
                }
            }
        return None
    
    def _extract_modal_pattern(self, start: int) -> Dict:
        """Extrai padrão de interação com modal"""
        actions = []
        i = start
        
        # Open button -> fills -> submit/cancel
        while i < len(self.actions) and i < start + 15:
            a = self.actions[i]
            testid = a.get('params', {}).get('testid', '')
            actions.append(a)
            i += 1
            
            if 'submit' in testid or 'cancel' in testid or 'confirm' in testid:
                break
        
        if len(actions) >= 2:
            return {
                'pattern_type': 'modal_interaction',
                'name': 'modal_workflow',
                'actions': actions,
                'length': len(actions),
                'metadata': {
                    'has_submit': any('submit' in a.get('params', {}).get('testid', '') for a in actions),
                    'critical': True,
                    'repeatable': True
                }
            }
        return None
    
    def _extract_tab_pattern(self, start: int) -> Dict:
        """Extrai padrão de navegação entre tabs"""
        action = self.actions[start]
        tab_name = action.get('params', {}).get('testid', '').replace('property-settings-tab-', '')
        
        return {
            'pattern_type': 'tab_navigation',
            'name': f'open_tab_{tab_name}',
            'actions': [action],
            'length': 1,
            'metadata': {
                'tab': tab_name,
                'critical': False,
                'repeatable': True
            }
        }
    
    def _extract_filter_pattern(self, start: int) -> Dict:
        """Extrai padrão de uso de filtros"""
        actions = []
        i = start
        
        # filter-icon -> selects -> submit-filters
        while i < len(self.actions) and i < start + 10:
            a = self.actions[i]
            testid = a.get('params', {}).get('testid', '')
            if 'filter' in testid or a.get('action') == 'select':
                actions.append(a)
                i += 1
                if 'submit-filters' in testid:
                    break
            else:
                break
        
        if len(actions) >= 2:
            return {
                'pattern_type': 'filter',
                'name': 'apply_filters',
                'actions': actions,
                'length': len(actions),
                'metadata': {
                    'filter_count': len([a for a in actions if a.get('action') == 'select']),
                    'critical': False,
                    'repeatable': True
                }
            }
        return None
    
    def save_for_rl(self, output_file: str = None):
        """Salva padrões em formato que RL pode usar"""
        if not self.patterns:
            self.extract_patterns()
        
        if output_file is None:
            output_file = Path("../barril!!/imitation_learning_patterns.json")
        else:
            output_file = Path(output_file)
        
        # Estrutura para RL
        rl_format = {
            "version": "1.0_imitation_learning",
            "source": "human_codegen_demo",
            "demo_file": str(self.demo_file),
            "processed_at": datetime.now().isoformat(),
            "total_actions": len(self.actions),
            "total_patterns": len(self.patterns),
            
            "patterns": {
                p['name']: {
                    'pattern_type': p['pattern_type'],
                    'action_sequence': p['actions'],
                    'metadata': p['metadata'],
                    'confidence': 1.0,  # Human demonstration
                    'source': 'human_demo',
                    'usage_count': 0
                }
                for p in self.patterns
            },
            
            "statistics": {
                'login': len([p for p in self.patterns if p['pattern_type'] == 'login']),
                'navigation': len([p for p in self.patterns if p['pattern_type'] == 'navigation']),
                'form_fill': len([p for p in self.patterns if p['pattern_type'] == 'form_fill']),
                'modal': len([p for p in self.patterns if p['pattern_type'] == 'modal_interaction']),
                'tab': len([p for p in self.patterns if p['pattern_type'] == 'tab_navigation']),
                'filter': len([p for p in self.patterns if p['pattern_type'] == 'filter']),
            }
        }
        
        # Save
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(rl_format, f, indent=2, ensure_ascii=False)
        
        print(f"\n[SAVE] Patterns saved to: {output_file}")
        print(f"\n[STATS] Pattern types:")
        for ptype, count in rl_format['statistics'].items():
            print(f"  {ptype}: {count}")
        
        return rl_format


if __name__ == "__main__":
    print("\n" + "="*70)
    print("CODEGEN DEMO PROCESSOR")
    print("="*70)
    
    demo_file = "demos/exploration_full_platform.py"
    processor = CodegenDemoProcessor(demo_file)
    
    # Parse
    actions = processor.parse_demo()
    
    # Extract patterns
    patterns = processor.extract_patterns()
    
    # Save for RL
    result = processor.save_for_rl()
    
    print("\n[OK] Processing complete!")
    print(f"  Total actions: {len(actions)}")
    print(f"  High-level patterns: {len(patterns)}")
    print(f"\nRL can now use these {len(patterns)} patterns for Imitation Learning!")

