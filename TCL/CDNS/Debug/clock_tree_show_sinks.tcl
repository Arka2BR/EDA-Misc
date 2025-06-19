proc show_sinks {} {
 foreach sg [get_ccopt_skew_groups *] {
 puts "Skew group: $sg"
 foreach sink [get_ccopt_property sinks_active -skew_group ${sg}] {
 if {[get_ccopt_property sink_type -pin $sink] != "ignore"} {
 puts $sink
 }
 }
 }
}
