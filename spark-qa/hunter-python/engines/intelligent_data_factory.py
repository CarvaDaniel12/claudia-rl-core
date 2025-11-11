"""
 INTELLIGENT DATA FACTORY - Dados estratgicos para explorao

OBJETIVO:
No gerar dados aleatrios! Gerar dados ESTRATGICOS que:
- Exploram edge cases
- Variam patterns
- Testam validations
- Descobrem bugs

STRATEGIES:
1. Boundary Testing (min, max, limites)
2. Special Characters (unicode, emojis, SQL injection)
3. Empty/Null values
4. Very Long strings
5. Different languages
6. Edge case combinations

FEEDBACK LOOP:
- Se field X sempre funciona  Tenta variations
- Se field Y sempre quebra  Tenta simplificar
- Aprende quais inputs causam bugs!
"""
from faker import Faker
from datetime import datetime, timedelta
from typing import Dict, List, Any
import random
import string

class IntelligentDataFactory:
    """
    Factory que gera dados ESTRATGICOS para testing
    """
    
    def __init__(self):
        self.faker = Faker()
        
        # Strategies disponveis
        self.strategies = [
            "normal",           # Dados normais (Faker)
            "boundary",         # Min/max values
            "special_chars",    # Unicode, smbolos
            "empty",            # Empty strings, nulls
            "very_long",        # Strings longas
            "multilingual",     # Diferentes idiomas
            "edge_cases"        # Combinations perigosas
        ]
        
        # Stats de uso (feedback loop!)
        self.strategy_stats = {
            strategy: {"used": 0, "success": 0, "bugs_found": 0}
            for strategy in self.strategies
        }
        
        self.current_strategy = "normal"
        self.run_number = 0
    
    def select_strategy(self, run_number: int) -> str:
        """
        Seleciona strategy baseado em run number e feedback
        
        Evolui ao longo do tempo:
        - Runs 1-20: Mostly normal (baseline)
        - Runs 21-50: Mix normal + boundary
        - Runs 51-100: All strategies
        - Runs 101+: Focus on strategies que acharam bugs
        """
        self.run_number = run_number
        
        # Early runs: normal data (baseline)
        if run_number <= 20:
            return random.choice(["normal", "normal", "normal", "boundary"])
        
        # Mid runs: exploratory
        elif run_number <= 100:
            return random.choice(self.strategies)
        
        # Late runs: focus on productive strategies
        else:
            # Calcula qual strategy achou mais bugs
            best_strategies = sorted(
                self.strategies,
                key=lambda s: self.strategy_stats[s]['bugs_found'],
                reverse=True
            )
            
            # 70% melhor, 30% explorao
            if random.random() < 0.7:
                return best_strategies[0]
            else:
                return random.choice(self.strategies)
    
    def generate_property_data(self, strategy: str = None) -> Dict:
        """
        Gera dados de property baseado em strategy
        """
        if strategy is None:
            strategy = self.current_strategy
        
        self.strategy_stats[strategy]['used'] += 1
        timestamp = datetime.now().strftime("%m%d%H%M")
        
        # Base data (sempre tem)
        base_data = {
            "timestamp": timestamp,
            "strategy_used": strategy
        }
        
        # Gera baseado em strategy
        if strategy == "normal":
            return {
                **base_data,
                "name": f"Hunter Property {timestamp}",
                "weblink": f"hunter-property-{timestamp}",
                "floor_count": str(random.randint(1, 5)),
                "property_size": str(random.randint(50, 500)),
                "address_line1": self.faker.street_address(),
                "address_line2": self.faker.secondary_address(),
                "city": self.faker.city(),
                "zip_code": self.faker.zipcode()[:8],
                "bedrooms": str(random.randint(1, 5)),
                "beds": str(random.randint(1, 8)),
                "bathrooms": str(random.choice(["1", "1.5", "2", "2.5", "3"])),
                "base_guests": str(random.randint(2, 6)),
                "max_guests": str(random.randint(4, 10)),
                "extra_guest_fee": str(random.randint(10, 50)),
                "nightly_price": str(random.randint(80, 300)),
                "tax_rate": str(random.randint(5, 15)),
                "security_deposit": str(random.randint(100, 500)),
                "cleaning_fee": str(random.randint(50, 150)),
                "cleaning_fee_tax": str(random.randint(5, 20))
            }
        
        elif strategy == "boundary":
            return {
                **base_data,
                "name": f"BoundTest{timestamp}",  # Short name
                "weblink": f"b{timestamp}",       # Min weblink
                "floor_count": "1",               # Min
                "property_size": "10",            # Min
                "address_line1": "1 St",          # Min address
                "address_line2": "",              # Empty (allowed)
                "city": "A",                      # Min city
                "zip_code": "12345",              # Min zip
                "bedrooms": "1",                  # Min
                "beds": "1",                      # Min
                "bathrooms": "0.5",               # Min
                "base_guests": "1",               # Min
                "max_guests": "2",                # Min
                "extra_guest_fee": "0",           # Min
                "nightly_price": "10",            # Min ($10)
                "tax_rate": "0",                  # Min
                "security_deposit": "0",          # Min
                "cleaning_fee": "5",              # Min
                "cleaning_fee_tax": "0"           # Min
            }
        
        elif strategy == "special_chars":
            return {
                **base_data,
                "name": f"Test Property {timestamp}",     # Special chars
                "weblink": f"test-property-{timestamp}",
                "floor_count": "2",
                "property_size": "100",
                "address_line1": "123 O'Brien St. #5",     # Apostrophe, #
                "address_line2": "Apt. 3",                 # Fraction symbol
                "city": "So Paulo",                        # Accents
                "zip_code": "12345",
                "bedrooms": "2",
                "beds": "2",
                "bathrooms": "1.5",
                "base_guests": "4",
                "max_guests": "6",
                "extra_guest_fee": "15",
                "nightly_price": "100",
                "tax_rate": "10",
                "security_deposit": "100",
                "cleaning_fee": "50",
                "cleaning_fee_tax": "5"
            }
        
        elif strategy == "very_long":
            long_name = f"Property with Very Long Name {timestamp} " + "X" * 50
            return {
                **base_data,
                "name": long_name[:100],  # Max 100 chars
                "weblink": f"very-long-weblink-{timestamp}-" + "a" * 30,
                "floor_count": "10",      # High number
                "property_size": "5000",  # Very large
                "address_line1": self.faker.street_address() + " with additional info" * 3,
                "address_line2": "Suite " + "A" * 20,
                "city": self.faker.city(),
                "zip_code": "99999999",   # Max 8 digits
                "bedrooms": "10",         # Many bedrooms
                "beds": "20",             # Many beds
                "bathrooms": "10",        # Many bathrooms
                "base_guests": "10",      # Many guests
                "max_guests": "20",       # Max guests
                "extra_guest_fee": "300", # Max fee
                "nightly_price": "10000", # High price
                "tax_rate": "50",         # High tax
                "security_deposit": "5000",
                "cleaning_fee": "600",
                "cleaning_fee_tax": "100"
            }
        
        elif strategy == "empty":
            return {
                **base_data,
                "name": f"Empty Test {timestamp}",
                "weblink": f"empty-{timestamp}",
                "floor_count": "",        # Empty (test required validation)
                "property_size": "",      # Empty
                "address_line1": "123 Test",  # Min required
                "address_line2": "",      # Empty allowed
                "city": "Test",
                "zip_code": "12345",
                "bedrooms": "1",
                "beds": "1",
                "bathrooms": "1",
                "base_guests": "2",
                "max_guests": "4",
                "extra_guest_fee": "0",
                "nightly_price": "50",
                "tax_rate": "0",
                "security_deposit": "0",
                "cleaning_fee": "0",
                "cleaning_fee_tax": "0"
            }
        
        else:  # multilingual, edge_cases, etc
            return {
                **base_data,
                "name": f"Casa {timestamp}",     # Portuguese
                "weblink": f"casa-{timestamp}",
                "floor_count": "2",
                "property_size": "150",
                "address_line1": "Rua das Flores, 123",
                "address_line2": "Apto 45",
                "city": "Rio de Janeiro",
                "zip_code": "12345678",
                "bedrooms": "3",
                "beds": "3",
                "bathrooms": "2",
                "base_guests": "4",
                "max_guests": "8",
                "extra_guest_fee": "20",
                "nightly_price": "200",
                "tax_rate": "12",
                "security_deposit": "300",
                "cleaning_fee": "80",
                "cleaning_fee_tax": "10"
            }
    
    def report_result(self, strategy: str, success: bool, bug_found: bool = False):
        """
        Feedback loop: reporta resultado de uma strategy
        """
        if success:
            self.strategy_stats[strategy]['success'] += 1
        
        if bug_found:
            self.strategy_stats[strategy]['bugs_found'] += 1
    
    def get_best_strategy(self) -> str:
        """Retorna strategy que mais achou bugs"""
        best = max(
            self.strategies,
            key=lambda s: self.strategy_stats[s]['bugs_found']
        )
        return best
    
    def print_stats(self):
        """Mostra stats de strategies"""
        print("\n" + "="*70)
        print("DATA FACTORY STATS")
        print("="*70)
        
        for strategy in self.strategies:
            stats = self.strategy_stats[strategy]
            if stats['used'] > 0:
                success_rate = (stats['success'] / stats['used']) * 100
                print(f"{strategy:15} - Used: {stats['used']:3} | Success: {success_rate:5.1f}% | Bugs: {stats['bugs_found']}")
        
        print("="*70)


if __name__ == "__main__":
    factory = IntelligentDataFactory()
    
    # Simula runs
    for i in range(1, 51):
        strategy = factory.select_strategy(i)
        data = factory.generate_property_data(strategy)
        
        print(f"Run {i}: Strategy={strategy}, Name={data['name'][:30]}")
        
        # Simula feedback
        success = random.random() > 0.2
        bug_found = strategy == "boundary" and random.random() > 0.8
        factory.report_result(strategy, success, bug_found)
    
    factory.print_stats()

