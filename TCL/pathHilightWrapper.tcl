source /nfs/site/disks/w.aadhika1.894/TCL/hilightPath.tcl
set launch "u_dual_eu_ex2_b_data_q_reg[25]/clk"
set capture "CDN_MBIT_u_cpsr_u_flag0_z_core_q_reg_MB_u_cpsr_u_flag0_c_core_q_reg_MB_u_cpsr_u_flag0_n_core_q_reg_MB_u_cpsr_u_flag0_v_core_q_reg/d2"
set path "report_timing -from $launch -to $capture"
#set outfile1 [open "path_pin_report.rpt" w+] 
hilitePath -report_timing_args $path 
#get_db -pin path_pin_report.rpt -net_object
