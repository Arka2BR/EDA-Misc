###############################################################################
# Author : Arkaprabho Adhikary
# This is a necessary step to run place_opt_design for CDNS 18.XX and above.
# This is only necessary when there is more than 50% scan chain definitions
# missing in the design and we want to keep scan chains unstitched.
###############################################################################

proc disconnectSI {} {
	set op [open detach_term.tcl w]
	foreach pin  [get_db [get_db insts -if {.pins.base_pin.base_name==si}] .pins.name] {
		set inst_name [get_db pin:$pin .inst.name]
		set net_name [get_db pin:$pin .net.name ]
		set pin_name si
		if {$net_name == ""} {continue}

			if {[is_common_ui_mode]} {
			puts $op "try {disconnect_pin -inst $inst_name -pin $pin_name -net $net_name} on error {result options} {puts {$pin_name not connected to $net_name}}"  
		} else {
			puts $op "try {detachTerm $inst_name scan $net_name} on error {result options} {puts {$pin_name not connected to $net_name}}"  
		}
	}
	close $op
	puts "Please source the created file detach_term.tcl"
}

disconnectSI
source detach_term.tcl
