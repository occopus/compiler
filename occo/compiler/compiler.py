#
# Copyright (C) 2014 MTA SZTAKI
#

__all__ = ['StaticDescription', 'SchemaError']

import yaml
import uuid

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

class StaticDescription(object):
    def __init__(self, infrastructure_description):
        desc = infrastructure_description \
            if type(infrastructure_description) is dict \
            else yaml.load(infrastructure_description)
        StaticDescription.schema_check(desc)
        self.infra_id = str(uuid.uuid4())
        self.name = desc['name']
        self.nodes = desc['nodes']
        self.node_lookup = dict((n['name'], n) for n in self.nodes)
        self.dependencies = desc['dependencies']
        self.topological_order = \
            StaticDescription.topo_order(self.nodes, self.dependencies)

    @staticmethod
    def schema_check(infrastructure_description):
        pass

    @staticmethod
    def topo_order(all_nodes, all_dependencies):
        nodes = all_nodes
        edges = [Edge(*ends) for ends in all_dependencies]
        topo_order = TopologicalOrder()
        while nodes:
            dependents = [i.dependent for i in edges]
            topo_level = TopoLevel([n for n in nodes if not n in dependents])
            edges = [e for e in edges if not e.dependee in topo_level]
            nodes = [n for n in nodes if not n in topo_level]
            topo_order.add_level(topo_level)
        return topo_order
