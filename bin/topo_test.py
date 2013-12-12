from topo_parse import isis_db_to_digraph
from topo_analyze import spofs
from topo_analyze import diff
from topo_draw import draw
import networkx as nx
import time
from sys import stdout, path, argv
from pymongo import MongoClient


def loadfile(testfile):
    time_start = time.clock()
    with open (testfile, "r") as myfile:
        data = myfile.readlines()
    gr = isis_db_to_digraph(data)
    print "Parser execution time:", time.clock() - time_start, "seconds"
    return gr

def ana_spof():
    time_start = time.clock()
    impacts = spofs(gr1)
    print "SPOF nodes:", impacts['spofs']
    print "Impacted nodes:", impacts['isolated']
    print "SPOF Analysis execution time:", time.clock() - time_start, "seconds"

def ana_diff():
    time_start = time.clock()
    changes = diff(gr1, gr2)
    for key in changes:
        if len(changes[key]) > 0:
            print key, changes[key]
    print "Topology diff execution time:", time.clock() - time_start, "seconds"

def topo_draw():
    impacts = spofs(gr1)
#    gr1.remove_node('RST-BAK01')
    changes = diff(gr1, gr2)
    for key in impacts:
        print key, impacts[key]
    for key in changes:
        print key, changes[key]
    time_start = time.clock()
#    draw(gr1, impacts, changes)
#    draw(gr1, impacts, return_svg=True)
    topo_entry = draw(gr1, impacts, save_svg=False, return_svg=True, return_graphml=True)
    print topo_entry['graphml']
    print topo_entry['svg']
#    draw(gr1)
    print "Topology drawing execution time:", time.clock() - time_start, "seconds"



file1 = "2013-06-23-100906-GMT_NA_isis.txt"
file2 = "2012-11-19-153957-EST_NA_isis.txt"
gr1 = loadfile(file1)
gr2 = loadfile(file2)
#print gr1.graph['timestamp']
#print gr1.graph['region']


#ana_spof()
#ana_diff()
topo_draw()
#mongo_save()
#mongo_load()

#graphml = '\n'.join(nx.generate_graphml(gr1))
#print graphml, type(graphml)
#print nx.read_graphml(graphml).nodes()

#gr3 = nx.read_graphml('zzz_test.graphml')
#print gr3.graph['type']
#print time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(gr3.graph['timestamp'])), "GMT"
