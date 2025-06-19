#############################################
# Developer : Arkaparabho Adhikary
# Date      : 19/06/2025
# EDA Tool  : Cadence Innovus
#############################################
#
#############################################
# OLD CLOCK TREE REMOVAL
#############################################
# Deleting original clock tree created by tool
delete_clock_trees <Main Clock Name>
delete_clock_trees <Global Driver for Main clock>
#delete_clock_trees mclk_fmav0<2>
#
#############################################
# OLD SKEW GROUP REMOVAL
#############################################
# Deleting mclk_fmav0 skew group
#delete_skew_groups mclk_fmav0/func_setup
#delete_skew_groups mclk_fmav0/func_LV
#delete_skew_groups mclk_fmav0/func_hold
#
#############################################
# CLOCK TREE DEFINITION
#############################################
set main_clock_name mclk_fmav0
#
# Creating clock tree definition on all DOP
foreach dop [get_db insts *<Global_Driver Instance name>*] {
    #regexp Par_Mclk_OOO_INT.* $dop dop_name
	set dop_name [get_db $dop .base_name]
	# Edit by Arka
	# Added ckfree pin consideration
    set dop_outpin_ck [get_object_name [get_pins -of $dop -filter "direction == out && name == <Clock Out Pin 1>"]]
	set dop_outpin_ckfree [get_object_name [get_pins -of $dop -filter "direction == out && name == <Clock Out Pin 2>"]]

	# ckq clocktree
    puts "USER: creating clock_tree definition on user_clock_tree_dop_${dop_name}_ckq"
    create_clock_tree -name user_clock_tree_dop_${dop_name}_ckq -source $dop_outpin_ck

    set_db [get_db clock_trees user_clock_tree_dop_${dop_name}_ckq] .cts_target_max_transition_time [get_db cts_target_max_transition_time_leaf]
    set_db [get_db clock_trees user_clock_tree_dop_${dop_name}_ckq] .cts_target_max_transition_time_leaf [get_db cts_target_max_transition_time_leaf]
    set_db [get_db clock_trees user_clock_tree_dop_${dop_name}_ckq] .cts_target_max_transition_time_sdc [get_db cts_target_max_transition_time_leaf]
    set_db [get_db clock_trees user_clock_tree_dop_${dop_name}_ckq] .cts_target_max_transition_time_top [get_db cts_target_max_transition_time_top]
    set_db [get_db clock_trees user_clock_tree_dop_${dop_name}_ckq] .cts_target_max_transition_time_trunk [get_db cts_target_max_transition_time_trunk]
    set_db [get_db clock_trees user_clock_tree_dop_${dop_name}_ckq] .cts_source_latency -index delay_corner:<Delay Corner 1> -90.0 ;# Coming from Clock Spec File
	set_db [get_db clock_trees user_clock_tree_dop_${dop_name}_ckq] .cts_source_latency -index delay_corner:<Delay Corner 2> -90.0 ;# Coming from Clock Spec File
	set_db [get_db clock_trees user_clock_tree_dop_${dop_name}_ckq] .cts_source_latency -index delay_corner:<Delay Corner 3>-150.0 ;# Coming from Clock Spec File

	# ckfree clock tree
	puts "USER: creating clock_tree definition on user_clock_tree_dop_${dop_name}_ckfree"
    create_clock_tree -name user_clock_tree_dop_${dop_name}_ckfree -source $dop_outpin_ckfree

    set_db [get_db clock_trees user_clock_tree_dop_${dop_name}_ckfree] .cts_target_max_transition_time [get_db cts_target_max_transition_time_leaf]
    set_db [get_db clock_trees user_clock_tree_dop_${dop_name}_ckfree] .cts_target_max_transition_time_leaf [get_db cts_target_max_transition_time_leaf]
    set_db [get_db clock_trees user_clock_tree_dop_${dop_name}_ckfree] .cts_target_max_transition_time_sdc [get_db cts_target_max_transition_time_leaf]
    set_db [get_db clock_trees user_clock_tree_dop_${dop_name}_ckfree] .cts_target_max_transition_time_top [get_db cts_target_max_transition_time_top]
    set_db [get_db clock_trees user_clock_tree_dop_${dop_name}_ckfree] .cts_target_max_transition_time_trunk [get_db cts_target_max_transition_time_trunk]
    set_db [get_db clock_trees user_clock_tree_dop_${dop_name}_ckfree] .cts_source_latency -index delay_corner:<Delay Corner 1> -90 ;# Coming from Clock Spec File
	set_db [get_db clock_trees user_clock_tree_dop_${dop_name}_ckfree] .cts_source_latency -index delay_corner:<Delay Corner 2> -90 ;# Coming from Clock Spec File
	set_db [get_db clock_trees user_clock_tree_dop_${dop_name}_ckfree] .cts_source_latency -index delay_corner:<Delay Corner 3> -150.0 ;# Coming from Clock Spec File
	
}

#############################################
# CLOCK TREE SOURCE GROUP
#############################################
# Compiling all the clock trees 
set all_clock_trees_ckq [get_db [get_db clock_trees *user_clock_tree_dop_*ckq] .name]
set all_clock_trees_ckfree [get_db [get_db clock_trees *user_clock_tree_dop_*ckfree] .name] 
#
puts "Creating clock tree source group: user_clocktree_sourcegroup"
create_clock_tree_source_group -name user_clocktree_sourcegroup_ckq -clock_trees $all_clock_trees_ckq
create_clock_tree_source_group -name user_clocktree_sourcegroup_ckfree -clock_trees $all_clock_trees_ckfree

