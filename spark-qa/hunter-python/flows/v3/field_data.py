"""
Test data for E2E flows: valid, invalid, and edge cases

Structured for easy consumption by test flows and RL system
"""
import random
import string
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Import IntelligentDataFactory for fuzzing strategies
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from engines.intelligent_data_factory import IntelligentDataFactory


class FieldData:
    """
    Test data factory for property and lead fields
    NOW WITH FUZZING: Set use_fuzzing=True to enable smart data generation
    """
    
    def __init__(self, use_fuzzing: bool = False, run_number: int = 1):
        self.session_id = self._generate_id(4)
        self.use_fuzzing = use_fuzzing
        self.run_number = run_number
        
        if use_fuzzing:
            self.fuzzer = IntelligentDataFactory()
            self.fuzzing_strategy = self.fuzzer.select_strategy(run_number)
        else:
            self.fuzzer = None
            self.fuzzing_strategy = "normal"
    
    @staticmethod
    def _generate_id(length: int = 4) -> str:
        """Generate random alphanumeric ID"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    # PROPERTY DATA
    
    def property_name(self, prefix: str = "TEST_PROPERTY") -> dict:
        """Property name test data"""
        id_suffix = self._generate_id(4)
        return {
            "valid": f"{prefix}_{id_suffix}",
            "valid_with_spaces": f"Test Property {id_suffix}",
            "valid_with_special": f"Test-Property_{id_suffix}",
            "min_length": "A",
            "max_length": "A" * 255,
            "invalid_empty": "",
            "invalid_only_spaces": "   ",
            "edge_unicode": f"Test 测试 {id_suffix}",
            "edge_emoji": f"Test Home {id_suffix}",
        }
    
    def property_size(self) -> dict:
        """Property size (sqft) test data"""
        return {
            "valid_small": "500",
            "valid_medium": "1500",
            "valid_large": "5000",
            "min": "1",
            "max": "999999",
            "invalid_zero": "0",
            "invalid_negative": "-100",
            "invalid_text": "abc",
            "invalid_decimal": "100.5",
            "edge_very_large": "9999999",
        }
    
    def address_line1(self) -> dict:
        """Street address test data"""
        num = random.randint(100, 9999)
        return {
            "valid": f"{num} Test Street",
            "valid_apartment": f"{num} Main St Apt 5B",
            "valid_po_box": f"PO Box {num}",
            "min_length": "1",
            "max_length": "A" * 255,
            "invalid_empty": "",
            "edge_special_chars": f"{num} Test St. #5-B",
            "edge_unicode": f"{num} Rua São Paulo",
        }
    
    def city(self) -> dict:
        """City name test data"""
        cities = ["TestCity", "New York", "São Paulo", "London", "Tokyo"]
        return {
            "valid": random.choice(cities),
            "valid_with_spaces": "Los Angeles",
            "valid_with_hyphen": "Winston-Salem",
            "min_length": "A",
            "max_length": "A" * 100,
            "invalid_empty": "",
            "edge_special": "Saint-Jean-sur-Richelieu",
            "edge_unicode": "São Paulo",
        }
    
    def zip_code(self) -> dict:
        """Zip/postal code test data"""
        return {
            "valid_us": "12345",
            "valid_us_plus4": "12345-6789",
            "valid_ca": "A1A 1A1",
            "valid_uk": "SW1A 1AA",
            "valid_br": "01310-100",
            "min_length": "12345",
            "invalid_too_short": "123",
            "invalid_letters_only": "ABCDE",
            "edge_all_zeros": "00000",
        }
    
    def state(self) -> dict:
        """State/province test data"""
        states = ["CA", "NY", "TX", "FL", "IL"]
        return {
            "valid": random.choice(states),
            "valid_full_name": "California",
            "min_length": "CA",
            "max_length": "A" * 50,
            "invalid_empty": "",
            "edge_lowercase": "ca",
        }
    
    def country_code(self) -> dict:
        """Country code test data"""
        return {
            "valid_us": "US",
            "valid_ca": "CA",
            "valid_uk": "GB",
            "valid_br": "BR",
            "valid_de": "DE",
        }
    
    def base_guests(self) -> dict:
        """Base guest count test data"""
        return {
            "valid_small": "2",
            "valid_medium": "4",
            "valid_large": "8",
            "min": "1",
            "max": "50",
            "invalid_zero": "0",
            "invalid_negative": "-1",
            "invalid_text": "abc",
            "edge_very_large": "100",
        }
    
    def max_guests(self) -> dict:
        """Max guest count test data"""
        return {
            "valid_small": "4",
            "valid_medium": "8",
            "valid_large": "16",
            "min": "1",
            "max": "100",
            "invalid_zero": "0",
            "invalid_less_than_base": "1",
            "edge_very_large": "200",
        }
    
    def nightly_price(self) -> dict:
        """Nightly base price test data"""
        return {
            "valid_low": "50",
            "valid_medium": "150",
            "valid_high": "500",
            "valid_very_high": "2000",
            "min": "1",
            "invalid_zero": "0",
            "invalid_negative": "-100",
            "invalid_text": "abc",
            "invalid_decimal": "99.99",
            "edge_very_high": "99999",
        }
    
    def currency(self) -> dict:
        """Currency code test data"""
        return {
            "valid_usd": "USD",
            "valid_eur": "EUR",
            "valid_gbp": "GBP",
            "valid_brl": "BRL",
            "valid_jpy": "JPY",
        }
    
    def description_text(self, field_name: str = "description") -> dict:
        """Description field test data"""
        return {
            "valid_short": f"Short {field_name} text",
            "valid_medium": f"This is a medium length {field_name} with multiple sentences. It provides good information.",
            "valid_long": f"This is a very long {field_name} text. " * 20,
            "min_length": "A",
            "max_length": "A" * 5000,
            "invalid_empty": "",
            "edge_special_chars": f"Description with $pecial ch@rs & symbols!",
            "edge_unicode": f"Description com acentuação: São Paulo, Açúcar, Café",
            "edge_newlines": f"Line 1\nLine 2\nLine 3",
        }
    
    def tax_rate(self) -> dict:
        """Tax rate percentage test data"""
        return {
            "valid_low": "5",
            "valid_medium": "10",
            "valid_high": "25",
            "min": "0",
            "max": "100",
            "invalid_negative": "-5",
            "invalid_over_100": "150",
            "invalid_text": "abc",
            "edge_decimal": "10.5",
        }
    
    def cleaning_fee(self) -> dict:
        """Cleaning fee test data"""
        return {
            "valid_low": "50",
            "valid_medium": "100",
            "valid_high": "300",
            "min": "0",
            "max": "9999",
            "invalid_negative": "-50",
            "invalid_text": "abc",
        }
    
    # LEAD DATA
    
    def guest_name(self, prefix: str = "TestGuest") -> dict:
        """Guest full name test data"""
        id_suffix = self._generate_id(4)
        return {
            "valid": f"{prefix}{id_suffix}",
            "valid_with_space": f"Test Guest {id_suffix}",
            "valid_full": f"John Smith {id_suffix}",
            "valid_with_middle": f"John Michael Smith {id_suffix}",
            "min_length": "A",
            "max_length": "A" * 255,
            "invalid_empty": "",
            "edge_hyphenated": f"Mary-Jane Smith {id_suffix}",
            "edge_apostrophe": f"O'Connor {id_suffix}",
            "edge_unicode": f"José García {id_suffix}",
        }
    
    def first_name(self, prefix: str = "Test") -> dict:
        """Guest first name test data"""
        id_suffix = self._generate_id(4)
        return {
            "valid": f"{prefix}{id_suffix}",
            "valid_common": "John",
            "min_length": "A",
            "max_length": "A" * 100,
            "invalid_empty": "",
            "edge_hyphenated": "Mary-Jane",
            "edge_unicode": "José",
        }
    
    def last_name(self, prefix: str = "TestLast") -> dict:
        """Guest last name test data"""
        id_suffix = self._generate_id(4)
        return {
            "valid": f"{prefix}{id_suffix}",
            "valid_common": "Smith",
            "min_length": "A",
            "max_length": "A" * 100,
            "invalid_empty": "",
            "edge_apostrophe": "O'Connor",
            "edge_hyphenated": "Smith-Jones",
            "edge_unicode": "García",
        }
    
    def email(self, prefix: str = "test") -> dict:
        """Email address test data"""
        id_suffix = self._generate_id(4)
        return {
            "valid": f"{prefix}{id_suffix}@test.com",
            "valid_plus": f"{prefix}+{id_suffix}@test.com",
            "valid_subdomain": f"{prefix}@mail.test.com",
            "valid_hyphen": f"{prefix}-{id_suffix}@test.com",
            "valid_underscore": f"{prefix}_{id_suffix}@test.com",
            "invalid_empty": "",
            "invalid_no_at": f"{prefix}{id_suffix}test.com",
            "invalid_no_domain": f"{prefix}@",
            "invalid_no_tld": f"{prefix}@test",
            "invalid_spaces": f"{prefix} {id_suffix}@test.com",
            "edge_long": f"{'a' * 50}@{'b' * 50}.com",
        }
    
    def phone(self) -> dict:
        """Phone number test data"""
        num = random.randint(1000000, 9999999)
        return {
            "valid_us": f"+1234567{num}",
            "valid_us_formatted": f"+1 (234) 567-{num}",
            "valid_intl": f"+55 11 9{num}",
            "valid_short": "1234567890",
            "min_length": "1234567890",
            "max_length": "+1" + "9" * 20,
            "invalid_empty": "",
            "invalid_letters": "abc-def-ghij",
            "edge_only_plus": "+",
            "edge_special_chars": "+1 (234) 567-8900 ext. 123",
        }
    
    def adult_count(self) -> dict:
        """Adult guest count test data"""
        return {
            "valid_1": "1",
            "valid_2": "2",
            "valid_4": "4",
            "max": "20",
            "invalid_zero": "0",
            "invalid_negative": "-1",
            "invalid_text": "abc",
        }
    
    def child_count(self) -> dict:
        """Child guest count test data"""
        return {
            "valid_0": "0",
            "valid_1": "1",
            "valid_3": "3",
            "max": "10",
            "invalid_negative": "-1",
            "invalid_text": "abc",
        }
    
    def pet_count(self) -> dict:
        """Pet count test data"""
        return {
            "valid_0": "0",
            "valid_1": "1",
            "valid_2": "2",
            "max": "5",
            "invalid_negative": "-1",
            "invalid_text": "abc",
        }
    
    def notes(self, context: str = "lead") -> dict:
        """Notes/comments test data"""
        return {
            "valid_short": f"Short {context} note",
            "valid_medium": f"This is a test note for {context}. It has multiple sentences.",
            "valid_long": f"Long {context} note. " * 50,
            "min_length": "A",
            "max_length": "A" * 10000,
            "invalid_empty": "",
            "edge_special": "Note with $pecial ch@rs!",
            "edge_unicode": "Nota com acentuação: São Paulo",
            "edge_newlines": "Line 1\nLine 2\nLine 3",
        }
    
    def date_checkin(self, days_from_now: int = 1) -> str:
        """Check-in date (tomorrow by default)"""
        date = datetime.now() + timedelta(days=days_from_now)
        return date.strftime("%d/%m/%Y")
    
    def date_checkout(self, days_from_now: int = 3) -> str:
        """Check-out date (3 days from now by default)"""
        date = datetime.now() + timedelta(days=days_from_now)
        return date.strftime("%d/%m/%Y")
    
    def date_invalid(self) -> dict:
        """Invalid date formats"""
        return {
            "invalid_empty": "",
            "invalid_format": "2025-01-15",
            "invalid_text": "tomorrow",
            "invalid_past": "01/01/2020",
            "edge_far_future": "31/12/2099",
        }
    
    # UTILITY METHODS
    
    def get_valid_property_data(self) -> dict:
        """Complete set of valid property data"""
        return {
            "propertyName": self.property_name()["valid"],
            "propertySize": self.property_size()["valid_medium"],
            "addressLine1": self.address_line1()["valid"],
            "city": self.city()["valid"],
            "zipCode": self.zip_code()["valid_us"],
            "state": self.state()["valid"],
            "countryCode": self.country_code()["valid_us"],
            "baseGuests": self.base_guests()["valid_small"],
            "maxGuests": self.max_guests()["valid_medium"],
            "nightlyBasePrice": self.nightly_price()["valid_medium"],
            "currency": self.currency()["valid_usd"],
        }
    
    def get_valid_lead_data(self, property_name: str = None) -> dict:
        """Complete set of valid lead data"""
        guest_first = self.first_name()["valid"]
        guest_last = self.last_name()["valid"]
        guest_full = f"{guest_first} {guest_last}"
        guest_email = self.email()["valid"]
        
        return {
            "lead": guest_full,
            "firstName": guest_first,
            "lastName": guest_last,
            "email": guest_email,
            "phone": self.phone()["valid_us"],
            "propertyName": property_name,
            "checkinDate": self.date_checkin(1),
            "checkoutDate": self.date_checkout(3),
            "adultCount": self.adult_count()["valid_2"],
            "childCount": self.child_count()["valid_0"],
            "petCount": self.pet_count()["valid_0"],
            "notes": self.notes("lead")["valid_medium"],
        }


# Example usage
if __name__ == "__main__":
    data = FieldData()
    
    print("="*70)
    print("FIELD DATA - Examples")
    print("="*70)
    
    print("\nValid Property Data:")
    prop_data = data.get_valid_property_data()
    for key, value in prop_data.items():
        print(f"  {key}: {value}")
    
    print("\nValid Lead Data:")
    lead_data = data.get_valid_lead_data("TestProperty_abc123")
    for key, value in lead_data.items():
        print(f"  {key}: {value}")
    
    print("\nProperty Name Variations:")
    for key, value in data.property_name().items():
        print(f"  {key}: {value}")
    
    print("\nEmail Variations:")
    for key, value in data.email().items():
        print(f"  {key}: {value}")
