#!/usr/bin/env python
#
# Script to login to one router per region, generate an SVG diagram of
# each region's IS-IS topology, and upload the topologies as both
# SVG+GraphML to a MongoDB server.
#
# Author: Greg Stilwell
# Date: 2013-08-02

from sys import argv, path
# Exscript is for automating SSHv2/Telnet connections
path.append('/usr/local/lib/python2.6/site-packages/Exscript-v2.1.388_g65e7e55-py2.6.egg')
from Exscript.util.match import any_match
from Exscript.util.template import eval_file
from Exscript.util.start import quickstart
# For connecting to MongoDB servers
from pymongo import MongoClient
# My own secret sauce, for network analysis+diagramming
path.append('/home/gstilwel/lib/python')
from topo_parse import isis_db_to_digraph
from topo_analyze import spofs
from topo_analyze import diff
from topo_draw import draw


# MongoDB server
dbserver = '172.20.205.20'

# Dictionary of {router:region} from which to pull the IS-IS database.
# Since our IS-IS topology is flat in each region, we only need to login
# to one router per region to get a complete picture of that region.
router_region = {
    'nyc-bak01':'NA',
    'lon-bak01':'EU',
    'hkg-bak01':'AP'}

# Exscript wants a list of URLs
routers = []
for router in router_region:
    routers.append('ssh://' + router)


def mongo_save(topo_entry):
    """Connect to MongoDB server, and upload an entry with
     the collected topology data."""
    try:
        mongo = MongoClient(dbserver)
        db = mongo['topologies']
        coll = db['isis']
        coll.insert(topo_entry)
    except:
        print 'Unable to upload to MongoDB, oh well!'

def draw_isis(job, host, conn):
    """"Use Exscript to login to a Cisco IOS router, get the IS-IS database,
    and parse+analyze+draw the IS-IS topology."""
    # host.name is provided by Exscript, returns name of current host
    region = router_region[host.name]
    conn.send("enable\r")
    conn.app_authorize()
    conn.execute('term len 0')
    conn.execute('show isis database detail')
    isis_db = conn.response
    # Got the database, now parse it into a DiGraph
    topo = isis_db_to_digraph(isis_db, region)
    # Got topology DiGraph, now analyze it for potential SPOF impacts
    impacts = spofs(topo)
    # Got topology & SPOF impacts, now save the diagram (SVG) in the current
    # working directory, and try to upload the topology XML data (SVG+GraphML)
    # to MongoDB server
    topo_entry = draw(topo, impacts, save_svg=True, return_svg=True, return_graphml=True)
    topo_entry['region'] = region
    topo_entry['timestamp'] = topo.graph['timestamp']
    mongo_save(topo_entry)
    # use conn.send to 'exit' because conn.execute waits for a normal
    # prompt that will never come, and cause a script timeout error.
    conn.send('exit')

# Open a connection to each router, and do draw_isis().
quickstart(routers, draw_isis, max_threads = 3)
