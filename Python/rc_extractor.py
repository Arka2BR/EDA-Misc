import os

################################################ VARIABLES ###########################################################################################################


base		= "/nfs/site/disks/w.aadhika1.894"

#dirs 		= [
#				"maia_idecode_PDK005_0.63v_SUL_160CH_tbml_v2_675pc_aadhika1_91.25/aadhika1_TBML_V2_geninno_160CH_675pc_PDK005_91.25"
#				]
	
#dir_paths	= [os.path.join(base, x) for x in dirs]
	
dir_paths	= [	"/nfs/site/disks/w.aadhika1.894/deimos_vexecutive_1278.3_PDK008_180CH_0.85v_FMAX_normSynth_IFS_bsl5_aadhika1_execution/deimos_vexecutive_1278.3_PDK008_180CH_0.85v_FMAX_normSynth_IFS_bsl5_aadhika1_260_5.25/aadhika1_TBML_V2_hybrid_1278.3_PDK008_180CH_0.85v_FMAX_normSynth_IFS_bsl5_260_5.25",
				"/nfs/site/disks/w.aadhika1.894/deimos_baselines/deimos_vexecutive_PDK005_180CH_0.89v_FMAX_normSynth_786_baseline_aadhika1_255_5.4/aadhika1_TBML_V2_pure_PDK005_180CH_0.89v_FMAX_normSynth_786_baseline_255_5.4",
				]	
	
classifiers	= ["1278.3 PDK008", "1278.3 PDK005"]				

SAVE_DIR 	= "/nfs/site/disks/w.aadhika1.894/fmax_Results"
				
SAVEFILENAME= "RC_78.3_PDK0.8_vs_PDK0.5_chart.csv"

SAVE_FILE	= os.path.join(SAVE_DIR, SAVEFILENAME)


################################################ FUNCTIONS ###########################################################################################################

def rc_extractor(path):

	LAYERS		= 13
	
	rc_dict		= {}
	
	LOG_DIR		= os.path.join(path, 'logs')
	
	RT 			= sorted([filename for filename in os.listdir(LOG_DIR) if filename.startswith("route.logv")], reverse=True)
	print(RT)

	log_file = os.path.join(LOG_DIR, RT[0])
	with open(log_file, 'r') as f:
		raw_data = f.readlines()

	#print(raw_data)
	
	flag = "#Start timing driven prevention iteration..."
	for line in raw_data:
		if flag in line:
			START_IDX = raw_data.index(line) + 8
			
	for line in raw_data[START_IDX: START_IDX + LAYERS]:
		rc_sub_dict			= {}
		line_data 			= line.strip().split()
		layer_name 			= line_data[4][:-1]
		resistance			= line_data[7]
		capacitance 		= line_data[11]
		rc          		= line_data[-1]
		
		#print(line_data)
	
		rc_sub_dict["Res (ohm/um)"]	= resistance
		rc_sub_dict["Cap (ff/um)"]	= capacitance
		rc_sub_dict["RC"]			= rc
		
		rc_dict[layer_name]			= rc_sub_dict
		
	return rc_dict	

def rc_dict_morph(rc_csv_dict):
	pass

def rc_csv_gen(path_list, classifiers, savefile):
	
	data_list	= []
	
	rc_csv_dict = {}
		
	for path, name in zip(path_list, classifiers):
		rc_csv_dict[name] = rc_extractor(path)
		
	t0_keys			= list(rc_csv_dict.keys())
	t1_keys			= list(rc_csv_dict[t0_keys[0]].keys())
	
	for item in t1_keys:
		sub_data_list = []
		for key in t0_keys:
			t1_data = ",".join(list(rc_csv_dict[key][item].values()))
			sub_data_list.append(t1_data)
		
		t0_data 	= ",".join(sub_data_list)
		data_list.append(t0_data)
		
		
		#print(data_list)
	
	#print(t0_keys, t1_keys)
		
		
	sub_keys 		= ["Res (ohm/um)", "Cap (ff/um)", "RC"]
	
	class_str		= ", , ,".join(classifiers)
	
	TOP_HEADER		= "Layers, {}\n".format(class_str)
	SUB_HEADER		= ",".join(sub_keys * len(classifiers)) 
	
	
	with open(savefile, 'w') as f:
		f.write(TOP_HEADER)
		f.write(", {}\n".format(SUB_HEADER))
		for item in t1_keys:
			f.write("{}, {}\n".format(item, data_list[t1_keys.index(item)]))
		
		print("RC_Data Generted at: {}".format(savefile))
		
		
	

rc_csv_gen(dir_paths, classifiers, SAVE_FILE)

	