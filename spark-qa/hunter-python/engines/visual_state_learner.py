"""
 VISUAL STATE LEARNER - Aprende com screenshots

OBJETIVO:
Hunter detecta mudanas visuais e aprende patterns visuais!

CAPACIDADES:
1.  Detecta se ao teve efeito (mudana visual)
2.  Identifica loops visuais (mesma tela repetida)
3.  Reconhece estados conhecidos (similarity matching)
4.  Aprende "visual signatures" de cada pgina

TECNOLOGIA:
- PIL (Pillow) - Image processing
- imagehash - Perceptual hashing (detecta similarity)
- OpenCV (opcional) - Template matching avanado

BENEFITS:
- Detecta quando selector "funcionou" mas no fez nada
- Identifica loops antes de completar 3 ciclos
- Aprende visual patterns de cada estado
- Evidncia visual de bugs (screenshots automticos)
"""
import io
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from PIL import Image
import imagehash
import json

class VisualStateLearner:
    """
    Sistema de aprendizado visual para Hunter
    """
    
    def __init__(
        self,
        screenshots_dir: str = "../barril!!/screenshots",
        visual_memory_file: str = "../barril!!/visual_memory.json"
    ):
        self.screenshots_dir = Path(screenshots_dir)
        self.visual_memory_file = Path(visual_memory_file)
        
        # Create screenshots dir if not exists
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        # Visual memory: hash  state info
        self.visual_memory = self._load_visual_memory()
        
        # Current session
        self.session_screenshots = []
        self.state_history = []  # Track visual states visited
        
        # Thresholds (tuneable!)
        self.SIMILARITY_THRESHOLD = 10  # Hash distance < 10 = similar
        self.LOOP_THRESHOLD = 3         # Same state 3x = loop
        self.NO_CHANGE_THRESHOLD = 5    # Hash distance < 5 = no change
    
    def _load_visual_memory(self) -> Dict:
        """Carrega memria visual de sesses anteriores"""
        if self.visual_memory_file.exists():
            with open(self.visual_memory_file, 'r') as f:
                return json.load(f)
        return {
            "known_states": {},      # hash  state_name
            "state_transitions": {}, # state_a  state_b (visual flow)
            "stats": {
                "total_screenshots": 0,
                "unique_states": 0,
                "loops_detected": 0
            }
        }
    
    def capture_state(
        self,
        page,
        state_name: str,
        action_description: str = ""
    ) -> Dict:
        """
        Captura screenshot e analisa estado visual
        
        Returns:
            {
                "screenshot_path": str,
                "hash": str,
                "state_type": "NEW" | "KNOWN" | "LOOP",
                "similar_to": str | None,
                "visual_change_detected": bool
            }
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{state_name}_{timestamp}.png"
        screenshot_path = self.screenshots_dir / filename
        
        # Capture screenshot
        screenshot_bytes = page.screenshot()
        
        # Save to disk
        with open(screenshot_path, 'wb') as f:
            f.write(screenshot_bytes)
        
        # Calculate perceptual hash
        img = Image.open(io.BytesIO(screenshot_bytes))
        img_hash = str(imagehash.phash(img))
        
        # Analyze state
        state_type, similar_to = self._analyze_state(img_hash, state_name)
        
        # Check for loops
        self.state_history.append(img_hash)
        loop_detected = self._detect_loop(img_hash)
        
        if loop_detected:
            state_type = "LOOP"
        
        # Save to memory
        if state_type == "NEW":
            self.visual_memory['known_states'][img_hash] = {
                "name": state_name,
                "first_seen": timestamp,
                "occurrences": 1,
                "screenshot_example": str(screenshot_path)
            }
            self.visual_memory['stats']['unique_states'] += 1
        else:
            # Increment occurrence
            if img_hash in self.visual_memory['known_states']:
                self.visual_memory['known_states'][img_hash]['occurrences'] += 1
        
        self.visual_memory['stats']['total_screenshots'] += 1
        
        # Record in session
        self.session_screenshots.append({
            "path": str(screenshot_path),
            "hash": img_hash,
            "state_name": state_name,
            "action": action_description,
            "timestamp": timestamp,
            "state_type": state_type
        })
        
        return {
            "screenshot_path": str(screenshot_path),
            "hash": img_hash,
            "state_type": state_type,
            "similar_to": similar_to,
            "loop_detected": loop_detected
        }
    
    def _analyze_state(self, current_hash: str, state_name: str) -> Tuple[str, Optional[str]]:
        """
        Analisa se estado  novo ou conhecido
        
        Returns: (state_type, similar_to)
        """
        # Exact match
        if current_hash in self.visual_memory['known_states']:
            known_name = self.visual_memory['known_states'][current_hash]['name']
            return ("KNOWN", known_name)
        
        # Similarity check (perceptual hash permite slight differences)
        current_hash_obj = imagehash.hex_to_hash(current_hash)
        
        for known_hash, state_info in self.visual_memory['known_states'].items():
            known_hash_obj = imagehash.hex_to_hash(known_hash)
            distance = current_hash_obj - known_hash_obj
            
            if distance <= self.SIMILARITY_THRESHOLD:
                return ("SIMILAR", state_info['name'])
        
        return ("NEW", None)
    
    def _detect_loop(self, current_hash: str) -> bool:
        """
        Detecta loops visuais (visitou mesma tela 3x)
        """
        if len(self.state_history) < self.LOOP_THRESHOLD:
            return False
        
        # Conta quantas vezes viu esse hash recentemente
        recent_history = self.state_history[-10:]  # Last 10 states
        count = 0
        
        current_hash_obj = imagehash.hex_to_hash(current_hash)
        
        for hist_hash in recent_history:
            hist_hash_obj = imagehash.hex_to_hash(hist_hash)
            distance = current_hash_obj - hist_hash_obj
            
            if distance <= self.SIMILARITY_THRESHOLD:
                count += 1
        
        if count >= self.LOOP_THRESHOLD:
            self.visual_memory['stats']['loops_detected'] += 1
            return True
        
        return False
    
    def detect_visual_change(
        self,
        before_screenshot_bytes: bytes,
        after_screenshot_bytes: bytes
    ) -> Dict:
        """
        Detecta o quanto mudou visualmente entre before/after
        
        Returns:
            {
                "change_magnitude": "NONE" | "MINOR" | "MAJOR",
                "distance": int,
                "action_had_effect": bool
            }
        """
        before_img = Image.open(io.BytesIO(before_screenshot_bytes))
        after_img = Image.open(io.BytesIO(after_screenshot_bytes))
        
        before_hash = imagehash.phash(before_img)
        after_hash = imagehash.phash(after_img)
        
        distance = before_hash - after_hash
        
        if distance < self.NO_CHANGE_THRESHOLD:
            magnitude = "NONE"
            had_effect = False
        elif distance < 20:
            magnitude = "MINOR"
            had_effect = True
        else:
            magnitude = "MAJOR"
            had_effect = True
        
        return {
            "change_magnitude": magnitude,
            "distance": int(distance),
            "action_had_effect": had_effect
        }
    
    def get_visual_signature(self, state_name: str) -> Optional[str]:
        """
        Retorna hash visual de um estado conhecido
        """
        for hash_val, state_info in self.visual_memory['known_states'].items():
            if state_info['name'] == state_name:
                return hash_val
        return None
    
    def calculate_visual_reward(self, state_result: Dict) -> float:
        """
        Calcula reward baseado em anlise visual
        
        Args:
            state_result: Resultado do capture_state()
        
        Returns:
            Reward points
        """
        reward = 0
        
        # New visual state discovered
        if state_result['state_type'] == "NEW":
            reward += 10
            print(f"   +10 NEW visual state discovered!")
        
        # Loop detected (penalty!)
        if state_result['loop_detected']:
            reward -= 15
            print(f"   -15 LOOP detected visually!")
        
        # Known state (small penalty for not exploring)
        if state_result['state_type'] == "KNOWN":
            reward -= 2
            print(f"   -2 Revisiting known state")
        
        return reward
    
    def save_visual_memory(self):
        """Persiste visual memory para prximas sesses"""
        with open(self.visual_memory_file, 'w') as f:
            json.dump(self.visual_memory, f, indent=2)
        
        print(f"\nVisual memory saved: {self.visual_memory_file}")
        print(f"   Known states: {len(self.visual_memory['known_states'])}")
        print(f"   Loops detected: {self.visual_memory['stats']['loops_detected']}")
    
    def print_session_summary(self):
        """Sumrio da sesso atual"""
        print("\n" + "="*70)
        print("VISUAL LEARNING SESSION SUMMARY")
        print("="*70)
        
        new_states = len([s for s in self.session_screenshots if s.get('state_type') == 'NEW'])
        loops = len([s for s in self.session_screenshots if s.get('state_type') == 'LOOP'])
        
        print(f"Screenshots captured: {len(self.session_screenshots)}")
        print(f"New states discovered: {new_states}")
        print(f"Loops detected: {loops}")
        print(f"Total known states: {len(self.visual_memory['known_states'])}")
        print("="*70)


# Teste rpido
if __name__ == "__main__":
    print("\n" + "="*70)
    print("VISUAL STATE LEARNER - Test")
    print("="*70)
    print("\nThis system learns visual patterns from screenshots")
    print("Detects: loops, state changes, visual similarity")
    print("="*70 + "\n")
    
    learner = VisualStateLearner()
    
    print(f"Visual memory loaded:")
    print(f"   Known states: {len(learner.visual_memory['known_states'])}")
    print(f"   Total screenshots: {learner.visual_memory['stats']['total_screenshots']}")
    print(f"   Loops detected: {learner.visual_memory['stats']['loops_detected']}")
    
    print("\nReady to capture visual states during training!")
    print("\nUsage:")
    print("   result = learner.capture_state(page, 'after_login')")
    print("   reward = learner.calculate_visual_reward(result)")

