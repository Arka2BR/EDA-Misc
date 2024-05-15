import os
import argparse

def path_group_lister(content, path_count, path_start=0):
	path_group_flat = 'all'
	
	hist_setup_all = {}
	actual_view = ""
	actual_group = ""
	actual_edge = 0
	actual_endpoint = ""
	actual_pba_slack = ""
	actual_endpoint_clock = ""
	min_period = 999999.0
	freq_list = []
	
	nPathCell	= dict()
	nPathVt		= {'hvt':0, 'svt':0, 'lvt':0, 'ulvt': 0}
	vt_map		= {'a': 'ulvt', 'b': 'lvt', 'c': 'svt', 'd':'hvt'}
	
	for i, x in enumerate(content):
		if 'View:' in x:
			actual_view = str(x.split()[1]).rstrip()
		if 'Group:' in x:
			actual_group = str(x.split()[1]).rstrip()
		if 'Clock Edge:' in x:
			actual_edge = str(x.split()[2]).rstrip()
			freq_list.append(float(actual_edge))
		if 'Endpoint:' in x:
			actual_endpoint = str(x.split()[2]).rstrip()
		if 'Clock: (R)' in x:
			actual_endpoint_clock = str(x.split()[2]).rstrip()
		if x.startswith('Path ') and not 'Path Delay' in x:
			actual_pba_slack = str(x.split()[3].split('(')[1]).rstrip()
		if 'Slack:' in x:
			if 'all' in path_group_flat:
				#print(content[i+9])
				hist_setup_all[actual_endpoint] 		= {
															'Slack': actual_pba_slack,
															'Start Index': i+9
															}
			if 'reg2reg' in path_group_flat and not 'in2reg' in actual_group and not 'in2out' in actual_group and not 'reg2out' in actual_group:
				#print(content[i+9])
				hist_setup_all[actual_endpoint] 		= {
															'Slack': actual_pba_slack,
															'Start Index': i+9
															}
		if '#' in x and not '#' in content[i+1] and not '#' in content[i-1] :
			hist_setup_all[actual_endpoint]['End Index'] = i-1
	
	min_period= max(freq_list,key=freq_list.count)
	
	if hist_setup_all:
		sorted_slack = sorted(hist_setup_all.items(),key=lambda item: float(item[1]['Slack']), reverse=False)
		#sorted_index = sorted(hist_setup_all.items(),key=lambda item: float(item[1]['Start Index']), reverse=False)
		
		
	for item in sorted_slack[path_start: min(path_start + path_count, len(sorted_slack))] :
		print(item)
		for line in content[item[1]['Start Index']:item[1]['End Index']]:
			line_lst 	= line.split()
			cell_name 	= line_lst[5]
			cell_vt		= cell_name[-7]
			if cell_name not in nPathCell.keys():
				nPathCell[cell_name] = 1
			else:
				nPathCell[cell_name] += 1
			
			nPathVt[vt_map[cell_vt]] +=1
	
	print(nPathCell)
	print(nPathVt)
	
	
		
if __name__ == "__main__":
		parser 		= argparse.ArgumentParser()
		parser.add_argument("-f", "--file", required=True,  help="Specify the timing report file to be used for analysis.")
		parser.add_argument("-pc", "--path_count", required=True, help="Specify the number of paths to be considered for analysis")
		parser.add_argument("-ps", "--path_start", help="Specify starting index of paths for analysis")
		parser.add_argument("-o", "--output", help="Specify output path for config file.")
		
		args 		= parser.parse_args()
		
		with open(args.file) as fl:
			content = fl.readlines()
			
		if args.path_start:
			path_group_lister(content, int(args.path_count), int(args.path_start))
		else:
			path_group_lister(content, int(args.path_count))
	
