# =====================================================================
# report_xtalk_from_timing_path_objects.tcl
#
# Purpose:
#   Traverse timing paths across the design and report timing path pins/nets
#   that have crosstalk delay delta and/or crosstalk transition delta.
#
# Key difference vs report_timing parsing:
#   Uses timing_path / timing_point object attributes directly:
#       annotated_delay_delta
#       annotated_delta_transition
#       si_xtalk_bumps
#
# Usage:
#   source report_xtalk_from_timing_path_objects.tcl
#
#   report_xtalk_from_timing_path_objects
#
#   report_xtalk_from_timing_path_objects 0.0 0.0 500 5 xtalk_path_points.tsv
#
# Args:
#   delay_delta_threshold : abs annotated delay delta threshold
#   tran_delta_threshold  : abs annotated transition delta threshold
#   max_paths_per_group   : max paths per path group per delay type
#   nworst                : nworst paths per endpoint
#   outfile               : TSV output file
#   path_type             : full or full_clock_expanded
#   pba_mode              : none/path/exhaustive
#
# Notes:
#   - Requires PT-SI database after update_timing.
#   - "All timing paths" is practically bounded by max_paths_per_group/nworst.
#   - Use full_clock_expanded if you also care about clock-path crosstalk.
# =====================================================================


proc __xt_is_number {x} {
    if {$x eq "" || $x eq "NA"} {
        return 0
    }
    if {[catch {expr {double($x)}}]} {
        return 0
    }
    return 1
}


proc __xt_abs {x} {
    if {![__xt_is_number $x]} {
        return 0.0
    }
    return [expr {abs(double($x))}]
}


proc __xt_get_attr {obj attr {default "NA"}} {
    if {$obj eq ""} {
        return $default
    }

    if {[catch {set v [get_attribute -quiet $obj $attr]}]} {
        return $default
    }

    if {$v eq ""} {
        return $default
    }

    return $v
}


proc __xt_get_first_attr {obj attr_list {default "NA"}} {
    foreach a $attr_list {
        set v [__xt_get_attr $obj $a ""]
        if {$v ne "" && $v ne "NA"} {
            return $v
        }
    }
    return $default
}


proc __xt_obj_name {obj {default "NA"}} {
    if {$obj eq ""} {
        return $default
    }

    if {[catch {set n [get_object_name $obj]}]} {
        return $default
    }

    if {$n eq ""} {
        return $default
    }

    return $n
}


proc __xt_collection_first {coll} {
    if {$coll eq ""} {
        return ""
    }

    if {[catch {sizeof_collection $coll} sz]} {
        return ""
    }

    if {$sz == 0} {
        return ""
    }

    return [index_collection $coll 0]
}


proc __xt_get_point_object {timing_point} {
    # Timing point object is usually in attribute "object".
    set obj [__xt_get_attr $timing_point object ""]

    if {$obj ne "" && $obj ne "NA"} {
        return $obj
    }

    return ""
}


proc __xt_get_net_of_obj {obj} {
    if {$obj eq ""} {
        return ""
    }

    if {[catch {set nets [get_nets -quiet -of_objects $obj]}]} {
        return ""
    }

    return [__xt_collection_first $nets]
}


proc __xt_get_driver_of_net {net} {
    if {$net eq ""} {
        return "NA"
    }

    # Internal net driver pin
    set drv_pins [get_pins -quiet -leaf -of_objects $net -filter "direction == out"]
    if {[sizeof_collection $drv_pins] > 0} {
        return [get_object_name [index_collection $drv_pins 0]]
    }

    # Top-level input port driver
    set drv_ports [get_ports -quiet -of_objects $net -filter "direction == in || direction == inout"]
    if {[sizeof_collection $drv_ports] > 0} {
        return [get_object_name [index_collection $drv_ports 0]]
    }

    return "NA"
}


proc __xt_get_cell_of_obj {obj} {
    if {$obj eq ""} {
        return "NA"
    }

    if {[catch {set cells [get_cells -quiet -of_objects $obj]}]} {
        return "NA"
    }

    if {[sizeof_collection $cells] > 0} {
        return [get_object_name [index_collection $cells 0]]
    }

    return "NA"
}


proc __xt_get_ref_of_cell_name {cell_name} {
    if {$cell_name eq "NA" || $cell_name eq ""} {
        return "NA"
    }

    set c [get_cells -quiet $cell_name]
    if {[sizeof_collection $c] == 0} {
        return "NA"
    }

    return [__xt_get_attr [index_collection $c 0] ref_name "NA"]
}


proc __xt_get_path_groups {} {
    if {[catch {set pgs [get_path_groups *]}]} {
        return "__ALL__"
    }

    if {[sizeof_collection $pgs] == 0} {
        return "__ALL__"
    }

    set out {}
    foreach_in_collection pg $pgs {
        lappend out [get_object_name $pg]
    }

    return $out
}


proc __xt_get_path_attr_name {path attr} {
    set v [__xt_get_attr $path $attr "NA"]

    if {$v eq "NA"} {
        return "NA"
    }

    # If attribute is an object, get name.
    if {![catch {set n [get_object_name $v]}]} {
        if {$n ne ""} {
            return $n
        }
    }

    return $v
}


