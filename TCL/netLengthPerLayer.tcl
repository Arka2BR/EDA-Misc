proc netLengthPerLayer {netname} {
#set fwrite [open $filename w+] 
puts "\n#######################################################"
puts "NETNAME: $netname"
set wireList [get_db net:$netname .wires]
set netLayerMap [dict create]
set layername_length ""
for {set wire 0} {$wire < [llength $wireList]} {incr wire} {
        set layerName [get_db [lindex $wireList $wire] .layer.name]
        set layerLength [get_db [lindex $wireList $wire] .length]
		#puts $filename $layerLength
        lappend layername_length $layerName $layerLength
		
	}

## MAKING AN ARRAY TO DISPLAY THE RESULTS ##
unset -nocomplain length
set count 0

foreach i $layername_length { 
if {[regexp "m" $i]} { set length($i) 0}
}

foreach i $layername_length {
if {[regexp "m" $i]} {
set length($i) [expr $length($i) + [lindex $layername_length [expr $count + 1]]]
}
incr count
}
parray length

## TO FIND TOTAL NET LENGTH ##
proc listadd L {expr [join $L +]+0}
puts "TOTAL NET LENGTH = [listadd [get_db net:$netname .wires.length]]"
puts "#######################################################\n"
}

