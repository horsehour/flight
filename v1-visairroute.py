from graph_tool.all import *
import pandas as pd
import numpy as np

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
		vsz[i], vord[i], vc[i] = 5, 0, np.array([225,192,50,256*0.2])/256 #light grey
	
	# Properties of routes: size, order, color
	esz, eord, ec = g.new_ep('int'), g.new_ep('int'), g.new_ep('vector<float>')

	for e in edges.values():
		esz[e],eord[e],ec[e] = 1, 0, np.array([153,216,201,256*0.2])/256 # light green
	return vsz, vord, vc, esz, eord, ec

node_names, node_index, edges, g = setup_route_net()
num_node, num_link = len(node_index), len(edges)

vsz, vord, vc, esz, eord, ec = config_graph()

# Highlight some routes
cdf0 = pd.read_csv('cost0.csv')
#cdf1 = pd.read_csv('cost.csv')
for i, row in cdf0.iterrows():
	n1, n2, ict = row.Departure, row.Arrival, row.Cost
	if ict > 0:
		name = n1 + '-' + n2
		# dark red
		v, vc[v],vord[v] = node_index[name], np.array([215, 25, 28, 0.8*256])/256,num_node

# Visualize the pairwise shortest paths through some specific route (w/ non-zero initial cost)
#for s, t in zip(['GEG-SEA','PDX-LAS', 'ANC-BET'],['PDX-LAS','ANC-BET','GEG-SEA']):
#for s, t in zip(['ANC-PDX', 'PDX-LAS', 'JFK-SEA', 'SEA-EWR'],['PDX-LAS', 'JFK-SEA', 'SEA-EWR', 'ANC-PDX']):
for s, t in zip(['ANC-PDX', 'PDX-LAS', 'LAS-SEA', 'SEA-LAX'],['PDX-LAS', 'LAS-SEA', 'SEA-LAX', 'ANC-PDX']):
	vs, path = shortest_path(g, node_index[s], node_index[t])
	for v in vs:
		vsz[v], vord[v], vc[v][3] = 5, num_node, 1

	for e in path:
		esz[e], eord[e], ec[e] = 1.5, num_link + num_node, np.array([7, 94, 251, 256])/256

output_file, pos_file = 'flightnet.pdf', 'coordination.csv'
pos = layout(g, node_names, node_index, pos_file=pos_file, layout_algo='arf')
graph_draw(g, pos=pos, vertex_color=vc, vertex_fill_color=vc, vorder=vord,
vertex_text=node_names,vertex_text_position=-2,vertex_font_size=5,
edge_pen_width=esz, edge_color=ec,eorder=eord,
output=output_file)

