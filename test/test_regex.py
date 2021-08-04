#*********************************************************************
#  This file is part of svgdigitizer.
#
#        Copyright (C) 2021 Albert Engstfeld
#        Copyright (C) 2021 Johannes Hermann
#        Copyright (C) 2021 Julian Rüth
#        Copyright (C) 2021 Nicolas Hörmann
#
#  svgdigitizer is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  svgdigitizer is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with svgdigitizer. If not, see <https://www.gnu.org/licenses/>.
#*********************************************************************
import unittest
import re
from svgdigitizer.svgplot import label_patterns


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
            match = re.match(label_patterns['ref_point'], test_case['test_string'])
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
            match = re.match(label_patterns['scale_bar'], test_case['test_string'])
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
            match = re.match(label_patterns['scaling_factor'], test_case['test_string'])
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
            match = re.match(label_patterns['curve'], test_case['test_string'])
            self.assertEqual(match.group('curve_id'), test_case['curve_id_group'])

if __name__ == "__main__": 
    unittest.main()
