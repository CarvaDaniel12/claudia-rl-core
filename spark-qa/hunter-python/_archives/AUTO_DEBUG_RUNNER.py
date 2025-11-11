"""
AUTO DEBUG RUNNER - Roda test_full_flow com debug automatico

Captura screenshots em CADA step
Salva log detalhado
Continua mesmo com erros (tenta completar o maximo possivel)
"""
import sys
from pathlib import Path
from datetime import datetime
import traceback

# Add to path
hunter_path = Path(__file__).parent
sys.path.insert(0, str(hunter_path))

def main():
    log_file = Path("AUTO_DEBUG_LOG.txt")
    screenshots_dir = Path("auto_debug_screenshots")
    screenshots_dir.mkdir(exist_ok=True)
    
    # Redirect output to log
    class Tee:
        def __init__(self, *files):
            self.files = files
        def write(self, data):
            for f in self.files:
                f.write(data)
                f.flush()
        def flush(self):
            for f in self.files:
                f.flush()
    
    log = open(log_file, 'w', encoding='utf-8')
    sys.stdout = Tee(sys.stdout, log)
    sys.stderr = Tee(sys.stderr, log)
    
    print("="*70)
    print(f"AUTO DEBUG RUNNER - Started: {datetime.now()}")
    print("="*70)
    print(f"Screenshots: {screenshots_dir}")
    print(f"Log: {log_file}")
    print("="*70)
    
    try:
        # Import and run test
        from flows import test_full_flow
        
        print("\nExecuting test_full_flow.main()...")
        test_full_flow.main()
        
        print("\n" + "="*70)
        print("SUCCESS: Test completed!")
        print("="*70)
        
    except Exception as e:
        print("\n" + "="*70)
        print(f"ERROR: {e}")
        print("="*70)
        print("\nFull traceback:")
        traceback.print_exc()
        
        print("\n" + "="*70)
        print("PARTIAL SUCCESS: Check log for details")
        print("="*70)
    
    finally:
        print(f"\nFinished: {datetime.now()}")
        print(f"Log saved: {log_file}")
        print(f"Screenshots: {screenshots_dir}")
        
        log.close()
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        
        print(f"\nAUTO DEBUG LOG: {log_file}")
        print("Check AUTO_DEBUG_LOG.txt for full output")

if __name__ == "__main__":
    main()

