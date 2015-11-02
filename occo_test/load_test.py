### Copyright 2014, MTA SZTAKI, www.sztaki.hu
###
### Licensed under the Apache License, Version 2.0 (the "License");
### you may not use this file except in compliance with the License.
### You may obtain a copy of the License at
###
###    http://www.apache.org/licenses/LICENSE-2.0
###
### Unless required by applicable law or agreed to in writing, software
### distributed under the License is distributed on an "AS IS" BASIS,
### WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
### See the License for the specific language governing permissions and
### limitations under the License.
import unittest
import occo.compiler as compiler
import yaml
import occo.util as util

def gen_case_load_dict(infra_desc):
    def test(self):
        statd = compiler.StaticDescription(infra_desc)
        self.assertEqual(yaml.load(str(statd.topological_order)),
                         infra_desc['expected_output'])
    return test
def gen_case_load_str(infra_desc):
    infra_description = yaml.dump(infra_desc)
    def test(self):
        statd = compiler.StaticDescription(infra_description)
        self.assertEqual(yaml.load(str(statd.topological_order)),
                         infra_desc['expected_output'])
    return test

class CompilerTest(unittest.TestCase):
    pass

with open(util.rel_to_file('test-config.yaml')) as f:
    config = yaml.load(f)
for isdesc in config['infrastructures']:
    setattr(CompilerTest, 'test_load_dict_{0[name]}'.format(isdesc),
            gen_case_load_dict(isdesc))
    setattr(CompilerTest, 'test_load_str_{0[name]}'.format(isdesc),
            gen_case_load_str(isdesc))
