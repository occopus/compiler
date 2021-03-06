from occo.resourcehandler import RHSchemaChecker
from occo.configmanager import CMSchemaChecker
from occo.exceptions import SchemaError
from occo.infraprocessor.node_resolution import ContextSchemaChecker
from occo.infraprocessor.synchronization import HCSchemaChecker
import importlib

import re
def is_valid_hostname(hostname):
    if "." in hostname:
        return "cannot contain \'.\' character"
    if len(hostname) > 64:
        return "is too long"
    allowed = re.compile(r"[a-z0-9-]{1,63}$", re.IGNORECASE)
    if not allowed.match(hostname):
        return "may contain only [a-z,0-9,-] characters"
    return None

class SchemaChecker(object):
    @staticmethod
    def check_infra_desc(infra_desc):
        import logging
        log = logging.getLogger('occo')

        keys = list(infra_desc.keys())
        if 'user_id' not in keys:
            log.warning("[SchemaCheck] WARNING: user_id is not defined in infrastructure description")
        if 'infra_name' not in keys:
            raise SchemaError("[SchemaCheck] ERROR: infra_name must be defined in infrastructure description")
        error = is_valid_hostname(infra_desc['infra_name'])
        if error:
            raise SchemaError("[SchemaCheck] ERROR: infra_name \"{0}\" {1}".format(infra_desc['infra_name'],str(error)))
        if 'nodes' not in keys:
            raise SchemaError("[SchemaCheck] ERROR: nodes section must be defined in infrastructure description")
        for node in infra_desc['nodes']:
            nodekeys = list(node.keys())
            if 'name' not in nodekeys:
                raise SchemaError("[SchemaCheck] ERROR: missing key \"name\" in node")
            error = is_valid_hostname(node['name'])
            if error:
                raise SchemaError("[SchemaCheck] ERROR: node \"{0}\" {1}".format(node['name'],str(error)))
            if 'type' not in nodekeys:
                raise SchemaError("[SchemaCheck] ERROR: missing key \"type\" in node %r" % node['name'])
            if 'scaling' not in nodekeys:
                log.warning("[SchemaCheck] WARNING: missing \"scaling\" parameter in node %r, using default scaling (single instance)",node['name'])
            else:
                for key in node['scaling']:
                    if key not in ['min', 'max']:
                        raise SchemaError("[SchemaCheck] ERROR: unknown key \"%r\" in scaling of node %r" % (key, node['name']))
            if 'filter' in nodekeys and not isinstance(node['filter'], dict):
                raise SchemaError("[SchemaCheck] ERROR: unknown type of filter in node %r - has to be a dict!" % node['name'])
            for key in nodekeys:
                if key not in ['name', 'type', 'scaling', 'filter', 'variables']:
                    raise SchemaError("[SchemaCheck] ERROR: unknown key \"%r\" in node %r" % (key, node['name']))
        if 'dependencies' not in keys:
            log.warning("[SchemaCheck] WARNING: no dependencies specified - using sequential ordering")
        else:
            for dep in infra_desc['dependencies']:
                if isinstance(dep, dict):
                    depkeys = list(dep.keys())
                    if 'connection' not in depkeys:
                        raise SchemaError("[SchemaCheck] ERROR: undefined connection ")
        for key in keys:
            if key not in ['user_id', 'infra_name', 'nodes', 'dependencies', 'variables']:
                raise SchemaError("[SchemaCheck] ERROR: unknown key %r in infastructure description" % key)
    
    @staticmethod
    def check_node_def(node_defs):
        for nodename, node_def in list(node_defs.items()):
            if ':' not in nodename or nodename.split(':', 1)[0] != 'node_def':
                context = "[SchemaCheck] ERROR in node %r: " % nodename
                msg = "Node definition must begin with 'node_def:<nodename>'!"
                raise SchemaError(msg, context)
            realnodename = nodename.split(':', 1)[1]
            if type(node_def) != list:
                context = "[SchemaCheck] ERROR in node %r: " % realnodename
                msg = "Node definition has to be a list of dictionaries!"
                raise SchemaError(msg, context)
            for node in node_def:
                #check for invalid sections:
                for key in node:
                    if key not in ["resource", "config_management",
                            "contextualisation", "health_check"]:
                        context = "[SchemaCheck] ERROR in node %r: " % realnodename
                        msg = "Invalid section %r" % key
                        raise SchemaError(msg, context)
                nodeindex = node_def.index(node)
                #resource section
                try:
                    if 'resource' not in node:
                        raise SchemaError("Missing 'resource' section!")
                    else:
                        resource = node['resource']
                        if 'type' not in resource:
                            raise SchemaError("Missing key \'type\'")
                        else:
                            protocol = resource['type']
                            libname = "occo.plugins.resourcehandler." + protocol
                            importlib.import_module(libname)
                            checker = RHSchemaChecker.instantiate(protocol=protocol)
                            checker.perform_check(resource)
                except SchemaError as e:
                    context = "[SchemaCheck] ERROR in 'resource' section of node %r[%d]: " % (realnodename, nodeindex)
                    raise SchemaError(e.msg, context)
                #config_manager section
                try:
                    if 'config_management' in node:
                        cm = node['config_management']
                        if 'type' not in cm:
                            raise SchemaError("Missing key \'type\'!")
                        else:
                            protocol = cm['type']
                            libname = "occo.plugins.configmanager." + protocol
                            importlib.import_module(libname)
                            checker = CMSchemaChecker.instantiate(protocol=protocol)
                            checker.perform_check(cm)
                except SchemaError as e:
                    context = "[SchemaCheck] ERROR in 'config_management' section of node %r[%d]: " % (realnodename, nodeindex)
                    raise SchemaError(e.msg, context)
                
                #contextualization section
                try:
                    if 'contextualisation' in node:
                        cont = node['contextualisation']
                        if 'type' not in cont:
                            raise SchemaError("Missing key \'type\'!")
                        else:
                            protocol = cont['type']
                            libname = "occo.plugins.infraprocessor.node_resolution." + protocol
                            importlib.import_module(libname)
                            checker = ContextSchemaChecker.instantiate(protocol=protocol)
                            checker.perform_check(cont)
                except SchemaError as e:
                    context = "[SchemaCheck] ERROR in 'contextualisation' section of node %r[%d]: " % (realnodename, nodeindex)
                    raise SchemaError(e.msg, context)
                        
                #health_check section
                try:
                    if 'health_check' in node:
                        hc = node['health_check']
                        if 'type' not in hc:
                            hc['type'] = 'basic'
                        if hc['type'] == 'basic':
                            libname = "occo.infraprocessor.synchronization"
                        else:
                            libname = "occo.infraprocessor.synchronization." + hc['type']
                        importlib.import_module(libname)
                        checker = HCSchemaChecker.instantiate(protocol=hc['type'])
                        checker.perform_check(hc)
                except SchemaError as e:
                    context = "[SchemaCheck] ERROR in 'health_check' section of node %r[%d]: " % (realnodename, nodeindex)
                    raise SchemaError(e.msg, context)
