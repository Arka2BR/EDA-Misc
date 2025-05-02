create_flow_step -name run_lec -owner cadence {

set flow_stage [get_db flow_report_name]
set design_name [get_design .name]

if {$flow_stage=="syn_map"} {

	write_do_lec -top $design_name -golden_design rtl -revised_design fv_map -flat -write_session lec_genus_${flow_stage}_dp_int -verbose -log_file lec_genus_${flow_stage}_int.dp.log > rtl_to_fv_map.tcl
	lec.db -xl -dofile rtl_to_fv_map.tcl

} elseif {$flow_stage == "syn_opt"} {
	
	write_hdl -lec > final.v
	write_do_lec  -top $design_name -golden_design rtl -revised_design final.v -flat -write_session lec_genus_${flow_stage}_dp_int -verbose -log_file lec_genus_${flow_stage}_int.dp.log > rtl_to_final.tcl
	lec.db -xl -dofile rtl_toFinal.tcl

}

}
