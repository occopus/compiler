#!/usr/bin/env python

import unittest
import occo.compiler as compiler
import yaml

class CompilerTest(unittest.TestCase):
    def setUp(self):
        self.testcfg = open('test-config.yaml')
        self.TEST_INFRA_ASCII='[A]\n[B, C]\n[D]'
        self.mapping = yaml.load(self.testcfg)['infrastructure']
    def test_load_dict(self):
        topo_order = compiler.load(self.mapping)
        self.assertEqual(str(topo_order), self.TEST_INFRA_ASCII)
    def test_load_str(self):
        infra_description = yaml.dump(self.mapping)
        topo_order = compiler.load(infra_description)
        self.assertEqual(str(topo_order), self.TEST_INFRA_ASCII)

class CompilerTestSuite(unittest.TestSuite):
    def __init__(self):
        unittest.TestSuite.__init__(
            self, map(CompilerTest, ['test_load_dict',
                                     'test_load_str']))

if __name__ == '__main__':
    alltests = unittest.TestSuite([CompilerTestSuite(),
                                   ])
    unittest.main()
