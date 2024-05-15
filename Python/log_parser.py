import os
from os import path as pth


STOD	= "/nfs/site/disks/w.aadhika1.673"
LUS		= "Log_Under_Study/deimos_route"
FILE	= "route.logv"
OP		= "parsed_{}".format(FILE)
ROOTDIR	= pth.join(STOD, LUS)
PATH	= pth.join(ROOTDIR, FILE)
SAVEPATH= pth.join(ROOTDIR, OP)

def segment_parser(data, TAGS, SAVEPATH, type=1):
	
	with open(SAVEPATH, 'w') as f:
		for line in data:
			if type==1:
				if any(tag in line for tag in TAGS) :
					refline = " ".join(line.split()[3:]) + "\n"
					f.write(",".join([str(data.index(line))+ '>>>>',refline]))
			elif type ==2:
				if not any(tag in line for tag in TAGS):
					refline = " ".join(line.split()[3:]) + "\n"
					#print(refline)
					f.write(refline)
				
	
	print("Successfully generated {}!".format(SAVEPATH))


with open(PATH, 'r') as f:
	raw_data = f.readlines()

#print(raw_data)

# Warning Parse
WARN_TAGS	= ["WARNING", "WARN"]
OP 			= "warnings.txt"
SAVEPATH 	= pth.join(ROOTDIR, OP)
segment_parser(raw_data, WARN_TAGS, SAVEPATH)

# Error Parse
ERR_TAGS	= ["Error", "ERROR", "error"]
OP 			= "errors.txt"
SAVEPATH 	= pth.join(ROOTDIR, OP)
segment_parser(raw_data, ERR_TAGS, SAVEPATH)

#Skip Parse
SKIP_TAGS		= ["Skipping", "gate forming layer type."]
OP 			= "Skips.txt"
SAVEPATH 	= pth.join(ROOTDIR, OP)
segment_parser(raw_data, SKIP_TAGS, SAVEPATH)

#Deletes Parse
DEL_TAGS		= ["Deleted", "deleted"]
OP 			= "Deletes.txt"
SAVEPATH 	= pth.join(ROOTDIR, OP)
segment_parser(raw_data, DEL_TAGS, SAVEPATH)

#AAE References
AAE_TAGS	= ["AAE"]
OP 				= "AAEInfo.txt"
SAVEPATH 		= pth.join(ROOTDIR, OP)
segment_parser(raw_data, AAE_TAGS, SAVEPATH)

#Corner References
CORNER_TAGS	= ["Corner", "corner"]
OP 				= "CornerInfo.txt"
SAVEPATH 		= pth.join(ROOTDIR, OP)
segment_parser(raw_data, CORNER_TAGS, SAVEPATH)


#Script References
SCRIPT_TAGS	= ["dict ", "puts", "foreach", "verbose", "if", "else", "}", "set_db", "vars", "$env", "get_db", "cmd", "tot_area", "prev_", "tmp_", "tptal_", "$"]
OP 				= "ScriptRefs.txt"
SAVEPATH 		= pth.join(ROOTDIR, OP)
segment_parser(raw_data, SCRIPT_TAGS, SAVEPATH)

#Read References
READ_TAGS	= ["Reading", "Read", "read"]
OP 				= "FileReads.txt"
SAVEPATH 		= pth.join(ROOTDIR, OP)
segment_parser(raw_data, READ_TAGS, SAVEPATH)

#File References
FILE_TAGS	= ["file", "File", "directory", ".yaml", "database"]
OP 				= "FileRef.txt"
SAVEPATH 		= pth.join(ROOTDIR, OP)
segment_parser(raw_data, FILE_TAGS, SAVEPATH)

#Processing
PROCESSING_TAGS	= ["processing", "Processing"]
OP 				= "Processing.txt"
SAVEPATH 		= pth.join(ROOTDIR, OP)
segment_parser(raw_data, PROCESSING_TAGS, SAVEPATH)

#Effort
EFFORT_TAGS	= ["effort","Effort", "EffortLevel"]
OP 				= "Effort.txt"
SAVEPATH 		= pth.join(ROOTDIR, OP)
segment_parser(raw_data, EFFORT_TAGS, SAVEPATH)

#Calculate
CALC_TAGS	= ["calculate", "Calculate"]
OP 				= "Calculate.txt"
SAVEPATH 		= pth.join(ROOTDIR, OP)
segment_parser(raw_data, CALC_TAGS, SAVEPATH)

#Threads
THREAD_TAGS	= ["thread", "Thread"]
OP 				= "Threading.txt"
SAVEPATH 		= pth.join(ROOTDIR, OP)
segment_parser(raw_data, THREAD_TAGS, SAVEPATH)

#Sourcing
SRC_TAGS	= ["source", "Source", "Sourcing", "sourcing", "sourced", "Sourced"]
OP 				= "Sourcing.txt"
SAVEPATH 		= pth.join(ROOTDIR, OP)
segment_parser(raw_data, SRC_TAGS, SAVEPATH)

#CAP/RES
CAPRES_TAGS	= ["found CAPMODEL", "found RESMODEL", "eee:", "cap","Cap", "CAP",  "resistance", "Resistance", "RC"]
OP 			= "CapRes.txt"
SAVEPATH 	= pth.join(ROOTDIR, OP)
segment_parser(raw_data, CAPRES_TAGS, SAVEPATH)

#Voltage
VOLT_TAGS	= ["Voltage", "voltage"]
OP 			= "Voltage.txt"
SAVEPATH 	= pth.join(ROOTDIR, OP)
segment_parser(raw_data, VOLT_TAGS, SAVEPATH)

