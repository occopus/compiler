#!/usr/bin/env python

import unittest
import occo.compiler as compiler
import yaml

def gen_test_load_dict(infra_desc):
    def test(self):
        statd = compiler.StaticDescription(infra_desc)
        self.assertEqual(yaml.load(str(statd.topological_order)),
                         infra_desc['expected_output'])
    return test
def gen_test_load_str(infra_desc):
    infra_description = yaml.dump(infra_desc)
    def test(self):
        statd = compiler.StaticDescription(infra_description)
        self.assertEqual(yaml.load(str(statd.topological_order)),
                         infra_desc['expected_output'])
    return test

class CompilerTest(unittest.TestCase):
    pass

with open('test-config.yaml') as f:
    config = yaml.load(f)
for isdesc in config['infrastructures']:
    setattr(CompilerTest, 'test_load_dict_%s'%isdesc['name'],
            gen_test_load_dict(isdesc))
    setattr(CompilerTest, 'test_load_str_%s'%isdesc['name'],
            gen_test_load_str(isdesc))
