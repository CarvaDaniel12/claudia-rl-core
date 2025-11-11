"""
PROPERTY-BASED TESTING - Generate test cases from properties/invariants

CONCEPT: Instead of writing specific test cases, define PROPERTIES the system must satisfy
Then auto-generate hundreds of test cases to verify those properties

EXAMPLE PROPERTY:
- "Property name must always appear in list after creation"
- "Lead count increases by exactly 1 after create"
- "Delete always reduces count by 1"

APPROACH:
1. Define properties as predicates
2. Generate diverse inputs (integration with IntelligentDataFactory)
3. Execute tests with generated inputs
4. Shrink failing cases to minimal example

INTEGRATION:
- Works with field_data.py (already has IntelligentDataFactory)
- Generates N test runs with different strategies
- Validates properties hold for all inputs
- If property violated -> bug found!

INSPIRED BY: Hypothesis (Python), QuickCheck (Haskell)
"""

import json
from pathlib import Path
from typing import Dict, List, Callable, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
import random


@dataclass
class Property:
    """A property that must hold for all inputs"""
    name: str
    predicate: Callable[[Any], bool]  # Function that returns True if property holds
    description: str
    category: str  # "data_integrity", "state_consistency", "performance"
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"


@dataclass
class PropertyViolation:
    """A detected property violation"""
    property_name: str
    input_data: Dict
    expected: str
    actual: str
    timestamp: str
    severity: str


