


from django.db.models import Q
from django.test import SimpleTestCase
from dataclasses import dataclass
from bloomerp.filters.lookups import LookupDefinition
from bloomerp.filters.lookups import LOOKUP_REGISTRY

@dataclass
class LookupTestCase:
    lookup:LookupDefinition
    input:dict
    expected:Q
    


class LookupTestCase(SimpleTestCase):
    cases : list[LookupTestCase] = [
        LookupTestCase(
            LOOKUP_REGISTRY.EQUALS,
            {"first_name__equals" : "David"},
            Q(first_name__equals="David")
        ),
        LookupTestCase(
            LOOKUP_REGISTRY.EQUALS,
            {"first_name" : "David"},
            Q(first_name="David")
        ),
        LookupTestCase(
            LOOKUP_REGISTRY.EQUALS,
            {"age" : 10},
            Q(age=10)
        )
    ]
    
    
    def test_lookups(self):
        """
        UC: Equal lookup produces correct query
        
        Expected Result: criteria
        """
        
        for case in self.cases:
            with self.subTest():
                
                field, value = next(iter(case.input.items()))
                
                self.assertEqual(
                    case.lookup.generate_q(field, value),
                    case.expected
                )
        
        

    
        