from occo.resourcehandler import RHSchemaChecker
from occo.configmanager import CMSchemaChecker
from occo.exceptions import SchemaError
from occo.infraprocessor.node_resolution import ContextSchemaChecker
import importlib

class SchemaChecker(object):
    @staticmethod
    def check_infra_desc(infra_desc):
        print "check_infra\n"

    @staticmethod
    def check_nodes(nodes):
        print "check_nodes\n"
    
    @staticmethod
    def check_node_def(node_defs):
        for nodename, node_def in node_defs.iteritems():
            for node in node_def:
                nodeindex = node_def.index(node)
                #resource section
                try:
                    if 'resource' not in node:
                        raise SchemaError("missing RESOURCE section")
                    else:
                        resource = node['resource']
                        if 'type' not in resource:
                            raise SchemaError("missing key \'type\'")
                        else:
                            protocol = resource['type']
                            libname = "occo.plugins.resourcehandler." + protocol
                            importlib.import_module(libname)
                            checker = RHSchemaChecker.instantiate(protocol=protocol)
                            checker.perform_check(resource)
                except SchemaError as e:
                    context = "[SCHEMA] ERROR in resource section of node %r[%d] - " % (nodename, nodeindex)
                    raise SchemaError(e.msg, context)
                #config_manager section
                try:
                    if 'config_management' in node:
                        cm = node['config_management']
                        if 'type' not in cm:
                            raise SchemaError("missing key \'type\'")
                        else:
                            protocol = resource['type']
                            libname = "occo.plugins.configmanager." + protocol
                            importlib.import_module(libname)
                            checker = CMSchemaChecker.instantiate(protocol=protocol)
                            checker.perform_check(cm)
                except SchemaError as e:
                    context = "[SCHEMA] ERROR in config_management section of node %r[%d] - " % (nodename, nodeindex)
                    raise SchemaError(e.msg, context)
                
                #contextualization section
                try:
                    if 'contextualization' in node:
                        cont = node['contextualization']
                        if 'type' not in cont:
                            raise SchemaError("missing key \'type\'")
                        else:
                            protocol = cont['type']
                            libname = "occo.plugins.infraprocessor.node_resolution." + protocol
                            importlib.import_module(libname)
                            checker = ContextSchemaChecker.instantiate(protocol=protocol)
                            checker.perform_check(cont)
                except SchemaError as e:
                    context = "[SCHEMA] ERROR in contextualization section of node %r[%d] - " % (nodename, nodeindex)
                    raise SchemaError(e.msg, context)
                        
                #health_check section