class PropertyBasedTesting:
    """
    Property-based testing framework
    Auto-generates test cases from defined properties
    """
    
    def __init__(self, properties_file: str = "barril!!/property_based_tests.json"):
        self.properties_file = Path(properties_file)
        self.properties_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Defined properties
        self.properties: List[Property] = []
        
        # Violations found
        self.violations: List[PropertyViolation] = []
        
        # Test generation stats
        self.total_tests_generated = 0
        self.total_properties_checked = 0
        
        # Define default properties for E2E flow
        self._define_default_properties()
        
        self._load()
    
    def _define_default_properties(self):
        """Define default properties for E2E flows"""
        
        # Property 1: Created property always has UUID
        self.add_property(
            name="property_has_uuid",
            predicate=lambda result: result.get('property_uid') is not None and len(result.get('property_uid', '')) > 0,
            description="Created property must have non-empty UUID",
            category="data_integrity",
            severity="CRITICAL"
        )
        
        # Property 2: Lead count increases after create
        self.add_property(
            name="lead_count_increases",
            predicate=lambda result: result.get('leads_after', 0) > result.get('leads_before', 0),
            description="Lead count must increase by at least 1 after creation",
            category="state_consistency",
            severity="HIGH"
        )
        
        # Property 3: Delete reduces count
        self.add_property(
            name="delete_reduces_count",
            predicate=lambda result: result.get('count_after', 0) < result.get('count_before', 0),
            description="Entity count must decrease after deletion",
            category="state_consistency",
            severity="HIGH"
        )
        
        # Property 4: Duration must be reasonable
        self.add_property(
            name="duration_reasonable",
            predicate=lambda result: 5.0 < result.get('duration', 0) < 600.0,
            description="Run duration must be between 5s and 10min",
            category="performance",
            severity="MEDIUM"
        )
        
        # Property 5: Successful runs have no errors
        self.add_property(
            name="success_implies_no_errors",
            predicate=lambda result: not result.get('success', False) or len(result.get('errors', [])) == 0,
            description="If success=True, errors list must be empty",
            category="state_consistency",
            severity="CRITICAL"
        )
    
    def _load(self):
        """Load property test results"""
        if self.properties_file.exists():
            try:
                with open(self.properties_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.violations = data.get('violations', [])
                    self.total_tests_generated = data.get('total_tests_generated', 0)
                    print(f"[PropertyBased] Loaded - {len(self.violations)} violations recorded")
            except Exception as e:
                print(f"[PropertyBased] Failed to load: {e}")
    
    def save(self):
        """Save property test results"""
        data = {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "properties_defined": [
                {
                    "name": p.name,
                    "description": p.description,
                    "category": p.category,
                    "severity": p.severity
                } for p in self.properties
            ],
            "total_tests_generated": self.total_tests_generated,
            "total_properties_checked": self.total_properties_checked,
            "violations_found": len(self.violations),
            "violations": [
                {
                    "property": v.property_name,
                    "severity": v.severity,
                    "timestamp": v.timestamp,
                    "expected": v.expected,
                    "actual": v.actual
                } for v in self.violations[-50:]  # Last 50
            ]
        }
        
        try:
            with open(self.properties_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[PropertyBased] Saved - {len(self.violations)} violations")
        except Exception as e:
            print(f"[PropertyBased] Failed to save: {e}")
    
    def add_property(self, name: str, predicate: Callable, description: str, category: str, severity: str):
        """Add a property to check"""
        prop = Property(
            name=name,
            predicate=predicate,
            description=description,
            category=category,
            severity=severity
        )
        self.properties.append(prop)
    
    def check_properties(self, result_data: Dict) -> Tuple[bool, List[PropertyViolation]]:
        """
        Check all properties against result data
        
        Returns:
            (all_passed, violations_list)
        """
        violations = []
        self.total_properties_checked += len(self.properties)
        
        for prop in self.properties:
            try:
                holds = prop.predicate(result_data)
                
                if not holds:
                    violation = PropertyViolation(
                        property_name=prop.name,
                        input_data=result_data,
                        expected=prop.description,
                        actual="Property violated - see input_data",
                        timestamp=datetime.now().isoformat(),
                        severity=prop.severity
                    )
                    violations.append(violation)
                    self.violations.append(violation)
                    
            except Exception as e:
                # Property check itself failed - might indicate bug
                violation = PropertyViolation(
                    property_name=prop.name,
                    input_data=result_data,
                    expected=prop.description,
                    actual=f"Property check failed: {e}",
                    timestamp=datetime.now().isoformat(),
                    severity="HIGH"
                )
                violations.append(violation)
                self.violations.append(violation)
        
        return len(violations) == 0, violations
    
    def generate_test_inputs(self, strategy: str, count: int = 10) -> List[Dict]:
        """
        Generate test inputs using IntelligentDataFactory strategies
        
        Args:
            strategy: "normal", "boundary", "special_chars", etc
            count: Number of test cases to generate
            
        Returns:
            List of input dictionaries
        """
        # Integration with IntelligentDataFactory
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent))
            from intelligent_data_factory import IntelligentDataFactory
            
            factory = IntelligentDataFactory()
            test_inputs = []
            
            for i in range(count):
                input_data = factory.generate_property_data(strategy)
                test_inputs.append(input_data)
            
            self.total_tests_generated += count
            return test_inputs
            
        except Exception as e:
            print(f"[PropertyBased] Failed to generate inputs: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Get property-based testing statistics"""
        critical_violations = [v for v in self.violations if v.severity == "CRITICAL"]
        
        return {
            "properties_defined": len(self.properties),
            "tests_generated": self.total_tests_generated,
            "properties_checked": self.total_properties_checked,
            "violations_found": len(self.violations),
            "critical_violations": len(critical_violations),
            "violation_rate": len(self.violations) / max(self.total_properties_checked, 1)
        }


# Demo
if __name__ == "__main__":
    print("\n" + "="*70)
    print("PROPERTY-BASED TESTING - Demo")
    print("="*70 + "\n")
    
    pbt = PropertyBasedTesting()
    
    print(f"Properties defined: {len(pbt.properties)}")
    for p in pbt.properties:
        print(f"  - {p.name}: {p.description}")
    
    # Test with valid data
    print("\nTest 1: Valid data")
    valid_result = {
        "property_uid": "abc123",
        "leads_before": 5,
        "leads_after": 6,
        "count_before": 10,
        "count_after": 9,
        "duration": 45.0,
        "success": True,
        "errors": []
    }
    all_pass, violations = pbt.check_properties(valid_result)
    print(f"  All properties passed: {all_pass}")
    
    # Test with invalid data
    print("\nTest 2: Invalid data (missing UUID)")
    invalid_result = {
        "property_uid": "",  # Violation!
        "leads_before": 5,
        "leads_after": 5,  # Violation! Count didn't increase
        "count_before": 10,
        "count_after": 9,
        "duration": 45.0,
        "success": True,
        "errors": ["timeout"]  # Violation! Has errors but success=True
    }
    all_pass, violations = pbt.check_properties(invalid_result)
    print(f"  All properties passed: {all_pass}")
    print(f"  Violations: {len(violations)}")
    for v in violations:
        print(f"    [{v.severity}] {v.property_name}: {v.expected}")
    
    # Generate test inputs
    print("\nGenerating test inputs:")
    inputs = pbt.generate_test_inputs("boundary", count=5)
    print(f"  Generated {len(inputs)} test cases")
    
    # Stats
    print(f"\nStats: {pbt.get_stats()}")
    
    pbt.save()
    print("\n[OK] Demo complete")

