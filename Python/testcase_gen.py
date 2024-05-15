#!/usr/bin/python3

import os
from os.path import join as oPe
import argparse
import subprocess
from time import sleep

# Tool Interfacing
def execute_tool(work_dir,run_dir, stage, tool, design=None):
    # Command Templates
    INVS_CMDS   = "#!/usr/bin/env tclsh\nread_db {}\nwrite_testcase -name {}_testcase\nexit\n"
    GENUS_CMDS  = "#!/usr/bin/env tclsh\nread_db {}\ncreate_testcase -copy_libraries -directory {}_testcase -design [lindex [split [get_db designs] ':'] 1] -write_db {}\nexit\n"
    INVS_START  = "{} -cpus 10 -no_gui -stylus -init {}"
    GENUS_START = "{} -no_gui -files {}"
    # File names
    GENUS_FILE  = 'genus_tst_gen.tcl'
    INVS_FILE   = 'inv_tst_gen.tcl'
 
    # Tool-wise modifications
    if tool == 'innovus':
        file_name   = INVS_FILE
        DB_PATH     = oPe(run_dir, "dbs/{}.enc".format(stage))
        cmd_template= INVS_CMDS.format(DB_PATH, stage)
        tool_start  = INVS_START

    elif tool == 'genus':
        file_name   = GENUS_FILE
        if os.path.exists(oPe(run_dir, "dbs/{}.db".format(stage))):
            DB_PATH     = oPe(run_dir, "dbs/{}.db".format(stage))
        else:
            DB_PATH     = oPe(run_dir, "dbs/{}.cdb".format(stage))
        cmd_template= GENUS_CMDS.format(DB_PATH, stage, stage)
        tool_start  = GENUS_START
    # Commons
    TOOL_PATH   = os.environ['{}_PATH'.format(tool.upper())]

    #Create file
    query_file  = oPe(work_dir, file_name)
    #Add testcase commands
    with open(query_file, 'w') as f:
         f.write(cmd_template)

    tool_cmd     = tool_start.format(TOOL_PATH, query_file)
    subprocess.run(tool_cmd, shell = "True",stdin = subprocess.PIPE)

    #Remove the generated script
    os.remove(query_file)

# Main function
def testcase_gen():

    # Parser setup
    parser = argparse.ArgumentParser()
    parser.add_argument("-rd", "--rundir", help="Specify run directory.", required=True)
    parser.add_argument("-s", "--stage", help="Specify the stage to run.You can use 'all' to generate for all stages")
    parser.add_argument("-o", "--output", help="Specify the output directory file name/path.", required=True)
    #parser.add_argument("-d", "--design", help="Specify exact design name. You can find it by using get_db designs inside Genus shell.")
    args = parser.parse_args()

    #Path setup
    WORK_DIR    = os.getcwd()
    RUN_DIR     = oPe(WORK_DIR, args.rundir)
    REPORT_DIR  = oPe(RUN_DIR, 'reports')
    LOG_DIR     = oPe(RUN_DIR, 'logs')
    INPUTS_DIR  = oPe(WORK_DIR, 'inputs')
    SCRIPTS_DIR = oPe(WORK_DIR, 'scripts')
    SETUP_PATH  = oPe(SCRIPTS_DIR,"common/setup.tcsh")

    FLOW_METRIC = "{}/flow.metrics*".format(RUN_DIR)

    OP_PATH     = oPe(WORK_DIR, args.output)

    # Misc variables
    GNUS_STAGES = ['pregeneric.db', 'postelab.db']
    INVS_STAGES = []

    # Get all tool stages
    for item in os.listdir(REPORT_DIR):
        path    = os.path.realpath(item)
        if not path.endswith('.html'):
            if not item.startswith('syn'):
                INVS_STAGES.append(item)
            else:
                GNUS_STAGES.append(item)

    # Generate testcases
    if args.stage==None or args.stage == 'all':
        for stage in GNUS_STAGES:
            execute_tool(WORK_DIR, RUN_DIR, stage, 'genus')
        for stage in INVS_STAGES:
            execute_tool(WORK_DIR, RUN_DIR, stage, 'innovus')
    elif args.stage not in INVS_STAGES and args.stage not in GNUS_STAGES:
        print("Invalid stage provided as argument.")
    else:
        if args.stage in INVS_STAGES: execute_tool(WORK_DIR, RUN_DIR, args.stage, 'innovus')
        elif args.stage in GNUS_STAGES: execute_tool(WORK_DIR, RUN_DIR, args.stage, 'genus')

    # Package into main output directory
    
    if not os.path.exists(OP_PATH):
        os.mkdir(OP_PATH)

    # Command Templates
    CP_CMD          = "cp -rf {} {}/."
    MV_CMD          = "mv {} {}/."

    # General Templates
    TESTCASE_DIR    = '{}/*_testcase'.format(WORK_DIR)
    HEX_CMD_HLDR    = "{}; {}; {}; {}; {}; {}"
    
    # Commands
    SCR_CPY = CP_CMD.format(SCRIPTS_DIR, OP_PATH)
    INP_CPY = CP_CMD.format(INPUTS_DIR, OP_PATH)
    LOG_CPY = CP_CMD.format(LOG_DIR, OP_PATH)
    REP_CPY = CP_CMD.format(REPORT_DIR, OP_PATH)
    MET_CPY = CP_CMD.format(FLOW_METRIC, OP_PATH)

    TST_MV  = MV_CMD.format(TESTCASE_DIR, OP_PATH)

    CMD_LST = HEX_CMD_HLDR.format(SCR_CPY, INP_CPY, LOG_CPY, REP_CPY, MET_CPY, TST_MV)

    # Execution
    subprocess.run(CMD_LST, shell = True)

    print("\u001b[35;1mPackaging Testcases successfully completed! \u001b[0m")

if __name__ == "__main__":
    testcase_gen()


