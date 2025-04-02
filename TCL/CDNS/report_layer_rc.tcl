##########################################################################
# STEP report_layer_rc
##########################################################################
create_flow_step -name report_layer_rc -owner cadence {

set LAYER_COUNT [get_db layers -if {.type==routing && .backside==false}]
set RC_CORNERS [all_rc_corners]
set REPORT_FILE rc_report.rpt
for layer $METAL_LAYERS {
	foreach corner $RC_CORNERS {
		report_unit_parasitics -layer $layer -rc_corner $corner >> $REPORT_FILE
			         }
}
}