#
#############################################
# OPCOND TO VIEW/DELAY MAPPING
#############################################
# Finding the 1.1v analysis and delay views
set opcond_high_search_term <Opcond 1>
set view_name_high [get_db [get_db analysis_views -if {.delay_corner.default_early_timing_condition.opcond.name=~$opcond_high_search_term* && .is_setup==true}] .name]
set view_constraint_high [get_db [get_db analysis_views $view_name_high] .constraint_mode.name]
set view_delay_corner_high [get_db [get_db delay_corners -if {.default_early_timing_condition.opcond.name=~$opcond_high_search_term* && .is_setup==true}] .name]
#
# Finding the 0.65v analysis and delay views
set opcond_nom_search_term <Opcond 2>
set view_name_nom [get_db [get_db analysis_views -if {.delay_corner.default_early_timing_condition.opcond.name=~$opcond_nom_search_term* && .is_setup==true}] .name]
set view_constraint_nom [get_db [get_db analysis_views $view_name_nom] .constraint_mode.name]
set view_delay_corner_nom [get_db [get_db delay_corners -if {.default_early_timing_condition.opcond.name=~$opcond_nom_search_term* && .is_setup==true}] .name]
#
#############################################
# SKEW GROUP MAPPING
#############################################
# Primary func_setup
set_db [get_db skew_groups *user*] .cts_skew_group_created_from_constraint_modes $view_constraint_high
set_db [get_db skew_groups *user*] .cts_skew_group_created_from_delay_corners $view_delay_corner_high
set_db [get_db skew_groups *user*] .cts_skew_group_created_from_clock $main_clock_name
set_db [get_db skew_groups *user*] .cts_skew_group_include_source_latency true
set_db [get_db skew_groups *user*] .cts_target_skew auto
set_db [get_db skew_groups *user*] .cts_skew_group_target_insertion_delay 0; # From Clock Spec

#
# Balance Skew Group
create_skew_group -balance_skew_groups [get_db skew_groups *user_clock_tree_dop_*ckq] -name balance_user_skew_groups_ckq
create_skew_group -balance_skew_groups [get_db skew_groups *user_clock_tree_dop_*ckfree] -name balance_user_skew_groups_ckfree

##### !!!!! You May need to change this depending on your clock quality !!!! #####
set_db skew_group:balance_user_skew_groups_ckq .cts_target_skew auto
set_db skew_group:balance_user_skew_groups_ckq .cts_skew_group_target_insertion_delay 0
set_db skew_group:balance_user_skew_groups_ckfree .cts_target_skew auto
set_db skew_group:balance_user_skew_groups_ckfree .cts_skew_group_target_insertion_delay 0
##### !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! ####

#############################################
# ID COnstraints
#############################################

set_db ccopt_auto_limit_insertion_delay_factor 1.2

#############################################
# DONT TOUCH SETTINGS
#############################################

## --------------------------------------------------------------------------
## Prevent issues with DOP assignment due to dont_touch issues
## --------------------------------------------------------------------------
#iproc_msg -info "dcahyadi - Prevent issues with DOP assignment due to dont_touch issues"
set_db [get_db [get_pins -hier -filter is_hierarchical==true] -if {.dont_touch==true}] .dont_touch none
set dont_touch_insts [ get_db insts -if {.is_integrated_clock_gating && .dont_touch != none} ]
set_db [get_cells $dont_touch_insts] .dont_touch none 

## --------------------------------------------------------------------------
## Remove dont touch from clock trees
## --------------------------------------------------------------------------
#iproc_msg -info "dcahyadi - Remove dont touch from clock trees"

set_db [get_db clock_trees .nets.hnets.hinst.module.design] .dont_touch false
set_db [get_db clock_trees .nets.hnets.hinst]               .dont_touch false
set_db [get_db clock_trees .nets.hnets]                     .dont_touch false
set_db [get_db clock_trees .insts]                          .dont_touch false
set_db [get_db clock_trees .nets.hnets.hinst.module]        .dont_touch false
set_db [get_db clock_trees .nets]                           .dont_touch false
set_db [get_db clock_trees .insts.pins]                     .dont_touch false
set_db [get_db clock_trees .nets.hnets.hinst]               .dont_touch_hports false
set_db [get_db clock_trees .nets.hnets.hinst.module]        .dont_touch_hports false

set_db opt_view_pruning_hold_views_active_list              $view_name_high
set_db opt_view_pruning_placement_setup_view_list           $view_name_high  
set_db opt_view_pruning_tdgr_setup_views_persistent_list    $view_name_high

#############################################
# CTS NET IDEALITY FIX
#############################################
set_db [get_db pins *glbdrv*/glbdrv_*/ckq] .net.cts_ideal_net false
set_db [get_db pins *glbdrv*/glbdrv_*/ckfree] .net.cts_ideal_net false

set_interactive_constraint_modes [get_db constraint_modes ]
reset_ideal_network [get_db [get_db pins *glbdrv*/glbdrv*/ckq] .net]
reset_ideal_network [get_db [get_db pins *glbdrv*/glbdrv*/ckfree] .net]
set_interactive_constraint_modes {}

#############################################
# CHECKS
#############################################

puts "ECF: [get_db design_early_clock_flow]"
puts "Clock Source group: [get_db clock_tree_source_groups]"
puts "Clock Source group count: [llength [get_db clock_tree_source_groups .clock_trees]]"
