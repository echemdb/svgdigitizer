import unittest
import re
from svgdigitizer.svgdigitizer import ref_point_regex_str, scale_bar_regex_str, scaling_factor_regex_str, curve_regex_str


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
            {'test_string': 'y_scale_bar: 50.6 µA cm⁻²',
            'value group': '50.6',
            'unit group': 'µA cm⁻²',
            },
            {'test_string': 'ysb: 50.6 µA cm⁻²',
            'value group': '50.6',
            'unit group': 'µA cm⁻²',
            },
        ]  
        for test_case in test_cases:
            match = re.match(scale_bar_regex_str, test_case['test_string'])
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
    
    def testCurveRegex(self):
        test_cases = [
            {'test_string': 'curve: the big one',
            'curve_id_group': 'the big one',
            },
            {'test_string': 'curve: black',
            'curve_id_group': 'black',
            },
        ]
        for test_case in test_cases:
            match = re.match(curve_regex_str, test_case['test_string'])
            self.assertEqual(match.group('curve_id'), test_case['curve_id_group'])

if __name__ == "__main__": 
    unittest.main()
