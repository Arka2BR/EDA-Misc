############################
# Script made by aadhika1
############################
#
proc get_fastest_driving_clock {clks} {
    set min_period 1e99
    set min_clk ""

    foreach clk $clks {
		set clk_name [get_clocks $clk]
        set p [get_attribute $clk_name period]
        if {$p < $min_period} {
            set min_period $p
            set min_clk [get_object_name $clk_name]
        }
    }

	return "$min_clk $min_period"
}

proc get_manhattan_dist {in_pin out_pin} {
    set in_x  [get_attribute [get_pins -hierarchical $in_pin] x_coordinate]
    set in_y  [get_attribute [get_pins -hierarchical $in_pin] y_coordinate]
    set out_x [get_attribute [get_pins -hierarchical $out_pin] x_coordinate]
    set out_y [get_attribute [get_pins -hierarchical $out_pin] y_coordinate]

	#puts "$in_x $in_y $out_x $out_y"

    set manhattan_distance [expr {abs($in_x - $out_x) + abs($in_y - $out_y)}]

	return $manhattan_distance

}

proc _ft_get_smd_rate {period cons_mode} {
    set ft_smd_rate 0
	#puts $cons_mode

    if {$cons_mode == "functapeout"} {
        if {$period <= 0.5 } {
			set ft_smd_rate 0.40
		} elseif {$period <= 0.714 && $period > 0.5} {
			set ft_smd_rate 0.60
		} elseif {$period <= 1.0 && $period > 0.714} {
			set ft_smd_rate 0.80
		} elseif {$period <= 2.0 && $period > 1.0} {
			set ft_smd_rate 1.00
		} elseif {$period > 2.0} {
			set ft_smd_rate 1.5
		}
    } elseif {$cons_mode == "functurbo_l3"} {
        if {$period <= 0.5} {
            set ft_smd_rate 0.35
        } elseif {$period <= 0.714 && $period > 0.5} {
            set ft_smd_rate 0.50
        } elseif {$period <= 1.0 && $period > 0.714} {
            set ft_smd_rate 0.60
        } elseif {$period <= 2.0 && $period > 1.0} {
            set ft_smd_rate 0.70
        } elseif {$period > 2.0} {
            set ft_smd_rate 0.80
        }
    }

    return $ft_smd_rate
}

proc _get_pin_name {full_pin_name} {
	set pin_name_split [split $full_pin_name "/"]
	set last_index_value [expr {[llength $pin_name_split] - 1}]
	set pin_base_name [lindex $pin_name_split $last_index_value]

	return $pin_base_name
}

proc gen_ft_smd {ft_pins cons_mode outfile} {
	# Open file for dumping
	set outfh [open $outfile w]

	foreach_in_collection ft_pin $ft_pins {

		puts "Attempting Budget for Input Pin : [get_object_name $ft_pin]"
		puts $outfh "# Top Input Pin : [get_object_name $ft_pin]"

		# Fanin
		set fanin_pins [filter_collection [get_pins -of_objects [all_fanin -to $ft_pin -flat -startpoints_only -only_cells -quiet]] "is_clock_pin==true"]
		set fanin_clocks [lsort -unique [get_object_name [get_attribute -quiet $fanin_pins clocks]]]

		# Fanout
		set fanout_pins [filter_collection [get_pins -of_objects [all_fanout -from $ft_pin -flat -endpoints_only -only_cells -quiet ]] "is_clock_pin==true"]
		set fanout_clocks [lsort -unique [get_object_name [get_attribute -quiet $fanout_pins clocks]]]

		# Exit FT port
		set exit_pins [filter_collection [all_fanout -from $ft_pin -levels 100] "full_name=~*FT_OUT* || full_name=~*_SPLIT_*"]
		set exit_pin_names [get_object_name $exit_pins]

		# All clocks on FT pin
		set all_ft_clocks [concat $fanin_clocks $fanout_clocks]

		set min_clk "NA"
		set min_period "NA"
		set ft_smd_rate 1.0
		set manhattan_dist 0
		set smd_tightness_factor 1.0

		# Get fastest clock
		if {[llength $all_ft_clocks] > 0} {
			lassign [get_fastest_driving_clock $all_ft_clocks] min_clk min_period
		}
		
		# Get SMD Rate
		if {$min_period != "NA"} {
			set ft_smd_rate [_ft_get_smd_rate $min_period $cons_mode]
		}

		# Get Manhattan Distance & write max_delay
		if {[sizeof_collection $exit_pins] != 0} {
			foreach_in_collection out_pin $exit_pins {

				set manhattan_dist [get_manhattan_dist $ft_pin $out_pin]
				set max_delay_value [expr {($manhattan_dist / (1000.0 ** 2.0)) * $ft_smd_rate * $smd_tightness_factor}]
				set input_pin_full_name [get_object_name $ft_pin]
				set input_pin_base_name [_get_pin_name $input_pin_full_name]
				set output_pin_full_name [get_object_name $out_pin]
				set output_pin_base_name [_get_pin_name $output_pin_full_name]

				# Write Budget
				puts $outfh "# Top Output Pin : $output_pin_full_name"
				puts $outfh "# Clock : $min_clk, Period : $min_period"
				puts $outfh "# SMD Rate : $ft_smd_rate"
				puts $outfh "# Manhattan Distance : $manhattan_dist"
				puts $outfh "set_max_delay $max_delay_value -from {$input_pin_base_name} -to {$output_pin_base_name};"
			}
		} else {
			puts $outfh "# No Output Pin available !"
			puts $outfh "# No Budgets Generated !"
		}
	

		puts $outfh "####################\n"

	}
	close $outfh

}

proc gen_ft_budget {design_name outdir} {

	# Var Setup
	global glob_cons_mode
	set DESIGN $design_name
	set OUTFILE_NAME "${DESIGN}_ft_budget.tcl"
	set OUTFILE "${outdir}/${OUTFILE_NAME}"

	# Get FT data
	set hier_name [get_object_name [get_cells -hierarchical -filter "ref_name==$DESIGN"]]
	set input_ft_pins [get_pins -hierarchical -filter "full_name=~$hier_name/*_FT_IN_*"]
	set output_ft_pins [get_pins -hierarchical -filter "full_name=~$hier_name/*_FT_OUT_*"]


	# Retrieve Input FT clock data
	puts "\[INFO\] Initiating FT Budgeting..."
	gen_ft_smd $input_ft_pins $glob_cons_mode $OUTFILE
	puts "\[INFO\] Generated FT Budget : $OUTFILE"

}

global glob_cons_mode
set glob_cons_mode $CONS_MODE
set DESIGN_NAME <Design-name>
set OUTDIR_PATH [pwd]
gen_ft_budget $DESIGN_NAME $OUTDIR_PATH
