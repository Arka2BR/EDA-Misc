##########################################################################
# STEP report_layer_rc
##########################################################################
create_flow_step -name report_layer_rc -owner cadence {

set METAL_LAYERS [get_db [get_db layers -if {.type==routing && .backside==false}] .name]
set RC_CORNERS [all_rc_corners]
set REPORT_FILE rc_report.rpt
foreach layer $METAL_LAYERS {
	foreach corner $RC_CORNERS {
		report_unit_parasitics -layer $layer -rc_corner $corner >> $REPORT_FILE
			         }
}
}
