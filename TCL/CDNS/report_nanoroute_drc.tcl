
create_flow_step -name report_nanoroute_drc -owner cadence {
#Get the markers for annoroute
set nr_drc_lst [get_db designs .markers -if {.originator==route_design}]

set drc_dict [dict create]
set drc_huddle [huddle create]
set block_name [get_db designs .name]
set stage [get_db flow_report_name]
set report_name "$block_name.nanoroute_drc.$stage.yaml"

# Store them in Dict
foreach dr $nr_drc_lst {
	set dr_type [get_db $dr .subtype]
	set dr_layer [get_db $dr .layer.name]
	set dr_fake [get_db $dr .is_false]
	if {![dict exists $drc_dict $dr_type]} {
		dict set drc_dict $dr_type [dict create $dr_layer 1]
	} elseif {![dict exists $drc_dict $dr_type $dr_layer]} {
		dict set drc_dict $dr_type $dr_layer 1
	} else {
		dict set drc_dict $dr_type $dr_layer [expr ([dict get $drc_dict $dr_type $dr_layer] + 1)]
	}
	
}
set outfile [open $report_name w+]
puts $outfile "##### Nano-route DRC Summary: #####"
# Convert Dict to Huddle for YAML generation
dict for {type layermix} $drc_dict {
	 
	dict for {layer count} $layermix { 
		if {![huddle exists $drc_huddle $type]} {
				huddle set drc_huddle $type [huddle create $layer $count]
			} elseif {![huddle exists $drc_huddle $type $layer]} {
				huddle set drc_huddle $type $layer $count
			}

	}
}
puts $outfile [::yaml::huddle2yaml $drc_huddle]
puts $outfile "# --------------END-----------------"
close $outfile
puts "Finished generating DRC report in : $report_name"
}
