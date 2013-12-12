#
# Algorithms for parsing network device outputs into NetworkX graph
# data structures, which is more useful for analysis and generating
# drawings from the graph structures.
#
# Author: Greg Stilwell
# Date: 2013-07-05
#

# TODO: parse OSPF db from Cisco IOS
# TODO: parse IS-IS db from Juniper JunOS
# TODO: parse OSPF db from Juniper JunOS
# TODO: figure a method to discover physical topology by network crawl

# NetworkX provides graph data structures and algorithms for graph analysis
import networkx as nx
# Regular expressions
import re
# Using permutations to mesh pseudonode topologies
from itertools import permutations
# For adding a timestamp (current time) as a graph attribute
import time


def isis_db_to_digraph(db, region='unknown', timestamp=''):
    """ Parse all IS adjacencies from a complete output of Cisco IOS
     'show isis database detail' into a NetworkX DiGraph structure,
      and return the DiGraph."""
    gr = nx.DiGraph()
    # Embed information about the topology within the graph
    gr.graph['type'] = "IS-IS"
    if timestamp == '':
        gr.graph['timestamp'] = time.time() # seconds since the epoch
    else:
        gr.graph['timestamp'] = timestamp # seconds since the epoch
    gr.graph['region'] = region # geographic location, e.g. 'EU'
    # Regex to find start of an IS-IS LSP fragment
    lsp = re.compile('^[0-9A-Za-z].*[0-9a-fA-F]{2}-[0-9a-fA-F]{2}')
    # Regex to find IS adjacency
    adj = re.compile('^.*Metric:.*IS')
    # Edges from DIS pseudonodes have metric=0 (bogus); keeping track of
    # these so we can go back and fix the metrics and topologies when
    # we collapse DIS/pseudonode(s) back into a single node.
    # structure: {(node, nsel):[metric, [adjacent_nodes]], ...}
    pnodes = {}
    # db needs to be a list
    if type(db) == type('string'):
        db = db.split('\n')
    for line in db:
        line.replace('\r', '')
        line.replace('\n', '')
        if lsp.match(line):
            # lsp_name example: "MXP01.00-00", i.e. <node>.<nselNN>-<fragFF>
            lsp_name = line.split(' ')[0]
            # Can use simple text slicing because .nsel-frag is fixed length
            node_a = lsp_name[0:-6]
            node_a = node_a.upper()
            nsel_a = lsp_name[-5:-3]
            if (nsel_a != '00') and (not pnodes.get((node_a, nsel_a))):
                pnodes[(node_a, nsel_a)] = [0, []]
        if adj.match(line):
            adj_tmp = line.split(' ')
            metric = adj_tmp[adj_tmp.index('Metric:') + 1]
            metric = int(metric)
            node_z = adj_tmp[-1][0:-4]
            node_z = node_z.upper()
            nsel_z = adj_tmp[-1][-3:-1]
            if (nsel_z != '00') and (not pnodes.get((node_z, nsel_z))):
                pnodes[(node_z, nsel_z)] = [0, []]
            # When node is a DIS, we need to remember the metric to its own
            # pseudonode (nsel != 00), because the pseudonode LSP has
            # metric=0 to adjacent nodes.  We need to fix these later when
            # we collapse pseudonodes into their parent nodes, so the metrics
            # will look sensible.
            if (node_a == node_z) and (nsel_z != '00'):
                pnodes[(node_z, nsel_z)][0] = metric
            if node_a != node_z:
                # Track bogus metric=0 edges, don't add to graph yet
                if metric == 0:
                    pnodes[(node_a, nsel_a)][1].append(node_z)
                # otherwise add as normal
                else:
                    gr.add_edge(node_a, node_z, Weight = metric)
    # We have the entire database, can now fix the bogus metric=0 pseudonode
    # edges.  Also mesh adjacent non-DIS nodes to prevent false SPOF alarms
    # because DIS/pseudonode topology is a star with DIS at the center.
    for (node, nsel) in pnodes:
        metric = pnodes[(node, nsel)][0]
        adj_nodes = pnodes[(node, nsel)][1]
        adj_nodes.append(node)
        mesh = list(permutations(adj_nodes, 2))
        for edge in mesh:
            if edge[0] == node:
                gr.add_edge(edge[0], edge[1], Weight = metric)
            # Uncomment these 3 lines to full-mesh the pseudonode topologies:
#             else:
#                 reverse_metric = gr[edge[0]][node]['Weight']
#                 gr.add_edge(edge[0], edge[1], Weight = reverse_metric) 
    return gr