proc __xt_get_timing_paths_for_group {delay_type group max_paths_per_group nworst path_type pba_mode} {

    set cmd [list get_timing_paths \
        -delay_type $delay_type \
        -max_paths $max_paths_per_group \
        -nworst $nworst \
        -path_type $path_type]

    if {$group ne "__ALL__"} {
        lappend cmd -group $group
    }

    if {$pba_mode ne "none" && $pba_mode ne ""} {
        lappend cmd -pba_mode $pba_mode
    }

    if {[catch {set paths [eval $cmd]} err]} {
        puts "WARN: get_timing_paths failed for delay_type=$delay_type group=$group"
        puts "      $err"
        return ""
    }

    return $paths
}


proc report_xtalk_from_timing_path_objects { \
    {delay_delta_threshold 0.0} \
    {tran_delta_threshold 0.0} \
    {max_paths_per_group 500} \
    {nworst 5} \
    {outfile "xtalk_path_points.tsv"} \
    {path_type "full_clock_expanded"} \
    {pba_mode "none"} \
} {

    set fp [open $outfile w]

    puts $fp [join [list \
        "DelayType" \
        "PathGroup" \
        "PathIndex" \
        "Slack" \
        "Startpoint" \
        "Endpoint" \
        "Point" \
        "PointDirection" \
        "Cell" \
        "RefName" \
        "VictimNet" \
        "NetDriver" \
        "AnnotatedDelayDelta" \
        "AnnotatedTransitionDelta" \
        "SI_Xtalk_Bumps" \
    ] "\t"]

    # Sanity hints
    if {![catch {set si_en [get_app_var si_enable_analysis]}]} {
        if {$si_en ne "true"} {
            puts "WARN: si_enable_analysis is not true. Crosstalk attributes may be empty/zero."
        }
    }

    set groups [__xt_get_path_groups]
    set total_paths 0
    set total_hits  0

    foreach delay_type {max min} {

        foreach group $groups {

            puts "INFO: scanning delay_type=$delay_type group=$group"

            set paths [__xt_get_timing_paths_for_group \
                $delay_type $group $max_paths_per_group $nworst $path_type $pba_mode]

            if {$paths eq ""} {
                continue
            }

            set pidx 0

            foreach_in_collection path $paths {

                incr pidx
                incr total_paths

                set slack [__xt_get_attr $path slack "NA"]
                set sp    [__xt_get_path_attr_name $path startpoint]
                set ep    [__xt_get_path_attr_name $path endpoint]

                set points [__xt_get_attr $path points ""]

                if {$points eq "" || $points eq "NA"} {
                    continue
                }

                foreach_in_collection tp $points {

                    set obj [__xt_get_point_object $tp]

                    if {$obj eq ""} {
                        continue
                    }

                    set point_name [__xt_obj_name $obj "NA"]

                    if {$point_name eq "NA"} {
                        continue
                    }

                    # Crosstalk delay delta on timing point
                    set delay_delta [__xt_get_first_attr $tp \
                        {annotated_delay_delta annotated_delta_delay} "0.0"]

                    # Crosstalk delta transition on timing point
                    set tran_delta [__xt_get_first_attr $tp \
                        {annotated_delta_transition annotated_transition_delta} "0.0"]

                    # Detailed aggressor/crosstalk bump info, if available
                    set bumps [__xt_get_first_attr $tp \
                        {si_xtalk_bumps} "NA"]

                    set abs_dd [__xt_abs $delay_delta]
                    set abs_td [__xt_abs $tran_delta]

                    # Report if either delay delta or transition delta is meaningful,
                    # or if SI bump attribute exists.
                    if {$abs_dd <= $delay_delta_threshold && \
                        $abs_td <= $tran_delta_threshold && \
                        $bumps eq "NA"} {
                        continue
                    }

                    set dir [__xt_get_attr $obj direction "NA"]

                    set net [__xt_get_net_of_obj $obj]
                    set net_name [__xt_obj_name $net "NA"]
                    set drv_name [__xt_get_driver_of_net $net]

                    set cell_name [__xt_get_cell_of_obj $obj]
                    set ref_name  [__xt_get_ref_of_cell_name $cell_name]

                    # Avoid embedded tabs/newlines in bumps field
                    regsub -all {\t} $bumps " " bumps
                    regsub -all {\n} $bumps " " bumps

                    puts $fp [join [list \
                        $delay_type \
                        $group \
                        $pidx \
                        $slack \
                        $sp \
                        $ep \
                        $point_name \
                        $dir \
                        $cell_name \
                        $ref_name \
                        $net_name \
                        $drv_name \
                        $delay_delta \
                        $tran_delta \
                        $bumps \
                    ] "\t"]

                    incr total_hits
                }
            }
        }
    }

    close $fp

    puts "INFO: scanned timing paths : $total_paths"
    puts "INFO: xtalk points found   : $total_hits"
    puts "INFO: wrote                : $outfile"
}

# Execution
report_xtalk_from_timing_path_objects 0.002 0.002 50000 50 xtalk_path_points.tsv full_clock_expanded none
