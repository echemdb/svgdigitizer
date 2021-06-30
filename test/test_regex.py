import unittest
import re
from svgdigitizer.svgdigitizer import ref_point_regex_str, scalebar_regex_str, scaling_factor_regex_str


class RegexTest(unittest.TestCase):

    def testPointRegex(self):
        test_cases = [
            {'test_string': 'x1: 1 µA cm⁻²',
            'point group': 'x1',
            'value group': '1',
            'unit group': 'µA cm⁻²',
            },
            {'test_string': 'x1:1µA cm⁻²',
            'point group': 'x1',
            'value group': '1',
            'unit group': 'µA cm⁻²',
            },
        ]  
        for test_case in test_cases:
            match = re.match(ref_point_regex_str, test_case['test_string'])
            self.assertEqual(match.group('point'), test_case['point group'])
            self.assertEqual(match.group('value'), test_case['value group'])
            self.assertEqual(match.group('unit'), test_case['unit group'])
    
    def testScaleBarRegex(self):
        test_cases = [
            {'test_string': 'y_scalebar: 50.6 µA cm⁻²',
            'value group': '50.6',
            'unit group': 'µA cm⁻²',
            },
            {'test_string': 'ysb: 50.6 µA cm⁻²',
            'value group': '50.6',
            'unit group': 'µA cm⁻²',
            },
        ]  
        for test_case in test_cases:
            match = re.match(scalebar_regex_str, test_case['test_string'])
            self.assertEqual(match.group('value'), test_case['value group'])
            self.assertEqual(match.group('unit'), test_case['unit group'])

    def testScalingFactor(self):
        test_cases = [
            {'test_string': 'y_scaling_factor: 50.6',
            'value group': '50.6',
            },
            {'test_string': 'ysf: 50.6',
            'value group': '50.6',
            },
        ]  
        for test_case in test_cases:
            match = re.match(scaling_factor_regex_str, test_case['test_string'])
            self.assertEqual(match.group('value'), test_case['value group'])


if __name__ == "__main__": 
    unittest.main()
