#######################################
## To find length of a net :         ##
#######################################
proc net_length {netname} {
set net_length 0
set net_wire_lengths [get_db net:$netname .wires.length]
foreach i $net_wire_lengths {
        set net_length [expr $net_length + $i] 
}
return $net_length
}

#####################################
## Find nets greater than a length ##
#####################################

proc netsGreaterThanLength {length filename} {
set fp [open $filename a]
puts $fp "Nets with net length greater than $length are:"
puts $fp "Net_Length \t\t Net_Name"
set cnt 0
set signal_nets [get_db [get_db nets -if {.is_clock != true && .is_power != true && .is_ground != true}] .name]
foreach net $signal_nets {
        if {[net_length $net] > $length} {
	puts $fp "[net_length $net] \t\t $net"
        incr cnt
        }
  }
close $fp
puts "Number of nets longer than $length um: $cnt "
puts "Longer nets are reported in $filename\n"
}

#####################################
## Find nets greater than a length ##
#####################################

netsGreaterThanLength 100 longNet.rpt
netsGreaterThanLength 150 longNet.rpt
