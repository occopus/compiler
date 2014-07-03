#
# Copyright (C) 2014 MTA SZTAKI
#

__all__ = ['load', 'SchemaError']

import yaml

class SchemaError(Exception):
    pass

class Edge(object):
    def __init__(self, dependent, dependee):
        self.__dependent = dependent
        self.__dependee = dependee
    @property
    def dependent(self):
       return self.__dependent
    @property
    def dependee(self):
       return self.__dependee

class TopoLevel(list):
    def add_node(self, node):
        self.append(node)
    def __str__(self):
        return '[%s]'%(', '.join(n['name'] for n in self))

class TopologicalOrder(list):
    def add_level(self, level):
        self.append(level)
    def __str__(self):
        return '\n'.join(str(i) for i in self)

def schema_check(infrastructure_description):
    pass

def load(infrastructure_description):
    desc = infrastructure_description \
        if type(infrastructure_description) is dict \
        else yaml.load(infrastructure_description)
    schema_check(infrastructure_description)

    nodes = desc['nodes']
    edges = [Edge(*ends) for ends in desc['dependencies']]
    topo_order = TopologicalOrder()
    while nodes:
        dependents = [i.dependent for i in edges]
        topo_level = TopoLevel([n for n in nodes if not n in dependents])
        edges = [e for e in edges if not e.dependee in topo_level]
        nodes = [n for n in nodes if not n in topo_level]
        topo_order.add_level(topo_level)
    return topo_order 

    
