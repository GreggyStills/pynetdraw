#
# Algorithms for drawing network topologies (graphs).
#
# Author: Greg Stilwell
# Date: 2013-07-31
#

# TODO: re-factor, code is getting way too long+ugly
# TODO: feature: draw only a subset of the whole network (maybe by regex on node name?)

# PyDot is a Python interface to GraphViz, a nifty set of libraries
# for automatically drawing network topologies (graphs).
import pydot
# For working w/ timestamps in graph attributes
import time
# NetworkX provides graph data structures, algorithms for graph analysis, and
# read/write of graphs in different formats
import networkx as nx


def url_node(node):
    """Takes a node name as input, returns a URL with node name embedded
     in a useful way."""
    url = "http://rst-nms-splunk01.corp.tnsi.com:8000"
    url = url + "/en-US/app/search/flashtimeline?q=search%20"
    url = url + "%s" %node
    url = url + "&earliest=0"
    return url

def draw(gr, impacts={}, changes={},
         return_svg=False, return_graphml=False,
         save_svg=True, save_graphml=False):
    """ Use GraphViz/Dot to draw a topology, optionally highlighting
     elements of interest to ensure they stand out in the diagram."""
    if gr.graph.has_key('type'):
        topo_type = gr.graph['type']  # e.g. 'IS-IS'
    else:
        topo_type = 'unknown'
    if gr.graph.has_key('region'):
        topo_region = gr.graph['region']  # e.g. 'EU'
    else:
        topo_region = 'unknown'
    if gr.graph.has_key('timestamp'):
        topo_time = time.gmtime(gr.graph['timestamp'])
        topo_time = time.strftime("%Y-%m-%d_%H-%M-%S", topo_time) + "_GMT"
    else:
        topo_time = "unknown"
    font_labels = 'Helvetica'
    colors = {}
    colors['main'] = 'lightgray' # root window background
    colors['borders'] = 'lightslategray' # borders around nodes+clusters
    colors['pop'] = 'beige' # cluster/POP background
    colors['node'] = 'linen' # regular node fill color
    # List of normal link colors (cycle through all these colors to vary
    # link colors for ease of tracing individual links)
    colors['links'] = ['midnightblue', 'black', 'saddlebrown', 'purple']
    # We really want the next colors to stand out, to show interesting things: 
    colors['spof'] = 'lightsalmon' # node is a single point of failure
    colors['isolated'] = 'yellow' # node would be isolated by SPOF failure
    colors['removed'] = 'red' # element has been removed since previous topo
    colors['added'] = '#01DF01' # (green) element has been added since previous topo
    #
    # If we got a topology diff, we need to re-add the nodes+edges that are now
    # missing since the previous capture, or they won't be drawn in the current
    # topology diagram.
    if changes.has_key('nodes_removed'):
        for node in changes['nodes_removed']:
            gr.add_node(node)
    if changes.has_key('edges_removed'):
        for edge in changes['edges_removed']:
            gr.add_edge(edge[0], edge[1], weight=1)
    #
    # Use PyDot/GraphViz to draw the topology.  The variable options here
    # (e.g. nodesep) are specified in the Dot language.
    dotgraph = pydot.Dot(
        "IS-IS Topology",
        graph_type='graph',
        bgcolor = colors['main'],
        nodesep = '0.25',
        ratio = '0.25',
        # 'ortho': edges horiz+vert w/ sharp corners, as in a circuit schematic
#        splines = 'ortho',
        rankdir = 'UD',  # UD=up/down, LR=left/right
        center = 'true',
        remincross = 'true',
        # simplify: draw only one edge between connected nodes
        simplify = 'true')
    #
    legend = pydot.Cluster(
        "Legend",
        label = "LEGEND\n" +\
         "Topology: " + topo_type +"\n" +\
         "Region: " + topo_region + "\n" +\
         "Recorded: " + topo_time + " \n\n\
         Note: Except for red (removed) and green (added),\n\
         link colors vary for ease of traceability.\n\n\
         (SPOF: Single Point of Failure)\n\n",
        fontsize = 16,
        parent_graph = dotgraph,
        style = 'filled',
        color = colors['borders'],
        fillcolor = "white")
    if impacts != {}:
        legend.add_node(pydot.Node(
            "Potential\nIsolation",
            style = 'filled',
            fillcolor = colors['isolated']))
        legend.add_node(pydot.Node(
            "Potential\nSPOF",
            style = 'filled',
            fillcolor = colors['spof']))
    if changes != {}:
        legend.add_node(pydot.Node(
            "Added",
            style = 'filled',
            fillcolor = colors['added']))
        legend.add_node(pydot.Node(
            "Removed\n(Failed?)",
            style = 'filled',
            fillcolor = colors['removed']))
    legend.add_node(pydot.Node(
        "Router",
        style = 'filled',
        fillcolor = colors['node']))
    dotgraph.add_subgraph(legend)
    #
    for node in gr.nodes():
        # Assuming the first 3 char's of the node name is the POP/location
        cluster_name = node[0:3]
        # create subgraph for the POP if it's not there already
        if dotgraph.get_subgraph(cluster_name) == []:
            subgr = pydot.Cluster(
                cluster_name,
                parent_graph = dotgraph,
                style = 'rounded',
                label = cluster_name,
                font = font_labels,
                fontsize = '16',
                color = colors['borders'],
                fillcolor = colors['pop'])
        if changes.has_key('nodes_removed') and node in changes['nodes_removed']:
            nodefill = colors['removed']
        elif impacts.has_key('spofs') and node in impacts['spofs']:
            nodefill = colors['spof']
        elif impacts.has_key('isolated') and node in impacts['isolated']:
            nodefill = colors['isolated']
        elif changes.has_key('nodes_added') and node in changes['nodes_added']:
            nodefill = colors['added']
        else:
            nodefill = colors['node']
        subgr.add_node(pydot.Node(
            node,
            URL = url_node(node),
            font = font_labels,
            fontsize = '10',
            style = "filled",
            color = colors['borders'],
            fillcolor = nodefill))
        dotgraph.add_subgraph(subgr)
    xcolor = 0  # link color selector; link colors vary for ease of tracing
    for edge in gr.edges():
        if changes.has_key('edges_removed') and edge in changes['edges_removed']:
            ecolor = colors['removed']
        elif changes.has_key('edges_added') and edge in changes['edges_added']:
            ecolor = colors['added']
        else:
            ecolor = colors['links'][xcolor]
        dotedge = pydot.Edge(edge, color = ecolor)
        dotgraph.add_edge(dotedge)
        xcolor += 1
        if xcolor >= len(colors['links']):
            xcolor = 0
    # We could draw a JPG/GIF/PNG/etc, but:
    # Generating SVG/DOT/XDOT is faster, smaller output, and easier to
    # manipulate on-the-fly for interactivity (e.g. Raphael, canviz).
    topos = {}
    if return_svg:
        topos['svg'] = dotgraph.create(prog='dot', format='svg')
    if return_graphml:
        topos['graphml'] = '\n'.join(nx.generate_graphml(gr))
    if save_svg:
        fname = "%s_%s_%s.svg" % (topo_time, topo_type, topo_region)
        dotgraph.write(fname, prog='dot', format='svg')
    if save_graphml:
        fname = "%s_%s_%s.graphml" % (topo_time, topo_type, topo_region)
        nx.write_graphml(gr, fname)
    return topos

