#!/usr/bin/python3

import os
import sys
import pathlib
import subprocess

print(sys.argv)

raw_path = sys.argv[1]
PATH 	 = os.path.realpath(raw_path)
PARENT	 = pathlib.Path(PATH).parent.absolute()




for item in os.listdir(PATH):
	abs_pth 	= os.path.join(PATH, item)
	if os.path.islink(abs_pth):
		real_pth	= os.readlink(abs_pth)
		
		if real_pth.startswith('..'):
			print(PARENT)
			real_pth = os.path.join(PARENT, real_pth[3:])
			print(real_pth)
		elif real_pth.startswith('parent'):
			print(PARENT)
			real_pth = os.path.join(PATH, real_pth)
			print(real_pth)
		lnk_rm		= f"rm {abs_pth}"
		lnk_cp		= f"cp -rf {real_pth} {PATH}/."
		chng_echo	= f"echo 'Replaced {abs_pth} with direct copy from {raw_path}'"
		cmds		= f"{lnk_rm}; {lnk_cp}; {chng_echo}"
		
		subprocess.run(cmds, shell=True)
		
		
print("Finished replacing paths!")
		
