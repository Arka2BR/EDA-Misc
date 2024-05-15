package require Tcl 8.5
package require tums 1.0
package require tums::utility 1.0
package provide tums::critical.path.analysis 1.0

### CRITICAL PATH ANALYSIS METRIC
namespace eval tums::critical.path.analysis {

# Import general purpose procedures 
namespace import -force ::tums::utility::*

# Set default run parameters
variable max_slack 0.0
variable num_paths 100
variable hierarchical_depth 2
variable scenarios ""
variable pba_mode "none"
variable groups ""
variable inc_io_paths "false"
variable inc_mem_paths "false"

# Dictionary templates
variable path_table_template [dict create \
    slack 0 \
    slack_adjustment 0 \
    sigma 0 \
    delay_type "" \
    path_group "" \
    scenario "" \
    stages 0 \
    total_fanout 0 \
    total_cell_delay 0 \
    total_net_delay 0 \
    skew 0 \
    mean_cppr 0 \
    cppr 0 \
    check_value_mean 0 \
    check_value 0 \
    frequency 0 \
    startpoint "" \
    endpoint "" \
]

# List of numeric path data keys
variable numeric_path_keys [list slack slack_adjustment stages total_fanout total_cell_delay \
    total_net_delay skew mean_cppr cppr check_value_mean check_value]

# TODO: cell_delay rank and unique cell count
variable internal_cell_table_template [dict create \
    cell_count 0 \
    cell_delay 0 \
    mean_cell_delay 0 \
    rise_time 0 \
    rise_count 0 \
    fall_time 0 \
    fall_count 0 \
    output_net_delay 0 \
    fanout 0 \
]

# TODO: unique cell count, fc_shell via resistance
variable net_table_template [dict create \
    cell_count 0 \
    net_delay 0 \
    mean_net_delay 0 \
    rise_time 0 \
    rise_count 0 \
    fall_time 0 \
    fall_count 0 \
    total_cap 0 \
    wire_cap 0 \
    xcap 0 \
    delta_delay 0 \
    metal_R 0 \
    wire_length { total 0 } \
]

# Initialize wire length dictionary to maintain order across all sections
foreach layer $tums::metal_layers {
    dict set net_table_template wire_length $layer 0
}

# TODO: unique cell count
variable startpoint_table_template [dict create \
    cell_count 0 \
    c2q_delay 0 \
    mean_c2q_delay 0 \
    rise_time 0 \
    rise_count 0 \
    fall_time 0 \
    fall_count 0 \
    output_net_delay 0 \
    fanout 0 \
]

# TODO: unique cell count
variable endpoint_table_template [dict create \
    cell_count 0 \
    skew 0 \
    setup_time 0 \
    setup_count 0 \
    hold_time 0 \
    hold_count 0 \
]

# Perform some net data calculations outside the timing point for loop to save time
proc process_data {data} {
    # Calculate total wire length
    dict with data {
        dict set wire_length total [lsum [dict values $wire_length]]
    }
    return $data
}

# Recursively use the process data proc on a dictionary
proc process_data_recursive {raw_data {leaf_key cell_count}} {
    set data [dict create]

    # Process the dictionary if it holds info for a basis
    if {[dict exists $raw_data $leaf_key]} {
        return [process_data $raw_data]
    }

    # Else move one level deeper
    dict for {key nested_dict} $raw_data {
        dict set data $key [process_data_recursive $nested_dict]
    }
    return $data
}

# Recursively calculate total values for nested hinsts
proc summate_hinst_tree {raw_data {leaf_key cell_count} {top_level true}} {
    set data            [dict create]
    set nested_totals   [list]
    
    # If a leaf hinst, no need to look deeper
    if {[dict exists $raw_data $leaf_key]} {
        return $raw_data 
    }

    # Upgrade lone "Other" entries as these are just totals for the whole hinst
    if {[dict keys $raw_data] eq "Other"} {
        if {$top_level} {
            return [list Total [lindex $raw_data 1]]
        } else {
            return [lindex $raw_data 1]
        }
    }

    # Else process all the hinsts nested inside the current hinst
    dict for {hinst hinst_info} $raw_data {
        # Process the next level down first
        dict set data $hinst [summate_hinst_tree $hinst_info $leaf_key false]
        
        # Get the totals for the nested hinst
        if {[dict exists $data $hinst $leaf_key]} {
            lappend nested_totals [dict get $data $hinst]
        } else {
            lappend nested_totals [dict get $data $hinst Total]
        }
    }

    # Sum the totals for the nested hinsts to get the totals for the current hinst
    set Total [dict_combine $nested_totals]
    set data [linsert $data 0 Total ${Total}]
    return $data
}

# Combine cell data dictionaries with the same family
proc summate_cell_family {raw_data} {
    # Setup dictionaries
    set family_dict_list [dict create]
    set data [dict create]

    # Create a list of dicts for each cell family
    dict for {cell_ref cell_data} $raw_data {
        if {[regexp $tums::re_node $cell_ref]} {
            regexp $tums::re_family $cell_ref match family
            dict lappend family_dict_list $family $cell_data 
        }
    }

    # Combine each list into one dictionary per cell family
    dict for {family dict_list} $family_dict_list {
        dict set data $family [dict_combine $dict_list]
    }
    
    # Alphabetize the families
    return [lsort -stride 2 $data]
}

# Combine cell data dictionaries with the same vt_char
proc summate_vt_char {raw_data} {
    # Get variables
    global tums::re_node
    global tums::re_vt_char
    global tums::vt_char_type_map
    global tums::vt_type_order

    # Setup dictionaries with Vt type order
    set vt_type_dict_list [dict create]
    set data [dict create]
    foreach vt_type $vt_type_order {
        dict set data $vt_type {}
    }

    # Create a list of dicts for each vt_type
    dict for {cell_ref cell_data} $raw_data {
        if {[regexp $re_node $cell_ref]} {
            regexp $re_vt_char $cell_ref match vt_char
            set vt_type [dict get $vt_char_type_map $vt_char]
            dict lappend vt_type_dict_list $vt_type $cell_data
        }
    }

    # Combine each list into one dictionary per vt_type
    dict for {vt_type dict_list} $vt_type_dict_list {
        dict set data $vt_type [dict_combine $dict_list]
    }
    return $data
}

# Combine cell data dictionaries with the same drive strength
proc summate_drive_strength {raw_data} {
    # Get variables
    global tums::re_node
    global tums::re_drive_strength
    
    # Setup dictionaries
    set data [dict create]
    set drive_dict_list [dict create]

    # Create a list of dicts for each vt_type
    dict for {cell_ref cell_data} $raw_data {
        if {[regexp $re_node $cell_ref]} {
            regexp $re_drive_strength $cell_ref match drive_strength
            dict lappend drive_dict_list $drive_strength $cell_data
        }
    }

    # Combine each list into one dictionary per vt_type
    dict for {drive_strength dict_list} $drive_dict_list {
        dict set data $drive_strength [dict_combine $dict_list]
    }
    
    # Alphabetize the drive strength
    set data [lsort -stride 2 $data]
    return $data
}

# Combine path data dictionaries with the same path group
proc summate_path_group {raw_data} {
    variable numeric_path_keys

    # Create a list of dicts for each cell family
    dict for {path_id path_data} $raw_data {
        # Get path group
        set path_group [dict get $path_data path_group]

        # Extract numeric values
        set numeric_data [dict create]
        foreach key $numeric_path_keys {
            dict set numeric_data $key [dict get $path_data $key]
        }

        # Add the numeric data to the dict list
        dict lappend group_dict_list $path_group $numeric_data
    }

    # Combine each list into one dictionary per cell family
    dict for {path_group dict_list} $group_dict_list {
        dict set data $path_group [dict_combine $dict_list]
        dict set data $path_group [linsert [dict get $data $path_group] 0 path_count [llength $dict_list]]
    }
    
    # Alphabetize the path group names
    return [lsort -stride 2 $data]
}

# Get the top N critical paths in the design (fc_shell)
proc fc_shell_get_paths {} {
    variable output_dir
    variable max_slack
    variable num_paths
    variable scenarios
    variable pba_mode
    variable groups
    variable inc_io_paths
    variable inc_mem_paths

    # Initialize exclude collection as empty
    global exclude_col
    set exclude_col [add_to_collection "" ""]

    # Initialize command options with 
    set opts "-max_paths $num_paths -path_type full_clock -pba_mode $pba_mode"

    # Add max_slack if value is specified
    if {[string is double -strict $max_slack]} {
        set opts [concat $opts "-slack_lesser_than $max_slack"]
    }

    # Add scenarios if scenarios are specified
    if {!($scenarios eq "")} {
        set opts [concat $opts "-scenarios $scenarios"]
    }

    # Specify path groups
    if {$groups ne ""} {
        set opts [concat $opts "-groups $groups"]
    }

    # Exclude ports unless io paths are to be included
    if {!$inc_io_paths} {
        set ports [get_ports]
        set ports [remove_from_collection $ports [get_ports "VDD VSS"]]
        append_to_collection exclude_col $ports
    }

    # Exclude macro pins unless memory paths are to be included
    if {!$inc_mem_paths} {
        set macros [get_cells -phy -filter "is_hard_macro || is_soft_macro"]
        set macro_pins [get_pins -of_objects $macros]
        append_to_collection exclude_col $macro_pins
    }

    # Add exclude option if needed
    if {[sizeof_collection $exclude_col] > 0} {
        set opts [concat $opts "-exclude \$exclude_col"]
    }

    # Report timing
    eval report_timing {*}$opts > $output_dir/timing.rpt

    # Get the timing paths
    puts "Acquiring paths with cmd: get_timing_paths $opts"
    return [eval get_timing_paths {*}$opts]
}

# Main procedure for Fusion Compiler
proc fc_shell {} {
    variable hierarchical_depth

    # Data dictionary templates
    variable path_table_template
    variable internal_cell_table_template
    variable net_table_template
    variable startpoint_table_template
    variable endpoint_table_template

    # Data dictionaries
    set path_data       [dict create cell_ref {} hinst {}]
    set cell_data       [dict create cell_ref {} hinst {}]
    set net_data        [dict create cell_ref {} hinst {}]
    set startpoint_data [dict create cell_ref {} hinst {}]
    set endpoint_data   [dict create cell_ref {} hinst {}]

    # Get the critical timing paths
    set paths [fc_shell_get_paths]

    # Get general path information
    set delay_types    [get_attribute $paths delay_type];     # Max = setup, min = hold
    set path_groups    [get_attribute $paths path_group_name]
    set path_scenarios [get_attribute $paths scenario_name]

    # Start and end points
    set startpoints [get_attribute -quiet -value_list $paths startpoint.full_name]
    set endpoints   [get_attribute -quiet -value_list $paths endpoint.full_name]

    # Slack
    set slacks [get_attribute -quiet -value_list $paths slack]

    # CPPR values
    set cppr_means    [get_attribute -quiet -value_list $paths variation_common_path_pessimism.mean]
    set cppr_std_devs [get_attribute -quiet -value_list $paths variation_common_path_pessimism.std_dev]

    # Clock period
    set clk_periods [get_attribute -quiet -value_list $paths endpoint_clock_period]

    # AAT, RAT, and slack statistical adjustment
    set arrival_times  [get_attribute -quiet -value_list $paths arrival]
    set required_times [get_attribute -quiet -value_list $paths required]
    
    # Latency and skew
    set startpoint_latencies      [get_attribute -quiet -value_list $paths startpoint_clock_latency]
    set endpoint_latencies        [get_attribute -quiet -value_list $paths endpoint_clock_latency]
    set endpoint_latency_means    [get_attribute -quiet -value_list $paths variation_endpoint_clock_latency.mean]
    set endpoint_latency_std_devs [get_attribute -quiet -value_list $paths variation_endpoint_clock_latency.std_dev]

    # Total fanout
    set total_fanouts [get_attribute -quiet -value_list $paths total_fanout]

    # Combinatorial delay totals
    set total_cell_delays [get_attribute -quiet -value_list $paths total_cell_delay]
    set total_net_delays  [get_attribute -quiet -value_list $paths total_net_delay]

    # Iterate through the critical paths
    set i 0
    puts "Iterating through [sizeof_collection $paths] timing_paths"
    foreach_in_collection path $paths {
        set path_id [expr $i+1]

        # Get timing points
        set points [get_attribute $path points]

        # Access path attribute lists
        set delay_type               [lindex $delay_types               $i]
        set path_scenario            [lindex $path_scenarios            $i]
        set slack                    [lindex $slacks                    $i]
        set arrival_time             [lindex $arrival_times             $i]
        set required_time            [lindex $required_times            $i]
        set startpoint_latency       [lindex $startpoint_latencies      $i] 
        set endpoint_latency         [lindex $endpoint_latencies        $i]
        set endpoint_latency_mean    [lindex $endpoint_latency_means    $i]
        set endpoint_latency_std_dev [lindex $endpoint_latency_std_devs $i]
        set clk_period               [lindex $clk_periods               $i]
        set cppr_mean                [lindex $cppr_means                $i]
        set cppr_std_dev             [lindex $cppr_std_devs             $i]

        # Get setup / hold time variation info
        if {$delay_type eq "max"} {
            set check_value_mean    [get_attribute -quiet $path variation_endpoint_setup_time_value.mean]
            set check_value_std_dev [get_attribute -quiet $path variation_endpoint_setup_time_value.std_dev]
        } else {
            set check_value_mean    [get_attribute -quiet $path variation_endpoint_hold_time_value.mean]
            set check_value_std_dev [get_attribute -quiet $path variation_endpoint_hold_time_value.std_dev]
        }
        
        # Set values to 0 if empty string is passed
        if {$slack                    eq ""} {set slack                    0.0}
        if {$arrival_time             eq ""} {set arrival_time             0.0}
        if {$required_time            eq ""} {set required_time            0.0}
        if {$startpoint_latency       eq ""} {set startpoint_latency       0.0}
        if {$endpoint_latency         eq ""} {set endpoint_latency         0.0}
        if {$endpoint_latency_mean    eq ""} {set endpoint_latency_mean    0.0}
        if {$endpoint_latency_std_dev eq ""} {set endpoint_latency_std_dev 0.0}
        if {$clk_period               eq ""} {set clk_period               0.0}
        if {$cppr_mean                eq ""} {set cppr_mean                0.0}
        if {$cppr_std_dev             eq ""} {set cppr_std_dev             0.0}
        if {$check_value_mean         eq ""} {set check_value_mean         0.0}
        if {$check_value_std_dev      eq ""} {set check_value_std_dev      0.0}

        # Convert variation values from ns to ps
        set endpoint_latency_mean    [expr $endpoint_latency_mean*1000]
        set endpoint_latency_std_dev [expr $endpoint_latency_std_dev*1000]
        set cppr_mean                [expr $cppr_mean*1000]
        set cppr_std_dev             [expr $cppr_std_dev*1000]
        set check_value_mean         [expr $check_value_mean*1000]
        set check_value_std_dev      [expr $check_value_std_dev*1000]

        # Calculate statistical adjustment for the path
        set statistical_adjustment [expr -($required_time - $arrival_time - $slack)]
        
        # Calculate clock skew for the path
        set skew [expr $endpoint_latency - $startpoint_latency]
        
        # Calculate number of stages
        set stages [expr floor([sizeof_collection $points]/2.0)]

        # Calculate path frequency (GHz) (assumes times are in ps)
        set path_frequency [expr 1e3/($clk_period - $slack)]

        # Get corner sigma
        redirect -variable pocv_rpt {report_ocvm -type pocvm -corner_sigma -scenario $path_scenario}
        regexp {Corner Sigma\s+([\d\.]+)} $pocv_rpt match corner_sigma

        # Calculate CPPR with variation
        set cppr_arrival_mean [expr $clk_period + $endpoint_latency_mean + $cppr_mean]
        set cppr_variation [RSS [list $endpoint_latency_std_dev $cppr_std_dev] true]
        set cppr_arrival [expr $cppr_arrival_mean - $corner_sigma * $cppr_variation]
        set cppr [expr $cppr_arrival - $endpoint_latency - $clk_period]

        # Calculate check_value with variation
        set check_value_arrival_mean [expr $cppr_arrival_mean + $check_value_mean]
        set check_value_variation [RSS [list $cppr_variation $check_value_std_dev] true]
        set check_value_arrival [expr $check_value_arrival_mean - $corner_sigma * $check_value_variation]
        set check_value [expr $check_value_arrival - $cppr_arrival]

        # Record path data
        dict set path_data id $path_id slack            $slack
        dict set path_data id $path_id slack_adjustment $statistical_adjustment
        dict set path_data id $path_id sigma            $corner_sigma
        dict set path_data id $path_id delay_type       $delay_type
        dict set path_data id $path_id path_group       [lindex $path_groups $i]
        dict set path_data id $path_id scenario         $path_scenario
        dict set path_data id $path_id stages           $stages
        dict set path_data id $path_id total_fanout     [lindex $total_fanouts $i]
        dict set path_data id $path_id total_cell_delay [lindex $total_cell_delays $i]
        dict set path_data id $path_id total_net_delay  [lindex $total_net_delays $i]
        dict set path_data id $path_id skew             $skew 
        dict set path_data id $path_id mean_cppr        $cppr_mean
        dict set path_data id $path_id cppr             $cppr
        dict set path_data id $path_id check_value_mean $check_value_mean
        dict set path_data id $path_id check_value      $check_value
        dict set path_data id $path_id frequency        $path_frequency
        dict set path_data id $path_id startpoint       [lindex $startpoints $i]
        dict set path_data id $path_id endpoint         [lindex $endpoints $i]

        # Get pin / ports of the path
        set objects [get_attribute $points object]

        # Get pin / port information
        set object_class  [get_attribute $objects object_class]
        set is_net_load   [get_attribute $objects is_net_load]
        set is_net_driver [get_attribute $objects is_net_driver]
        set is_clock_pin  [get_attribute -quiet -value_list $objects is_clock_pin]; # ports are likely to return "" for this attribute
        
        # Get delay from one timing point to the next
        set delays [get_attribute $points delay]

        # Get transition time for the timing points
        set trans [get_attribute $points transition]

        # Get net capacitance for the timing points
        set caps [get_attribute $points capacitance]

        # Get the mean and std dev (sensit) for the delay time
        set delay_means    [get_attribute $points variation_increment.mean]
        set delay_std_devs [get_attribute $points variation_increment.std_dev]
        
        # Get the mean and std dev (sensit) for the arrival time
        set arrival_means    [get_attribute $points variation_arrival.mean]
        set arrival_std_devs [get_attribute $points variation_arrival.std_dev]

        # Rise and fall information
        set rise_fall [get_attribute $points rise_fall]

        # Fanouts
        set fanouts [get_attribute $points num_fanout]

        # Delta delay for nets (value is stored on load pin timing points)
        set delta_delays [get_attribute -quiet -value_list $points delta_delay]

        # Iterate through the points
        for {set j 0} {$j < [sizeof_collection $points]} {incr j} {
            set object [index_collection $objects $j]

            # Get cell information if point is a pin
            if {[lindex $object_class $j] eq "pin"} {
                set cell_ref  [get_attribute $object cell.lib_cell.name]
                set hier_path [get_attribute -quiet $object cell.parent_cell.full_name]
            } else {
                continue
            }

            # Determine hierarchy up to the max level
            set hierarchy [split $hier_path "/"]
            lappend hierarchy "Other"
            set hierarchy [lrange $hierarchy 0 $hierarchical_depth-1]

            # Fill out data for startpoint
            if {[lindex $is_net_driver $j] && [lindex $is_clock_pin $j-1] eq "true"} {
                # Copy in template for a new entry
                if {![dict exists $startpoint_data cell_ref $cell_ref]} {
                    dict set startpoint_data cell_ref $cell_ref $startpoint_table_template
                }
                if {![dict exists $startpoint_data hinst {*}$hierarchy]} {
                    dict set startpoint_data hinst {*}$hierarchy $startpoint_table_template
                }

                # Add to the cell ref entry
                dict_add startpoint_data [list cell_ref $cell_ref cell_count] 1
                dict_add startpoint_data [list cell_ref $cell_ref c2q_delay] [lindex $delays $j]
                dict_add startpoint_data [list cell_ref $cell_ref mean_c2q] [lindex $delay_means $j]
                dict_add startpoint_data [list cell_ref $cell_ref output_net_delay] [lindex $delays $j+1]
                dict_add startpoint_data [list cell_ref $cell_ref fanout] [lindex $fanouts $j]

                # Add to the hinst entry
                dict_add startpoint_data [list hinst {*}$hierarchy cell_count] 1
                dict_add startpoint_data [list hinst {*}$hierarchy c2q_delay] [lindex $delays $j]
                dict_add startpoint_data [list hinst {*}$hierarchy mean_c2q] [lindex $delay_means $j]
                dict_add startpoint_data [list hinst {*}$hierarchy output_net_delay] [lindex $delays $j+1]
                dict_add startpoint_data [list hinst {*}$hierarchy fanout] [lindex $fanouts $j]

                # Add to rise or fall time entry
                if {[lindex $rise_fall $j] eq "rise"} {
                    dict_add startpoint_data [list cell_ref $cell_ref  rise_time] [lindex $trans $j]
                    dict_add startpoint_data [list cell_ref $cell_ref  rise_count] 1
                    dict_add startpoint_data [list hinst {*}$hierarchy rise_time] [lindex $trans $j]
                    dict_add startpoint_data [list hinst {*}$hierarchy rise_count] 1
                } else {
                    dict_add startpoint_data [list cell_ref $cell_ref  fall_time] [lindex $trans $j]
                    dict_add startpoint_data [list cell_ref $cell_ref  fall_count] 1
                    dict_add startpoint_data [list hinst {*}$hierarchy fall_time] [lindex $trans $j]
                    dict_add startpoint_data [list hinst {*}$hierarchy fall_count] 1
                }
                

            # Fill out data for internal cells
            } elseif {[lindex $is_net_driver $j] && !([lindex $is_clock_pin $j-1] eq "true")} {
                # Copy in template for a new entry
                if {![dict exists $cell_data cell_ref $cell_ref]} {
                    dict set cell_data cell_ref $cell_ref $internal_cell_table_template
                }
                if {![dict exists $cell_data hinst {*}$hierarchy]} {
                    dict set cell_data hinst {*}$hierarchy $internal_cell_table_template
                }

                # Add to the cell ref entry
                dict_add cell_data [list cell_ref $cell_ref cell_count] 1
                dict_add cell_data [list cell_ref $cell_ref cell_delay] [lindex $delays $j]
                dict_add cell_data [list cell_ref $cell_ref mean_cell_delay] [lindex $delay_means $j]
                dict_add cell_data [list cell_ref $cell_ref output_net_delay] [lindex $delays $j+1]
                dict_add cell_data [list cell_ref $cell_ref fanout] [lindex $fanouts $j]
                
                # Add to the hinst entry
                dict_add cell_data [list hinst {*}$hierarchy cell_count] 1
                dict_add cell_data [list hinst {*}$hierarchy cell_delay] [lindex $delays $j]
                dict_add cell_data [list hinst {*}$hierarchy mean_cell_delay] [lindex $delay_means $j]
                dict_add cell_data [list hinst {*}$hierarchy output_net_delay] [lindex $delays $j+1]
                dict_add cell_data [list hinst {*}$hierarchy fanout] [lindex $fanouts $j]

                # Add to the rise or fall time entry
                if {[lindex $rise_fall $j] eq "rise"} {
                    dict_add cell_data [list cell_ref $cell_ref  rise_time] [lindex $trans $j]
                    dict_add cell_data [list cell_ref $cell_ref  rise_count] 1
                    dict_add cell_data [list hinst {*}$hierarchy rise_time] [lindex $trans $j]
                    dict_add cell_data [list hinst {*}$hierarchy rise_count] 1
                } else {
                    dict_add cell_data [list cell_ref $cell_ref  fall_time] [lindex $trans $j]
                    dict_add cell_data [list cell_ref $cell_ref  fall_count] 1
                    dict_add cell_data [list hinst {*}$hierarchy fall_time] [lindex $trans $j]
                    dict_add cell_data [list hinst {*}$hierarchy fall_count] 1
                }
            }

            # Fill out data for incident nets
            if {[lindex $is_net_driver $j]} {
                # Copy in template for a new entry
                if {![dict exists $net_data cell_ref $cell_ref]} {
                    dict set net_data cell_ref $cell_ref $net_table_template
                }
                if {![dict exists $net_data hinst {*}$hierarchy]} {
                    dict set net_data hinst {*}$hierarchy $net_table_template
                }

                # Get delta delay if the net has one
                set delta_delay [lindex $delta_delays $j+1]
                if {$delta_delay eq ""} {set delta_delay 0.0}

                # Report parasitics for the net
                set net [get_nets -of_objects [index_collection $objects $j]]
                redirect -variable parasitic_rpt {report_parasitics -xcap -[lindex $rise_fall $j+1] -scenario $path_scenario $net}

                # Failsafe for parasitic info
                set wire_cap 0
                set metal_R 0
                set xcap 0
                set via_R 0

                # Extract parasitic info
                regexp {Wire\s+capacitance\s+=\s+([\d\.]+)} $parasitic_rpt match wire_cap
                regexp {Total\s+resistance\s+=\s+([\d\.]+)} $parasitic_rpt match metal_R
                regexp {Total\s+xcap\s+=\s+([\d\.]+)}       $parasitic_rpt match xcap

                # Add to the cell ref entry
                dict_add net_data [list cell_ref $cell_ref cell_count] 1
                dict_add net_data [list cell_ref $cell_ref net_delay] [lindex $delays $j+1]
                dict_add net_data [list cell_ref $cell_ref mean_net_delay] [lindex $delay_means $j+1]
                dict_add net_data [list cell_ref $cell_ref total_cap] [lindex $caps $j]
                dict_add net_data [list cell_ref $cell_ref wire_cap] $wire_cap
                dict_add net_data [list cell_ref $cell_ref xcap] $xcap
                dict_add net_data [list cell_ref $cell_ref delta_delay] $delta_delay
                dict_add net_data [list cell_ref $cell_ref metal_R] $metal_R
                #dict_add net_data [list cell_ref $cell_ref via_R] $via_R
                
                # Add to the hinst entry
                dict_add net_data [list hinst {*}$hierarchy cell_count] 1
                dict_add net_data [list hinst {*}$hierarchy net_delay] [lindex $delays $j+1]
                dict_add net_data [list hinst {*}$hierarchy mean_net_delay] [lindex $delay_means $j+1]
                dict_add net_data [list hinst {*}$hierarchy total_cap] [lindex $caps $j]
                dict_add net_data [list hinst {*}$hierarchy wire_cap] $wire_cap
                dict_add net_data [list hinst {*}$hierarchy xcap] $xcap
                dict_add net_data [list hinst {*}$hierarchy delta_delay] $delta_delay
                dict_add net_data [list hinst {*}$hierarchy metal_R] $metal_R
                #dict_add net_data [list hinst {*}$hierarchy via_R] $via_R
                
                # Add to rise or fall 
                if {[lindex $rise_fall $j+1] eq "rise"} {
                    dict_add net_data [list cell_ref $cell_ref  rise_time] [lindex $trans $j+1]
                    dict_add net_data [list cell_ref $cell_ref  rise_count] 1
                    dict_add net_data [list hinst {*}$hierarchy rise_time] [lindex $trans $j+1]
                    dict_add net_data [list hinst {*}$hierarchy rise_count] 1
                } else {
                    dict_add net_data [list cell_ref $cell_ref  fall_time] [lindex $trans $j+1]
                    dict_add net_data [list cell_ref $cell_ref  fall_count] 1
                    dict_add net_data [list hinst {*}$hierarchy fall_time] [lindex $trans $j+1]
                    dict_add net_data [list hinst {*}$hierarchy fall_count] 1
                }
                
                # Get wire length by layer
                set route_length [get_attribute [index_collection $objects $j] net.route_length]
                if {$route_length == 0} {continue}
                foreach pair $route_length {
                    lassign $pair layer length
                    dict_add net_data [list cell_ref $cell_ref  wire_length $layer] $length
                    dict_add net_data [list hinst {*}$hierarchy wire_length $layer] $length
                }
            }

            # Fill out endpoint data
            if {$j == [sizeof_collection $points]-1} {
                # Copy in template for a new entry
                if {![dict exists $endpoint_data cell_ref $cell_ref]} {
                    dict set endpoint_data cell_ref $cell_ref $endpoint_table_template
                }
                if {![dict exists $endpoint_data hinst {*}$hierarchy]} {
                    dict set endpoint_data hinst {*}$hierarchy $endpoint_table_template
                }

                # Add to the cell ref entry
                dict_add endpoint_data [list cell_ref $cell_ref cell_count] 1
                dict_add endpoint_data [list cell_ref $cell_ref skew] $skew

                # Add to the hinst entry
                dict_add endpoint_data [list hinst {*}$hierarchy cell_count] 1
                dict_add endpoint_data [list hinst {*}$hierarchy skew] $skew

                if {$delay_type eq "max"} {
                    dict_add endpoint_data [list cell_ref $cell_ref  setup_time] $check_value_mean
                    dict_add endpoint_data [list cell_ref $cell_ref  setup_count] 1
                    dict_add endpoint_data [list hinst {*}$hierarchy setup_time] $check_value_mean
                    dict_add endpoint_data [list hinst {*}$hierarchy setup_count] 1
                } else {
                    dict_add endpoint_data [list cell_ref $cell_ref  hold_time] $check_value_mean
                    dict_add endpoint_data [list cell_ref $cell_ref  hold_count] 1
                    dict_add endpoint_data [list hinst {*}$hierarchy hold_time] $check_value_mean
                    dict_add endpoint_data [list hinst {*}$hierarchy hold_count] 1
                }
            }

            set prev_is_clock_pin $is_clock_pin
        }

        # Move to the next path
        incr i
    }

    set data [dict create \
        paths $path_data \
        startpoints $startpoint_data \
        internal_cells $cell_data \
        nets $net_data \
        endpoints $endpoint_data \
    ]
    return $data
}

# Get the top N critical paths in the design (innovus) 
proc innovus_get_paths {} {
    variable max_slack
    variable num_paths
    variable scenarios
    variable pba_mode
	variable inc_io_paths

    # Initialize command options with 
    set opts "-max_paths $num_paths -path_type full_clock"

	if {!$inc_io_paths} {
		set opts [concat $opts "-skip_io_paths"]
	}

    # Add max_slack if value is specified
    if {[string is double -strict $max_slack]} {
        set opts [concat $opts "-max_slack $max_slack"]
    }

    # Add PBA mode
    if {$pba_mode ne "none"} {
        set opts [concat $opts "-retime path_slew_propagation"]
    }
    if {$pba_mode eq "exhaustive"} {
        set opts [concat $opts "-retime_mode exhaustive"]
    }

    # Add scenario if scenarios are specified
    if {!($scenarios eq "")} {
        if {[llength $scenarios]>1} {puts "WARN: only the first scenario in scenarios will be used with report_timing"}
        set opts [concat $opts "-view [lindex $scenarios 0]"]
    }
    
    # Store paths as collection
    set opts [concat $opts "-collection"]

    # Get the timing paths
    puts "Acquiring paths with cmd: report_timing $opts"
    return [report_timing {*}$opts]
	report_timing {*}$opts > critical_path_analysis_timing.rpt
}

# Main procedure for Innovus
proc innovus {} {
    variable hierarchical_depth

    # Get hierarchy delimiter
    set path_delimiter [get_db write_def_hierarchy_delimiter]
    
    # Data dictionary templates
    variable path_table_template
    variable internal_cell_table_template
    variable net_table_template
    variable startpoint_table_template
    variable endpoint_table_template

    # Data dictionaries
    set path_data       [dict create cell_ref {} hinst {}]
    set cell_data       [dict create cell_ref {} hinst {}]
    set net_data        [dict create cell_ref {} hinst {}]
    set startpoint_data [dict create cell_ref {} hinst {}]
    set endpoint_data   [dict create cell_ref {} hinst {}]

    # Get the critical timing paths
    set paths [innovus_get_paths]

    # Get sigma value
    set sigma [get_db timing_nsigma_multiplier]

    # Get general path information
    set delay_types    [get_db $paths .check_type]; # setup or hold
    set path_groups    [get_db $paths .path_group_name]
    set path_scenarios [get_db $paths .view_name]

    # Start and end points
    set startpoints [get_db $paths .launching_point.name]
    set endpoints   [get_db $paths .capturing_point.name]

    # Slack
    set slacks [get_db $paths .slack]

    # CPPR values
    set cpprs         [get_db $paths .cppr_adjustment]
    set cppr_means    [get_db $paths .cppr_adjustment_mean]
    set cppr_std_devs [get_db $paths .cppr_adjustment_sigma]

    # Check values
    set check_values      [get_db $paths .check_delay]
    set check_value_means [get_db $paths .check_delay_mean]

    # Clock period
    set clk_periods [get_db $paths .period]

    # AAT, RAT, and slack statistical adjustment
    set arrival_times  [get_db $paths .arrival]
    set required_times [get_db $paths .required_time]
    
    # Latency and skew
    set skews                     [get_db $paths .skew]
    set startpoint_latencies      [get_db $paths .launching_clock_latency]
    set endpoint_latencies        [get_db $paths .capturing_clock_latency]
    set endpoint_latency_means    [get_db $paths .capturing_clock_latency_mean]
    set endpoint_latency_std_devs [get_db $paths .capturing_clock_latency_stddev]

    # Iterate through the critical paths
    set i 0
    puts "Iterating through [sizeof_collection $paths] timing_paths"
    foreach_in_collection path $paths {
        set path_id [expr $i+1]

        # Get timing points
        set points [get_db $path .timing_points]
        set output_points [get_db $points -if {.pin.direction==out}]
        set input_points  [get_db $points -if {.pin.direction==in}]

        # Access path attribute lists
        set delay_type               [lindex $delay_types               $i]
        set path_scenario            [lindex $path_scenarios            $i]
        set slack                    [lindex $slacks                    $i]
        set arrival_time             [lindex $arrival_times             $i]
        set required_time            [lindex $required_times            $i]
        set startpoint_latency       [lindex $startpoint_latencies      $i] 
        set endpoint_latency         [lindex $endpoint_latencies        $i]
        set endpoint_latency_mean    [lindex $endpoint_latency_means    $i]
        set endpoint_latency_std_dev [lindex $endpoint_latency_std_devs $i]
        set clk_period               [lindex $clk_periods               $i]
        set check_value_mean         [lindex $check_value_means         $i]

        # Get rc_corner
        if {$delay_type eq "setup"} {
            set rc_corner [get_db analysis_view:$path_scenario .delay_corner.late_rc_corner.name]
        } else {
            set rc_corner [get_db analysis_view:$path_scenario .delay_corner.early_rc_corner.name]
        }

        # Calculate statistical adjustment for the path
        set statistical_adjustment [expr -($required_time - $arrival_time - $slack)]
        
        # Calculate clock skew for the path
        set skew [expr $endpoint_latency - $startpoint_latency]
        
        # Calculate number of stages
        set stages [expr floor([llength $points]/2.0)]

        # Calculate path frequency (GHz) (assumes times are in ps)
        set path_frequency [expr 1e3/($clk_period - $slack)]

        # Calculate total fanout
        set fanouts [get_db $output_points .pin.fanout]
        set total_fanout [expr [lsum $fanouts]-[llength $fanouts]+1]

        # Calculate total cell delay
        set total_cell_delay [lsum [get_db $output_points .delay]]

        # Calculate total net delay
        set total_net_delay [lsum [get_db $input_points .delay]]

        # Record path data
        dict set path_data id $path_id slack            $slack
        dict set path_data id $path_id slack_adjustment $statistical_adjustment
        dict set path_data id $path_id sigma            $sigma
        dict set path_data id $path_id delay_type       $delay_type
        dict set path_data id $path_id path_group       [lindex $path_groups $i]
        dict set path_data id $path_id scenario         $path_scenario
        dict set path_data id $path_id stages           $stages
        dict set path_data id $path_id total_fanout     $total_fanout
        dict set path_data id $path_id total_cell_delay $total_cell_delay
        dict set path_data id $path_id total_net_delay  $total_net_delay
        dict set path_data id $path_id skew             $skew 
        dict set path_data id $path_id mean_cppr        [lindex $cppr_means $i]
        dict set path_data id $path_id cppr             [lindex $cpprs $i]
        dict set path_data id $path_id check_value_mean [lindex $check_value_means $i]
        dict set path_data id $path_id check_value      [lindex $check_values $i]
        dict set path_data id $path_id frequency        $path_frequency
        dict set path_data id $path_id startpoint       [lindex $startpoints $i]
        dict set path_data id $path_id endpoint         [lindex $endpoints $i]

        # Get pin / ports of the path
        set pins [get_db $points .pin]
		#puts "timing point: $points"
		#puts "pins: $pins"
		#set only_pins [list]
		#foreach pin $pins {
		#	if {![get_property $pin is_pin]} {
		#		set index [lsearch $pins $pin]
		#		set only_pins [lreplace $pins $index $index]
		#	}
		#}

        # Get pin information
        set direction    [get_db $pins .direction]
        set is_clock_pin [get_db $pins .is_clock_network_pin]
        
        # Get cell reference names
        set cells      [get_db $pins .inst]
        set cell_refs  [get_db $cells .base_cell.name]

        # Get hierarchy (cells at the top level will return an empty string as the hierarchy path)
        set hier_paths [get_db $cells .parent]

        # Get delay from one timing point to the next
        set delays [get_db $points .delay]

        # Get transition time for the timing points
        set trans [get_db $points .slew]

        # Get net capacitance for the timing points
        set caps [get_db $points .load]

        # Get the mean and std dev (sensit) for the delay time
        set delay_means    [get_db $points .delay_mean]
        set delay_std_devs [get_db $points .delay_sigma]
        
        # Get the mean and std dev (sensit) for the arrival time
        set arrival_means    [get_db $points .arrival_mean]
        set arrival_std_devs [get_db $points .arrival_sigma]

        # Rise and fall information
        set rise_fall [get_db $points .transition_type]

        # Fanouts
        set fanouts [get_db $pins .fanout]

        # Delta delay
        set delta_delays [get_db $points .delta_delay]

        # Iterate through the points
        for {set j 0} {$j < [llength $points]} {incr j} {
            set cell_ref [lindex $cell_refs $j]

            # Determine hierarchy up to the max level
            set hierarchy [split [lindex $hier_paths $j] $path_delimiter]
            lappend hierarchy "Other"
            set hierarchy [lrange $hierarchy 1 $hierarchical_depth]
            # Fill out data for startpoint
			#puts "pins: $pins"
			#puts "only_pins: $only_pins"
			#puts "is_clock_pin: $is_clock_pin"
			#puts "direction: $direction"
            if {[lindex $direction $j] eq "out" && [lindex $is_clock_pin $j-1]} {
                # Copy in template for a new entry
                if {![dict exists $startpoint_data cell_ref $cell_ref]} {
                    dict set startpoint_data cell_ref $cell_ref $startpoint_table_template
                }
                if {![dict exists $startpoint_data hinst {*}$hierarchy]} {
                    dict set startpoint_data hinst {*}$hierarchy $startpoint_table_template
                }
                # Add to the cell ref entry
                dict_add startpoint_data [list cell_ref $cell_ref cell_count] 1
                dict_add startpoint_data [list cell_ref $cell_ref c2q_delay] [lindex $delays $j]
                dict_add startpoint_data [list cell_ref $cell_ref mean_c2q] [lindex $delay_means $j]
                dict_add startpoint_data [list cell_ref $cell_ref output_net_delay] [lindex $delays $j+1]
                dict_add startpoint_data [list cell_ref $cell_ref fanout] [lindex $fanouts $j]
                # Add to the hinst entry
                dict_add startpoint_data [list hinst {*}$hierarchy cell_count] 1
                dict_add startpoint_data [list hinst {*}$hierarchy c2q_delay] [lindex $delays $j]
                dict_add startpoint_data [list hinst {*}$hierarchy mean_c2q] [lindex $delay_means $j]
                dict_add startpoint_data [list hinst {*}$hierarchy output_net_delay] [lindex $delays $j+1]
                dict_add startpoint_data [list hinst {*}$hierarchy fanout] [lindex $fanouts $j]
                # Add to rise or fall time entry
                if {[lindex $rise_fall $j] eq "rise"} {
                    dict_add startpoint_data [list cell_ref $cell_ref  rise_time] [lindex $trans $j]
                    dict_add startpoint_data [list cell_ref $cell_ref  rise_count] 1
                    dict_add startpoint_data [list hinst {*}$hierarchy rise_time] [lindex $trans $j]
                    dict_add startpoint_data [list hinst {*}$hierarchy rise_count] 1
                } else {
                    dict_add startpoint_data [list cell_ref $cell_ref  fall_time] [lindex $trans $j]
                    dict_add startpoint_data [list cell_ref $cell_ref  fall_count] 1
                    dict_add startpoint_data [list hinst {*}$hierarchy fall_time] [lindex $trans $j]
                    dict_add startpoint_data [list hinst {*}$hierarchy fall_count] 1
                }
                
            # Fill out data for internal cells
            } elseif {[lindex $direction $j] eq "out" && ![lindex $is_clock_pin $j-1]} {
                # Copy in template for a new entry
                if {![dict exists $cell_data cell_ref $cell_ref]} {
                    dict set cell_data cell_ref $cell_ref $internal_cell_table_template
                }
                if {![dict exists $cell_data hinst {*}$hierarchy]} {
                    dict set cell_data hinst {*}$hierarchy $internal_cell_table_template
                }

                # Add to the cell ref entry
                dict_add cell_data [list cell_ref $cell_ref cell_count] 1
                dict_add cell_data [list cell_ref $cell_ref cell_delay] [lindex $delays $j]
                dict_add cell_data [list cell_ref $cell_ref mean_cell_delay] [lindex $delay_means $j]
                dict_add cell_data [list cell_ref $cell_ref output_net_delay] [lindex $delays $j+1]
                dict_add cell_data [list cell_ref $cell_ref fanout] [lindex $fanouts $j]
                
                # Add to the hinst entry
                dict_add cell_data [list hinst {*}$hierarchy cell_count] 1
                dict_add cell_data [list hinst {*}$hierarchy cell_delay] [lindex $delays $j]
                dict_add cell_data [list hinst {*}$hierarchy mean_cell_delay] [lindex $delay_means $j]
                dict_add cell_data [list hinst {*}$hierarchy output_net_delay] [lindex $delays $j+1]
                dict_add cell_data [list hinst {*}$hierarchy fanout] [lindex $fanouts $j]

                # Add to the rise or fall time entry
                if {[lindex $rise_fall $j] eq "rise"} {
                    dict_add cell_data [list cell_ref $cell_ref rise_time] [lindex $trans $j]
                    dict_add cell_data [list cell_ref $cell_ref rise_count] 1
                    dict_add cell_data [list hinst {*}$hierarchy rise_time] [lindex $trans $j]
                    dict_add cell_data [list hinst {*}$hierarchy rise_count] 1
                } else {
                    dict_add cell_data [list cell_ref $cell_ref fall_time] [lindex $trans $j]
                    dict_add cell_data [list cell_ref $cell_ref fall_count] 1
                    dict_add cell_data [list hinst {*}$hierarchy fall_time] [lindex $trans $j]
                    dict_add cell_data [list hinst {*}$hierarchy fall_count] 1
                }
            }
            # Fill out data for incident nets
            if {[lindex $direction $j] eq "out"} {
                # Copy in template for a new entry
                if {![dict exists $net_data cell_ref $cell_ref]} {
                    dict set net_data cell_ref $cell_ref $net_table_template
                }
                if {![dict exists $net_data hinst {*}$hierarchy]} {
                    dict set net_data hinst {*}$hierarchy $net_table_template
                }

                # Report parasitics for the net
                set net [get_db [lindex $pins $j] .net.name]
                redirect -variable parasitic_rpt {report_net_parasitics $net -rc_corner $rc_corner}

                # Failsafe for parasitic info
                set wire_cap 0
                set metal_R 0
                set xcap 0
                set via_R 0

                # Extract parasitic info
                regexp {Total\s+Ground\s+Cap\s+=\s+([\d\.]+)} $parasitic_rpt match wire_cap
                regexp {Total\s+Res\s+=\s+([\d\.]+)} $parasitic_rpt match metal_R
                regexp {Total\s+XCap\s+=\s+([\d\.]+)} $parasitic_rpt match xcap

                # Add to the cell ref entry
                dict_add net_data [list cell_ref $cell_ref cell_count] 1
                dict_add net_data [list cell_ref $cell_ref net_delay] [lindex $delays $j+1]
                dict_add net_data [list cell_ref $cell_ref mean_net_delay] [lindex $delay_means $j+1]
                dict_add net_data [list cell_ref $cell_ref total_cap] [lindex $caps $j]
                dict_add net_data [list cell_ref $cell_ref wire_cap] $wire_cap
                dict_add net_data [list cell_ref $cell_ref xcap] $xcap
                dict_add net_data [list cell_ref $cell_ref delta_delay] [lindex $delta_delays $j+1]
                dict_add net_data [list cell_ref $cell_ref metal_R] $metal_R
                #dict_add net_data [list cell_ref $cell_ref via_R] $via_R
                
                # Add to the hinst entry
                dict_add net_data [list hinst {*}$hierarchy cell_count] 1
                dict_add net_data [list hinst {*}$hierarchy net_delay] [lindex $delays $j+1]
                dict_add net_data [list hinst {*}$hierarchy mean_net_delay] [lindex $delay_means $j+1]
                dict_add net_data [list hinst {*}$hierarchy total_cap] [lindex $caps $j]
                dict_add net_data [list hinst {*}$hierarchy wire_cap] $wire_cap
                dict_add net_data [list hinst {*}$hierarchy xcap] $xcap
                dict_add net_data [list hinst {*}$hierarchy delta_delay] [lindex $delta_delays $j+1]
                dict_add net_data [list hinst {*}$hierarchy metal_R] $metal_R
                #dict_add net_data [list hinst {*}$hierarchy via_R] $via_R
                
                # Get wire length by layer
                set lengths [get_db [lindex $pins $j] .net.wires.length]
                set layers  [get_db [lindex $pins $j] .net.wires.layer.name]
                foreach length $lengths layer $layers {
                    dict_add net_data [list cell_ref $cell_ref  wire_length $layer] $length
                    dict_add net_data [list hinst {*}$hierarchy wire_length $layer] $length
                }

                # Add to rise or fall 
                if {[lindex $rise_fall $j+1] eq "rise"} {
                    dict_add net_data [list cell_ref $cell_ref rise_time] [lindex $trans $j+1]
                    dict_add net_data [list cell_ref $cell_ref rise_count] 1
                    dict_add net_data [list hinst {*}$hierarchy rise_time] [lindex $trans $j+1]
                    dict_add net_data [list hinst {*}$hierarchy rise_count] 1
                } else {
                    dict_add net_data [list cell_ref $cell_ref fall_time] [lindex $trans $j+1]
                    dict_add net_data [list cell_ref $cell_ref fall_count] 1
                    dict_add net_data [list hinst {*}$hierarchy fall_time] [lindex $trans $j+1]
                    dict_add net_data [list hinst {*}$hierarchy fall_count] 1
                }
            }
            # Fill out endpoint data
            if {$j == [llength $points]-1} {
                # Copy in template for a new entry
                if {![dict exists $endpoint_data cell_ref $cell_ref]} {
                    dict set endpoint_data cell_ref $cell_ref $endpoint_table_template
                }
                if {![dict exists $endpoint_data hinst {*}$hierarchy]} {
                    dict set endpoint_data hinst {*}$hierarchy $endpoint_table_template
                }

                # Add to the cell ref entry
                dict_add endpoint_data [list cell_ref $cell_ref cell_count] 1
                dict_add endpoint_data [list cell_ref $cell_ref skew] $skew

                # Add to the hinst entry
                dict_add endpoint_data [list hinst {*}$hierarchy cell_count] 1
                dict_add endpoint_data [list hinst {*}$hierarchy skew] $skew

                if {$delay_type eq "max"} {
                    dict_add endpoint_data [list cell_ref $cell_ref setup_time] $check_value_mean
                    dict_add endpoint_data [list cell_ref $cell_ref setup_count] 1
                    dict_add endpoint_data [list hinst {*}$hierarchy setup_time] $check_value_mean
                    dict_add endpoint_data [list hinst {*}$hierarchy setup_count] 1
                } else {
                    dict_add endpoint_data [list cell_ref $cell_ref hold_time] $check_value_mean
                    dict_add endpoint_data [list cell_ref $cell_ref hold_count] 1
                    dict_add endpoint_data [list hinst {*}$hierarchy hold_time] $check_value_mean
                    dict_add endpoint_data [list hinst {*}$hierarchy hold_count] 1
                }
            }

            set prev_is_clock_pin $is_clock_pin
        }

        # Move to the next path
        incr i
    }

    set data [dict create \
        paths $path_data \
        startpoints $startpoint_data \
        internal_cells $cell_data \
        nets $net_data \
        endpoints $endpoint_data \
    ]
    return $data
}

# Main procedure
proc common {} {
    # Start runtime timer
    set start_time [clock microseconds]

    # Check that the tool is supported
    global tums::vendor
    if {!($vendor eq "innovus" || $vendor eq "fc_shell")} {
        puts "$vendor is not supported!"
        return
    }

    # Print run information
    puts "\nRunning Critical Path Analysis with $vendor ..."
    print_settings

    # Validate the critical path analysis settings
    if {[validate_settings]} {return}

    # Get data
    set data [$vendor]
    puts "Finished gathering critical path analysis data"

    # Process net data
    dict set data nets [process_data_recursive [dict get $data nets]]

    # Alphabetize cell reference names
    dict set data startpoints    cell_ref [lsort -stride 2 [dict get $data startpoints    cell_ref]]
    dict set data internal_cells cell_ref [lsort -stride 2 [dict get $data internal_cells cell_ref]]
    dict set data nets           cell_ref [lsort -stride 2 [dict get $data nets           cell_ref]]
    dict set data endpoints      cell_ref [lsort -stride 2 [dict get $data endpoints      cell_ref]]

    # Recursively summate each level of the hinst tree
    dict set data startpoints    hinst [summate_hinst_tree [dict get $data startpoints    hinst]]
    dict set data internal_cells hinst [summate_hinst_tree [dict get $data internal_cells hinst]]
    dict set data nets           hinst [summate_hinst_tree [dict get $data nets           hinst]]
    dict set data endpoints      hinst [summate_hinst_tree [dict get $data endpoints      hinst]]

    # Summate cell refs by family
    dict set data startpoints    family [summate_cell_family [dict get $data startpoints    cell_ref]]
    dict set data internal_cells family [summate_cell_family [dict get $data internal_cells cell_ref]]
    dict set data nets           family [summate_cell_family [dict get $data nets           cell_ref]]
    dict set data endpoints      family [summate_cell_family [dict get $data endpoints      cell_ref]]

    # Summate cell refs by Vt type
    dict set data startpoints    vt_type [summate_vt_char [dict get $data startpoints    cell_ref]]
    dict set data internal_cells vt_type [summate_vt_char [dict get $data internal_cells cell_ref]]
    dict set data nets           vt_type [summate_vt_char [dict get $data nets           cell_ref]]
    dict set data endpoints      vt_type [summate_vt_char [dict get $data endpoints      cell_ref]]

    # Summate cell refs by drive strength
    dict set data startpoints    drive_strength [summate_drive_strength [dict get $data startpoints    cell_ref]]
    dict set data internal_cells drive_strength [summate_drive_strength [dict get $data internal_cells cell_ref]]
    dict set data nets           drive_strength [summate_drive_strength [dict get $data nets           cell_ref]]
    dict set data endpoints      drive_strength [summate_drive_strength [dict get $data endpoints      cell_ref]]

    # Summate paths by path group
    dict set data paths group [summate_path_group [dict get $data paths id]]

    # Print csv and xlsx files
    print_csv
    print_xlsx

    # End timer and return data
    set end_time [clock microseconds]
    puts "\nCritical path analysis runtime = [format "%.3f" [expr ($end_time-$start_time)/1e6]]s"
    return $data    
}

# Print the data dictionary to csv files
proc print_csv {{dict data}} {
    variable output_dir
    variable path_table_template
    variable numeric_path_keys
    variable internal_cell_table_template
    variable net_table_template
    variable startpoint_table_template
    variable endpoint_table_template
    puts "\nWriting CSV files from $dict dictionary ..."

    # Get data dictionary
    upvar $dict local_dict
    
    # Iterate through the data areas
    dict for {category category_dict} $local_dict {
        dict for {section section_data} $category_dict {
            # Determine filename
            if {![file exists $output_dir/$category]} {
                file mkdir $output_dir/$category
            }

            # Open channel
            set fp [open $output_dir/$category/${section}.csv w]

            # Print column names for the CSV
            switch $category {
                paths {
                    if {$section eq "id"} {
                        set csv_columns [join [dict keys $path_table_template] ,]
                    } else {
                        set csv_columns "path_count,[join $numeric_path_keys ,]"
                    }
                }
                startpoints {set csv_columns [join [dict keys $startpoint_table_template] ,]}
                internal_cells {set csv_columns [join [dict keys $internal_cell_table_template] ,]}
                nets {
                    set csv_columns [concat [dict keys $net_table_template] $tums::metal_layers]
                    set csv_columns [join $csv_columns ,]
                }
                endpoints {set csv_columns [join [dict keys $endpoint_table_template] ,]}
            }
            puts $fp "$section,$csv_columns"

            # Each leaf in the section is a row in the table
            if {$section eq "hinst"} {
                set leafs [get_hinst_tree $section_data]
                foreach leaf $leafs {
                    puts -nonewline $fp [join $leaf /]
                    write_data [dict get $section_data {*}$leaf] $fp
                }
            } else {
                dict for {leaf leaf_data} $section_data {
                    # Avoid writing "nan" as it gets confused with NaN
                    if {$leaf eq "nan"} {set leaf "nan_"}
                    puts -nonewline $fp $leaf
                    write_data $leaf_data $fp
                }
            }
            
            # Finish CSV
            puts $fp "\n"
            close $fp
        }
    }
}

# Combine alike CSV files into one XLSX files
proc print_xlsx {} {
    variable output_dir
    puts "\nCombining CSV files into an XLSX file for each critical.path.analysis run ..."
    
    # Error message for if ADEPT is not enabled
    if {[catch {exec csvs2xlsx --help}]} {
        puts "ERROR: ADEPT not enabled, cannot run csvs2xlsx. In an ADEPT enabled shell, re-run the command: ::tums::power.breakdown::print_xlsx"
        return
    }

    # Run csvs2xlsx on each run directory in the power.breakdown directory
    foreach entry [exec ls $output_dir] {
        if {[file isdirectory $output_dir/$entry]} {
            set fp "$output_dir/$entry"
            set csvs [glob $fp/*.csv]
            exec csvs2xlsx -o ${fp}.xlsx {*}$csvs 
        }
    }
    puts "XLSX file generation complete"
}

# Recursively get the keys of a hinst tree
proc get_hinst_tree {dict {leaf_key cell_count} {path ""}} {
    set key_tree [list]
    dict for {key value} $dict {
        if {[dict exists $value $leaf_key]} {
            lappend key_tree [concat $path $key]
        } else {
            lappend key_tree {*}[get_hinst_tree $value $leaf_key [concat $path $key]]
        }
    }
    return $key_tree
}

# Write a data dictionary to a specified channel
proc write_data {data fp} {
    dict for {key value} $data {
        if {$key eq "wire_length"} {
            foreach length [dict values $value] {
                puts -nonewline $fp ",$length"
            }
        } else {
            puts -nonewline $fp ",$value"
        }
    }
    puts $fp ""
}

# Print current critical path analysis settings
proc print_settings {} {
    variable output_dir
    variable max_slack
    variable num_paths
    variable hierarchical_depth
    variable scenarios
    variable pba_mode
    variable inc_io_paths
    variable inc_mem_paths

    # Print settings
    puts "output_dir         = $output_dir"
    puts "number of paths    = $num_paths"
    puts "max slack          = $max_slack"
    puts "hierarchical depth = $hierarchical_depth"
    puts "pba mode           = $pba_mode"
    
    switch $tums::vendor {
        fc_shell {puts "scenario(s)        = $scenarios"}
        innovus  {puts "analysis view      = $scenarios"}
    }

    puts "include IO paths   = $inc_io_paths"
    puts "include MEM paths  = $inc_mem_paths\n" 
}

# TODO: Validate the critical path analysis settings
proc validate_settings {} {
    # Do not raise a flag if all checks passed
    return 0
}

# Set the output directory for critical path analysis
proc set_output_dir_name {output_dir_name} {
    variable output_dir

    # Join the TUMs ward to the metric output directory name
    set output_dir [file join $::tums::ward $output_dir_name]

    # Make the directory if needed
    if {![file isdirectory $output_dir]} {
        file mkdir $output_dir
    }
}

# Name of output directory under tums::ward
set_output_dir_name "critical.path.analysis"

namespace export -clean common print_settings
}
