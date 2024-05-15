################
## This proc takes up the "report_timing -options" as an arguments and can highlight datapath (by default) and launch_clock_path and capture_clock_path in GUI. 
################

proc dict'sort {dict args} {
    set res {}
    foreach key [eval [list lsort] [lrange $args 0 end] [list [dict keys $dict]]] {
        lappend a() $key [dict get $dict $key]
    }
    set res [lindex [array get a] 1]
}

proc netLengthPerLayer {netname filename layerStorage} {
puts $layerStorage
puts $filename "\n#######################################################"
puts $filename "NETNAME: $netname"
set wireList [get_db net:$netname .wires]
set layername_length ""
for {set wire 0} {$wire < [llength $wireList]} {incr wire} {
        set layerName [get_db [lindex $wireList $wire] .layer.name]
        set layerLength [get_db [lindex $wireList $wire] .length]
		#puts $filename $layerLength
        lappend layername_length $layerName $layerLength
		if {![dict exists $layerStorage $layerName]} {
		
			dict append layerStorage $layerName $layerLength
			set newTotal [expr {[dict get $layerStorage "Total"] + $layerLength}]
			dict set layerStorage "Total" $newTotal
			#puts $layerStorage
		} else {
			set newLength [expr {[dict get $layerStorage $layerName] + $layerLength}]
			dict set layerStorage $layerName $newLength
			set newTotal [expr {[dict get $layerStorage "Total"] + $layerLength}]
			dict set layerStorage "Total" $newTotal
		}
        }
#puts $filename $layerStorage

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
puts $filename "TOTAL NET LENGTH = [listadd [get_db net:$netname .wires.length]]"
puts $filename "#######################################################\n"

return $layerStorage

}


proc hilitePath {args} {
 
  set launch_clock_path 0
  set capture_clock_path 0
 
  set results(-help) "none"
  set results(-report_timing_args) "none"
  set results(-deselectAll) "none"
  set results(-launch_clock_path) "none"
  set results(-capture_clock_path) "none"

  parse_proc_arguments -args $args results

  if {$results(-help)==""} {
    help -verbose hilitePath
    return 1
  }
  
  set pin_path_report_file [open "path_pin_report.rpt" w+]
  set netList ""
  dict set netLayerMap "Total" 0
  
  if {$results(-deselectAll)!="none"} {deselectAll}
  if {$results(-launch_clock_path)!="none"} {set launch_clock_path 1}
  if {$results(-capture_clock_path)!="none"} {set capture_clock_path 1}
  if {$results(-report_timing_args)!="none"} {
    set report_timing_args $results(-report_timing_args)
    if {![regexp full_clock $report_timing_args]} {set timing_path [eval "$report_timing_args -collection -path_type full_clock"]} else {
	set timing_path [eval "$report_timing_args -collection"]}
  } else {
    set timing_path [eval "report_timing -collection -path_type full_clock"]
  }
  foreach_in_collection path $timing_path {
	
    if {$launch_clock_path} {set path [get_property $path launch_clock_path]}
    if {$capture_clock_path} {set path [get_property $path capture_clock_path]}
    set t_points [get_property $path timing_points]
    foreach_in_collection point $t_points {
      set pin [get_object_name [get_property $point pin]]
      eval_legacy "selectPin $pin"
      if {[catch {eval_legacy {dbIsTermFTerm $pin}}]} {
        catch {eval_legacy {selectInst [dbTermInstName [dbGetTermByInstTermName $pin]]}}
        #puts [dbTermInstName [dbGetTermByInstTermName $pin]]
      }
	  lappend netList [get_db pin:$pin .net.name]
	  
    }
  }
  lsort -unique $netList
  foreach net $netList {
	set netLayerMap [netLengthPerLayer $net $pin_path_report_file $netLayerMap]
  }
  puts $pin_path_report_file [dict'sort $netLayerMap]
  close $pin_path_report_file
}

define_proc_arguments hilitePath \
 -info "Highlight the combinational logic between startpoint and endpoint" \
 -define_args {\
  {-report_timing_args "Specifies the arguments of the report_timing" "string" string optional}
  {-deselectAll "deselects all previously selected objects" "" boolean optional}
  {-launch_clock_path "Highlights the launch clock path" "" boolean optional}
  {-capture_clock_path "Highlights the capture clock path" "" boolean optional}
}
