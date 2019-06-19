from graph_tool.all import *
from bisect import bisect
import pandas as pd
import numpy as np

intervals = [100, 200, 400, 500, 600, 800, 2000, 4000]

def setup_route_net():
	node_index, edges = {}, {}

	routes = pd.read_csv('routes.csv')
	g = Graph(directed=True)
	node_names = g.new_vp('string')
	
	for i, row in routes.iterrows():
		n1, n2 = row.flight1, row.flight2
		if n1 not in node_index:
			v1 = g.add_vertex()
			node_index[n1] = v1
			node_names[v1] = n1
		else:
			v1 = node_index[n1]
	
		if n2 not in node_index:
			v2 = g.add_vertex()
			node_index[n2] = v2
			node_names[v2] = n2
		else:
			v2 = node_index[n2]
	
		e = g.add_edge(v1,v2)
		edges[(v1,v2)] = e
	return node_names, node_index, edges, g


def layout(g, node_names, node_index, pos_file, layout_algo='sfdp'):
	if pos_file:
		df = pd.read_csv(pos_file)
		pos = g.new_vp('vector<double>')
		ymin, ymax = df.y.min(), df.y.max()
		df['y'] = ymin + ymax - df.y
		
		for i, row in df.iterrows():
			node = row.route
			v = node_index[node]
			pos[v] = [row.x, row.y]
	elif layout_algo == 'sfdp':
		pos = sfdp_layout(g)
	elif layout_algo == 'fr':
		pos = fruchterman_reingold_layout(g, n_iter=2000)	
	else:
		pos = arf_layout(g, max_iter=0, d=5, a=5)
	
	if not pos_file:
		pos_file = 'coordination.csv'
		routes, xs, ys = [], [], []
		for v in range(len(node_index)):
			routes.append(node_names[v])
			x, y = pos[v]
			xs.append(x)
			ys.append(y)
		dat = pd.DataFrame({'route': routes, 'x': xs, 'y': ys})
		dat.to_csv(pos_file, index=False)
	return pos

def config_graph():
	# Properties of node_index: size, order, color
	vsz, vord, vc = g.new_vp('int'), g.new_vp('int'), g.new_vp('vector<float>')
	for i in range(len(node_index)):
		vsz[i], vord[i], vc[i] = 5, 0, np.array([128,128,128,128*0.3])/256 #light grey
	
	# Properties of routes: size, order, color
	esz, eord, ec = g.new_ep('int'), g.new_ep('int'), g.new_ep('vector<float>')

	for e in edges.values():
		esz[e],eord[e],ec[e] = 1, 0, np.array([153,216,201,256*0.3])/256 # light green
	return vsz, vord, vc, esz, eord, ec

node_names, node_index, edges, g = setup_route_net()
num_node, num_link = len(node_index), len(edges)

vsz, vord, vc, esz, eord, ec = config_graph()

def show_state(cdf, entry='Cost', initial=True):
	if initial:
		output_file = 'flightnet1.pdf'
	else:
		output_file = 'flightnet2-{}.pdf'.format(entry)
	
	cdf = cdf[cdf.Airline == 'AS'].reset_index(drop=True)
	for i, row in cdf.iterrows():
		n1, n2, ict = row.Departure, row.Arrival, row[entry]
		name = n1 + '-' + n2
		if name not in node_index:
			continue

		v = node_index[name]
#		if ict > 0:	
#			vc[v],vord[v] = np.array([128,128,128,256])/256, num_node
		# Define the size using the cost (zero - 5)
		#vsz[v] = np.log2(ict + 100)
		vsz[v] = 8 + bisect(intervals, ict)

	# Visualize the pairwise shortest paths through some specific route (w/ non-zero initial cost)
	#for s, t in zip(['GEG-SEA','PDX-LAS', 'ANC-BET'],['PDX-LAS','ANC-BET','GEG-SEA']):
	for s, t in zip(['ANC-PDX', 'PDX-LAS', 'OAK-SEA', 'SEA-EWR', 'SEA-ANC'],['PDX-LAS', 'OAK-SEA', 'SEA-EWR', 'SEA-ANC', 'ANC-PDX']):
	#for s, t in zip(['ANC-PDX', 'PDX-LAS', 'LAS-SEA', 'SEA-LAX'],['PDX-LAS', 'LAS-SEA', 'SEA-LAX', 'ANC-PDX']):
		vs, path = shortest_path(g, node_index[s], node_index[t])
		for v in vs:
			vord[v], vc[v][3] = num_node, 1
		for e in path:
			esz[e], eord[e], ec[e] = 1.5, num_link + num_node, np.array([7, 94, 251, 256])/256

	pos_file = 'coordination.csv'
	pos = layout(g, node_names, node_index, pos_file=pos_file, layout_algo='arf')
	graph_draw(g, pos=pos, vertex_size=vsz, vertex_color=vc, vertex_fill_color=vc, vorder=vord,
	edge_pen_width=esz, edge_color=ec,eorder=eord,
	output=output_file)

# Highlight some routes
cdf0 = pd.read_csv('cost0.csv')
show_state(cdf0, initial=True)

cdf1 = pd.read_csv('cost.csv')
show_state(cdf1, entry='LQR', initial=False)
show_state(cdf1, entry='NoControl', initial=False)