#Wire
WIRE_TAGS	= ["Wire", "wire"]
OP 			= "Wire.txt"
SAVEPATH 	= pth.join(ROOTDIR, OP)
segment_parser(raw_data, WIRE_TAGS, SAVEPATH)

#TIME
TIME_TAGS	= ["WNS", "TNS", "reg2reg", "reg2cgate", "in2out", "in2reg", "reg2out", "HEPG", "All Paths", "Violating Paths", "max_tran", "max_cap", "max_fanout", "max_length", "DRV", "Glitch"]
OP 			= "Timing.txt"
SAVEPATH 	= pth.join(ROOTDIR, OP)
segment_parser(raw_data, TIME_TAGS, SAVEPATH)

#IBS/IBM
LIB_TAGS	= ["ibs", "ibm"]
OP 			= "CellInfo.txt"
SAVEPATH 	= pth.join(ROOTDIR, OP)
segment_parser(raw_data, LIB_TAGS, SAVEPATH)

#FILLER
FILLER_TAGS	= ["Filler", "FILLER", "filler"]
OP 			= "FillerInfo.txt"
SAVEPATH 	= pth.join(ROOTDIR, OP)
segment_parser(raw_data, FILLER_TAGS, SAVEPATH)

#BUF/INV
BUFINV_TAGS	= ["Lib Analyzer", "buffer", "inverter"]
OP 			= "BufInv.txt"
SAVEPATH 	= pth.join(ROOTDIR, OP)
segment_parser(raw_data, BUFINV_TAGS, SAVEPATH)

#VIA
VIA_TAGS	= ["VIA", "via", "Via"]
OP 			= "ViaInfo.txt"
SAVEPATH 	= pth.join(ROOTDIR, OP)
segment_parser(raw_data, VIA_TAGS, SAVEPATH)

#DRC
DRC_TAGS	= ["drc", "violations", "optimization iteration",
				"MetSpc",
				"EOLSpc",
				"#\tm0",
				"#\tm1",
				"#\tm2",
				"#\tm3",
				"#\tm4",
				"#\tm5",
				"#\tm6",
				"#\tm7",
				"#\tm8",
				"#\tm9",
				"#\tm10",
				"#\tm11",
				"#	    Totals ",
				"#	Totals",
				"Routing",
				"routing",
				"#	    ndr",
				"#	    Rule",
				"#    By Non-Default Rule",
				"#    By Layer and Type :"
				]
OP 			= "DRCInfo.txt"
SAVEPATH 	= pth.join(ROOTDIR, OP)
segment_parser(raw_data, DRC_TAGS, SAVEPATH)

#Power
POWER_TAGS	= ["Power", "power"]
OP 			= "PowerInfo.txt"
SAVEPATH 	= pth.join(ROOTDIR, OP)
segment_parser(raw_data, POWER_TAGS, SAVEPATH)


#DAG Library Cell Dist
DAG_TAGS	= ["Clock DAG",
				"Bufs:",
               "Invs:",
               "ICGs:",
               "DCGs:",
				]
OP 			= "DAG_lib_cell_dist.txt"
SAVEPATH 	= pth.join(ROOTDIR, OP)
segment_parser(raw_data, DAG_TAGS, SAVEPATH)

#Redundancy Removal
RED_TAGS	= ["TAT_INFO",
				"User-Defined: net",
				"(VOLTUS_POWR-1520)",
				"/nfs/site/stod/stod3109/w.glnkish.127",
				"OPERPROF:",
				"Before cleanup",
				"After cleanup",
				"***",
				"*\n",
				"#\n",
				" / ",
				"CDS",
				"CPU",
				"Begin Processing",
				"Ended Processing",
				"Run Statistics",
				"Cpu time",
				"Increased memory",
				"Elapsed time",
				"elapsed",
				"Total memory",
				"Peak memory" ,
				"cal_flow",
				"cal_base_flow",
				"generate_cong_map_content",
				"update starts on",
				"init_flow_edge",
				"measure_qor",
				"measure_congestion",
				"report_flow_cap",
				"analyze_m2_tracks",
				"report_initial_resource",
				"mark_pg_pins_accessibility",
				"set_net_region",
				"'set_switching_activity' finished successfully.",
				"Info: End MT loop @coeSlackTraversor::updateSlacksAndFailingCount.",
				"GMT",
				"implementation."
				] 
TAGS		= RED_TAGS + WARN_TAGS + ERR_TAGS + SKIP_TAGS + CAPRES_TAGS + BUFINV_TAGS +DAG_TAGS + PROCESSING_TAGS +EFFORT_TAGS + CALC_TAGS + SRC_TAGS + THREAD_TAGS + VIA_TAGS + DRC_TAGS + VOLT_TAGS + FILE_TAGS + READ_TAGS
TAGS		= TAGS + AAE_TAGS + DEL_TAGS + SCRIPT_TAGS + POWER_TAGS + WIRE_TAGS + TIME_TAGS + FILLER_TAGS + CORNER_TAGS + LIB_TAGS
OP 			= "Reduce.txt"
SAVEPATH 	= pth.join(ROOTDIR, OP)
segment_parser(raw_data, TAGS, SAVEPATH, 2)

#Remove whitespaces in the filtered Reduce

with open(SAVEPATH, 'r') as f:
	unfildat =  f.readlines()
		
		
with open(SAVEPATH, 'w') as f:	
	for line in unfildat:
		if not line.strip('\n')=="":
			#print(line)
			f.write(line)

