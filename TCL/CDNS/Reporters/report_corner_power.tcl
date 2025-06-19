##########################################################################
# STEP report_power
##########################################################################
create_flow_step -name report_corner_power -owner cadence {
	set analysis_views [get_db analysis_views]
	set stage [get_db flow_report_name]
	foreach view $analysis_views {

	set view_name [get_db $view .name]
	set setup_check [get_db $view .is_setup]
	if {$setup_check == true} {
		set view_voltage [get_db $view .delay_corner.default_early_timing_condition.opcond.voltage]
	
		set pos [string first . $view_voltage]
		set mod_view_voltage [string replace $view_voltage $pos $pos p]
		set report_file_name "power_${stage}_${mod_view_voltage}.rpt"
		puts "Generating Power report for Analysis View : $view_name, Operating at voltage: $view_voltage ..."
		report_power -view $view_name -out_file $report_file_name
		puts "Generated $report_file_name"
		}

	}

}
