import os
import subprocess

FILE = "/nfs/site/disks/w.aadhika1.894/deimos_samples/deimos_PDK005_i0m_opt2_sample/scripts/user/report_z_dist.tcl"
BASE = "/nfs/site/disks/w.aadhika1.894"
DIR_TAG	= "deimos_vexecutive_PDK005_180CH_0.89v_FMAX_normSynth_opt2_sweep_new3_aadhika1_"
RUN_TAG	= "aadhika1_TBML_V2_hybrid_PDK005_180CH_0.89v_FMAX_normSynth_opt2_sweep_new3"

DIRS = [f for f in os.listdir(BASE) if f.startswith(DIR_TAG)]

for dir in DIRS:
	dir_path	= os.path.join(BASE, dir)
	run_path	= os.path.join(dir_path, [x for x in os.listdir(dir_path) if x.startswith(RUN_TAG)][0])
	sub_path	= os.path.join(dir_path, 'scripts/user')
	
	copy_dir	= "cp -rf {} {}/.".format(FILE, sub_path)
	
	subprocess.run(copy_dir, shell = True)
	print("Copied to {}".format(sub_path))
	
	

