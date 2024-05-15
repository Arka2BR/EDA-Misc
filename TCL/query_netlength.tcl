

proc netLengthPerLayer {netname} {

set outputFile report_netlist_wirelngth.rpt
puts "\n#######################################################" >> $outputFile
puts "NETNAME: $netname" >> $outputFile
set wireList [get_db net:$netname .wires]
set layername_length ""
for {set wire 0} {$wire < [llength $wireList]} {incr wire} {
        set layerName [get_db [lindex $wireList $wire] .layer.name]
        set layerLength [get_db [lindex $wireList $wire] .length]
        lappend layername_length $layerName $layerLength
	#puts $layername_length
        }
puts $layername_length >> $outputFile


## MAKING AN ARRAY TO DISPLAY THE RESULTS ##
unset -nocomplain length
set count 0

proc listadd L {expr [join $L +]+0}
puts "TOTAL NET LENGTH = [listadd [get_db net:$netname .wires.length]]" >> $outputFile
puts "#######################################################\n" >> $outputFile
}

set netlist [get_db nets]

foreach net $netlist {
	set net_name [lindex [split $net ':'] 1]
	netLengthPerLayer $net_name
}

