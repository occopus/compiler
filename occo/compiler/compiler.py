#
# Copyright (C) 2014 MTA SZTAKI
#

"""Compiler module for the OCCO service.

This module provides a compiler that generates a node grouping based on the
topologial order of the infrastructure graph.

Each group pertains to a topological level of the graph; that is, it contains no
dependencies among its nodes. These nodes can be processed in parallel when
possible.

The list of groups returned by the compiler represents the topological
dependendencies in the infrastructure. Groups must be processed in sequence,
without parallelization.
"""

__all__ = ['StaticDescription', 'SchemaError']

import yaml
import uuid

class SchemaError(Exception):
    """Exception representing a schema error in the input data."""
    pass

class Edge(object):
    """Represents an edge of the infrastructure graph."""
    def __init__(self, dependent, dependee):
        self.__dependent = dependent
        self.__dependee = dependee
    @property
    def dependent(self):
        """The node that depends on the other."""
        return self.__dependent
    @property
    def dependee(self):
        """The node that is depended on by the other."""
        return self.__dependee

class TopoLevel(list):
    """Represents a topological level.

    Although being technically a list, the order of its items is irrelevant."""
    def add_node(self, node):
        self.append(node)
    def __str__(self):
        return '- !!set\n%s'%('\n'.join('  ? %s'%n['name'] for n in self))

class TopologicalOrder(list):
    """Represents the topological ordering of nodes.

    This is a list of topological levels, in order. The nodes in the first
    group do not depend on anything."""
    def add_level(self, level):
        self.append(level)
    def __str__(self):
        return '\n'.join(str(i) for i in self)

class StaticDescription(object):
    """Represents a statical description of an infrastructure.

    Attributes: #TODO: properties
    - infra_id: the unique identifier of the infrastructure,
                implicitly generated #TODO: possibly specified id
    - name:     the name of the infrastructure
    - nodes:    list of all nodes (order irrelevant)
    - node_lookup:
                lookup table for nodes; the keys are their names
    - dependencies:
                list of edges
    - topological_order:
                the topological ordering of the graph; see TopologicalOrder
                and method topo_order
    """
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
        """This function will validate the infrastructure description upon
        creating this object.

        If the schema is invalid, it will be signaled by raising a
        SchemaError exception.

        TODO: implement schema checking."""
        pass

    @staticmethod
    def topo_order(all_nodes, all_dependencies):
        """Creates a topological ordering based on the list of nodes and
        the list of edges."""
        # Create representation suitable for topological ordering
        nodes = all_nodes
        edges = [Edge(*ends) for ends in all_dependencies]
        # Return value:
        topo_order = TopologicalOrder()
        # Move all nodes into topo_order, level by level
        while nodes:
            # All nodes that depend on something
            dependents = [i.dependent for i in edges]
            # All nodes that do *not* depend on anything (nodes\dependents)
            # These nodes constitute a topological level
            topo_level = TopoLevel([n for n in nodes if not n in dependents])
            # Remove nodes that were put in topo_level, as now they are
            # satisfied dependencies.
            nodes = [n for n in nodes if not n in topo_level]
            # Remove edges connected with nodes just removed.
            edges = [e for e in edges if not e.dependee in topo_level]

            topo_order.add_level(topo_level)
        return topo_order
