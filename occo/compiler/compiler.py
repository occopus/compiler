#
# Copyright (C) 2014 MTA SZTAKI
#

"""Compiler module for the OCCO service.

.. moduleauthor:: Adam Visegradi <adam.visegradi@sztaki.mta.hu>

This module provides a compiler that generates a node grouping based on the
topologial order of the infrastructure graph.

Each group pertains to a topological level of the graph; that is, it contains no
dependencies among its nodes. These nodes may be processed in parallel.

The list of groups returned by the compiler represents the topological
dependendencies in the infrastructure. Groups must be processed in sequence,
without parallelization.

The compiler may provide other services in the future, for example:
  - Resolving all references in the descriptions (e.g. node type), recursively,
    validating them early.
  - Pre-resolving everything. This would imply that the Infrastructure
    Processor will not need to do so, and that the descriptions become frozen
    for this infrastructure instance immediately upon instantiation. (Late
    resolution in the Infrastructure Processor may lead to inconsistency if the
    user is allowed to change the descriptions while the infrastructure is
    running.  However, freezing would make updating a running infrastructure
    more challenging.

.. todo:: We haven't thought through *updating* nodes in a running
    infrastructure. For starters, there is no :term:`IP` command for that.

.. todo:: Move exceptions to a dedicated exception module.

.. ifconfig:: api_doc is False

    .. autofunction:: altcall
    .. autofunction:: create_mapping
    .. autoclass:: Edge
        :members:
    .. autoclass:: TopoLevel
        :members:
    .. autoclass:: TopologicalOrder
        :members:
"""

__all__ = ['StaticDescription', 'SchemaError']

import yaml
import uuid
import occo.util as util
from occo.exceptions import SchemaError

def altcall(target, data):
    """
    Allows alternative calling of a function/method.

    The parameter can either be a dictionary or another object. If a dictionary
    is specified, it will be used as parameters (``**``). If anything else is
    specified, it will be used as the sole positional argument for the
    method..

    This only works with methods having the following signature:

    ``foo( self, mandatory [ , optional_1=X [ , optional_2=Y [ ... ] ] ] [ , **kwargs ] )``

    ---Where ``mandatory`` *must not be* a dictionary.

    Using this, configuration can omit a dictionary specification, if only the
    mandatory argument is to be specified. E.g.:

    .. code-block:: yaml

        # Instead of this:
        obj:
            mandatory: 1

        # Only this:
        obj: 1

    """
    if type(data) is dict:
        return target(**data)
    else:
        return target(data)

def create_mapping(attributes, synch=False, **kwargs):
    """
    Creates an attribute mapping between nodes; excluding node references.

    That is, a complete mapping between two nodes can be described with a
    triplet of (``Node``, ``Node``, ``Mapping``).

    :param attributes: The two attributes to be connected.
    :type attributes: Pair (:class:`list` or :func:`tuple` of two :class:`str`\
        s).
    :param bool synch: The InfraProcessor should synchronize on this attribute
        (wait for the upstream node to export this attribute).
    :param ** kwargs: Arbitrary information that can be used by mediating
        services (InfraProcessor, node Resolver, etc.)
    """
    retval = dict(attributes=attributes, synch=synch)
    retval.update(kwargs)
    return retval

class Edge(object):
    """Represents an edge of the infrastructure graph.

    :param connection: The two nodes connected.
    :type connection: Pair (:class:`list` or :func:`tuple` of two nodes).
    :param mappings: The attribute mappings between the nodes.
    :param ** kwargs: Arbitrary information that can be used by mediating
        services (InfraProcessor, node Resolver, etc.)
    """
    def __init__(self, connection, mappings=[], **kwargs):
        self.__dependent, self.__dependee = connection
        self.__mappings = mappings
        self.__dict__.update(kwargs)
    @property
    def dependent(self):
        """The node that depends on the other."""
        return self.__dependent
    @property
    def dependee(self):
        """The node that is depended on by the other."""
        return self.__dependee
    @property
    def mappings(self):
        """Attribute mappings between vertices."""
        return self.__mappings

class TopoLevel(list):
    """Represents a topological level of the dependency graph.

    Although it's implemented as a :class:`list`, the order of its items is
    irrelevant. A :class:`list` is used instead of a :class:`set` because
    insertion and iteration are faster, while only those two are used
    (:class:`set` operations are not).

    .. automethod:: __str__
    """

    def __str__(self):
        """ Format the object as string.

        This function is used for development only (debugging, logging,
        testing), other components do not depend on it.

        The format of the output can be parsed as YAML, and it will yield a
        *set* (cf. the class documentation). The reason for this is that it
        makes unit testing easier, because :meth:`set.__eq__` is oblivious to
        the order of elements.

        .. todo:: Use str.format instead of %
        """
        return '- !!set\n%s'%('\n'.join('  ? %s'%n['name'] for n in self))

