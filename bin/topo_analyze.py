#
# Algorithms for analyzing network topologies (i.e. graphs, as in Graph Theory).
#
# Author: Greg Stilwell
# Date: 2013-07-05
#

# NetworkX provides graph data structures and algorithms for graph analysis
import networkx as nx

def spofs(gr):
    """Identifies the SPOF nodes (single points of failure) in a topology, and
    the downstream nodes that will be isolated from the majority of the network
    when any of the SPOFs fail.  Takes a NetworkX Graph or DiGraph as input,
    returns a dictionary of two lists:
    1. a list of SPOF nodes (single points of failure)
    2. a list of downstream nodes that will become isolated when SPOFs fail."""
    if type(gr) != type(nx.Graph()):
        gr = gr.to_undirected(gr)
    # structure:
    #  {'spofs':[node1, node2,...,nodeN], 'isolated':[node1, node2,...,nodeN]}
    impacts = {}
    impacts['spofs'] = list(nx.articulation_points(gr))
    impacts['isolated'] = []
    for spof in impacts['spofs']:
        gr_tmp = gr.copy()
        gr_tmp.remove_node(spof)
        ccomp = nx.connected_components(gr_tmp)
        ccomp.sort(key=len)
        for sublist in range(len(ccomp)-1):
            for node in ccomp[sublist]:
                if not node in impacts['isolated']:
                    impacts['isolated'].append(node)      
    return impacts

def diff(gr1, gr2):
    """ A topology 'diff' utility, useful for identifying changes between two
    versions of the same topology, e.g. failures.  Takes two NetworkX Graphs
    or DiGraphs as input (gr1 newest), returns a dictionary of four lists:
    1. a list of nodes added (in gr1, but not in gr2)
    2. a list of nodes removed (not in gr1, but in gr2)
    3. a list of edges added (in gr1, but not in gr2)
    4. a list of edges removed (not in gr1, but in gr2)"""
    def diff_lists(a, b):
        return [aa for aa in a if aa not in b]
    changes = {}
    changes['nodes_added'] = diff_lists(gr1.nodes(), gr2.nodes())
    changes['nodes_removed'] = diff_lists(gr2.nodes(), gr1.nodes())
    changes['edges_added'] = diff_lists(gr1.edges(), gr2.edges())
    changes['edges_removed'] = diff_lists(gr2.edges(), gr1.edges())
    return changes
