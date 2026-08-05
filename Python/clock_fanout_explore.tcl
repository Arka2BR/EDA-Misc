# ================================================================
# Created by arkaprab 12/7/2026
# ================================================================

proc report_data_path_high_fanout {threshold {outfile "data_path_high_fanout.rpt"}} {

    set fp [open $outfile w]

    puts $fp "# Data-path instances with direct fanout > $threshold"
    puts $fp "# Design: [current_design]"
    puts $fp "#"
    puts $fp [format "%-8s %-90s %-90s %-20s %-90s" \
        "Fanout" "Instance" "Driver_Pin" "Ref_Name" "Net"]
    puts $fp [string repeat "-" 310]

    # ------------------------------------------------------------
    # Build lookup table of clock-tree objects to exclude.
    # This is whole-design clock-tree traversal.
    # ------------------------------------------------------------
    array set is_clk_obj {}

    set clk_objs [all_fanout -quiet -clock_tree -flat]

    foreach_in_collection obj $clk_objs {
        set is_clk_obj([get_object_name $obj]) 1
    }

    # ------------------------------------------------------------
    # Iterate over all leaf cells in the design.
    # ------------------------------------------------------------
    set all_cells [get_cells -quiet -hierarchical *]

    if {[sizeof_collection $all_cells] == 0} {
        puts "WARN: No cells found in design."
        close $fp
        return
    }

    array set seen_driver_pin {}

    foreach_in_collection cell $all_cells {

        set inst_name [get_object_name $cell]

        # Skip hierarchical cells if attribute exists.
        if {![catch {set is_hier [get_attribute $cell is_hierarchical]}]} {
            if {$is_hier == "true"} {
                continue
            }
        }

        # Skip cells that are themselves part of clock tree.
        if {[info exists is_clk_obj($inst_name)]} {
            continue
        }

        if {[catch {set ref_name [get_attribute $cell ref_name]}]} {
            set ref_name "NA"
        }

        set out_pins [get_pins -quiet -of_objects $cell -filter "direction == out"]

        foreach_in_collection op $out_pins {

            set op_name [get_object_name $op]

            # De-dup
            if {[info exists seen_driver_pin($op_name)]} {
                continue
            }
            set seen_driver_pin($op_name) 1

            # Skip driver pins that are part of clock tree.
            if {[info exists is_clk_obj($op_name)]} {
                continue
            }

            set nets [get_nets -quiet -of_objects $op]
            if {[sizeof_collection $nets] == 0} {
                continue
            }

            foreach_in_collection net $nets {

                set net_name [get_object_name $net]

                # Skip nets that are part of clock tree.
                if {[info exists is_clk_obj($net_name)]} {
                    continue
                }

                # Direct load pins on driven net.
                set load_pins [get_pins -quiet -leaf -of_objects $net -filter "direction == in"]

                set fo 0

                foreach_in_collection lp $load_pins {

                    set lp_name [get_object_name $lp]

                    # Exclude clock-tree load pins.
                    if {[info exists is_clk_obj($lp_name)]} {
                        continue
                    }

                    incr fo
                }

                if {$fo > $threshold} {
                    puts $fp [format "%-8d %-90s %-90s %-20s %-90s" \
                        $fo $inst_name $op_name $ref_name $net_name]
                }
            }
        }
    }

    close $fp
    puts "INFO: Report written to $outfile"
}

report_data_path_high_fanout 30
