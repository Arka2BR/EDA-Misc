##########################################################################
# STEP report_layer_rc
##########################################################################
create_flow_step -name report_layer_rc -owner cadence {

set LAYER_COUNT $env{LAYER_COUNT}
set RC_CORNERS [all_rc_corners]
set REPORT_FILE rc_report.txt
for {set i 0} {$i < $LAYER_COUNT + 1} {incr i} {
	set layer "m$i"
	foreach corner $RC_CORNERS {
		report_unit_parasitics -layer $layer -rc_corner $corner >> $REPORT_FILE
			         }
}
}