class TopologicalOrder(list):
    """Represents the topological ordering of nodes.

    This is a list of topological levels (:class:`TopoLevel`), in order. The
    nodes in the first group do not depend on anything. Successive levels
    depend on the the preceding one.

    .. automethod:: __str__
    """
    def add_level(self, level):
        """ Add a node to the topological level. """
        # Although currently just a proxy for list.append(), this abstraction
        # makes changing the implementation of TopoLevel possible.
        self.append(level)

    def __str__(self):
        """ Format the object as string.

        This function is used for development only (debugging, logging,
        testing), other components do not depend on it.
        """
        return '\n'.join(str(i) for i in self)

class StaticDescription(object):
    """Represents a statical description of an infrastructure.

    :param infrastructure_description: The description of the infrastructure.
        This can either be a YAML string, which will be parsed, or an already
        parsed data structure (:class:`dict`). See :ref:`infradescription` for
        details.

    :raises SchemaError: if the schema is invalid.
    :raises KeyError: if the schema is invalid, until :meth:`schema_check` is
        implemented.

    .. todo:: Implement :meth:`schema_check` and remove the ``:raises:``
        clause about :exc:`ValueError`.

    :var infra_id: The unique identifier of the infrastructure, implicitly
        generated.
    :var name: The name of the infrastructure
    :var nodes: Unordered list of all nodes.
    :var node_lookup: Lookup table for nodes based on their names.
    :var dependencies: Unordered list of edges.
    :var topological_order: The topological ordering of the graph; see
        :class:`TopologicalOrder` and method :meth:`topo_order`.

    .. todo:: The ``infra_id`` may be predefined?
    """
    def __init__(self, infrastructure_description):
        # Deserialize description if necessary
        desc = infrastructure_description \
            if type(infrastructure_description) is dict \
            else yaml.load(infrastructure_description)

        StaticDescription.schema_check(desc)

        self.infra_id = str(uuid.uuid4())
        self.name = desc['name']
        self.nodes = desc['nodes']

        self.node_lookup = dict((n['name'], n) for n in self.nodes)
        self.dependencies = desc['dependencies']
        self.edges = [altcall(Edge, e) for e in self.dependencies]
        self.topological_order = \
            StaticDescription.topo_order(self.nodes, self.edges)
        self.prepare_nodes(desc)
        self.user_id = desc['user_id']
        self.variables = desc.get('variables', dict())

    def prepare_nodes(self, desc):
        """
        Sets up node descriptions.

        Upon instantiating the infrastructure, instantiated node descriptions
        inherit some of the information from the infrastructure description:

            - authentication information (``user_id``)
            - identifier of the instantiated infrastructure (``infra_id`` -->
                ``environment_id``.
            - variables (node description variables are kept intact)
            - attribute mappings

        The resulting node description should be completely self-contained.

        """

        for i in self.nodes:
            i['environment_id'] = self.infra_id # Foreign key, if you like

            # Variables inherited from the infrastructure
            # Variables specified in the node description are preferred
            i['variables'] = util.dict_merge(desc.get('variables', dict()),
                                             i.get('variables', dict()))

            # Copying the user_id into all nodes' descriptions is an
            # optimization, so IP::CreateNode does not need to resolve the
            # containing infrastructure's static description.
            i['user_id'] = desc['user_id']

            # Setup attribute mappings based on infrastructure description
            i['mappings'] = self.merge_mappings(i)

    def merge_mappings(self, node):
        inbound, outbound = dict(), dict()
        for e in self.edges:
            if e.dependee is node:
                dest, key = outbound, e.dependent['name']
            elif e.dependent is node:
                dest, key = inbound, e.dependee['name']
            else:
                continue

            dest[key] = [altcall(create_mapping, m) for m in e.mappings]
        return dict(inbound=inbound, outbound=outbound)

    @staticmethod
    def schema_check(infrastructure_description):
        """This function will validate the infrastructure description upon
        creating this object.

        :raises SchemaError: if the schema is invalid.

        .. todo:: implement schema checking.
        """
        pass

    @staticmethod
    def topo_order(all_nodes, all_edges):
        """Creates a topological ordering based on the list of nodes and
        the list of edges.

        .. todo:: Using generators instead of lists  (``(...for...)`` instead
            ``[...for...]``) in the generating phase should be more
            memory-efficient. Should try it and use it if it works.
        """

        # Create representation suitable for topological ordering
        ## List of nodes
        nodes = all_nodes
        ## Convert pairs to Edges
        edges = all_edges

        # Return value:
        topo_order = TopologicalOrder()

        # Move all nodes into topo_order, level by level
        while nodes:
            # Negative logic: we need all independent nodes, but it needs
            # calculating a NotExists quantifier, which is always inefficient.
            # So:
            ## All nodes that _do_ depend on _something_
            dependents = [i.dependent for i in edges]
            ## Now it's simple: independent = all \ dependent
            ## These nodes constitute a topological level
            topo_level = TopoLevel(n for n in nodes if not n in dependents)

            # Remove nodes that were put in this topological level, as now they
            # are satisfied dependencies.
            nodes = [n for n in nodes if not n in topo_level]
            # Remove half edges (edges connected with nodes just removed).
            edges = [e for e in edges if not e.dependee in topo_level]

            # Add to output
            topo_order.add_level(topo_level)

        # Done
        return topo_order
