set user_dir scripts/ppa_steps
set tech_dir scripts/asicflows/cadence/tech.dot31.g1m.tp6
set proc_dir $tech_dir/procs

# Initial Setup
# ----------------------------------------------------------------------------------------------------------------------
source $user_dir/init_innovus_user.tcl
source $tech_dir/tech_config.tcl
source $tech_dir/set_pg_grid_config.tcl
source $tech_dir/init_innovus_i7.tcl
source $tech_dir/default_settings.tcl
source $tech_dir/cts_ndr_rules.tcl

set procs [glob $proc_dir/*]

foreach scr $procs {
	source $scr
}

# Previous PG cleanup
# ----------------------------------------------------------------------------------------------------------------------
delete_routes -type special -shapes stripe

# Execution
# ----------------------------------------------------------------------------------------------------------------------

set is_power_plan_done 0
set stripe_status [get_db pg_nets .special_wires.status -unique]
if { $stripe_status eq "routed" } {
#        set is_power_plan_done 1
        P_msg_info "Power Plan is available in DEF. skipping create_pg_grid step"
} else {
        set is_power_plan_done 0
}

if { $is_power_plan_done == 0 } {


  set_db generate_special_via_enable_check_drc true
  set_db generate_special_via_opt_cross_via 1
  #set_db add_stripes_remove_floating_stripe_over_block 1
  set_db add_stripes_remove_floating_stripe_over_block 0
  set_db add_stripes_skip_via_on_pin {}
  set_db generate_special_via_preferred_vias_only use_lef
  set_db add_stripes_use_fgc 1
  eval_legacy {setViaGenMode -use_cce 0 }


  if {[info exists vars(INTEL_POWER_FORMAT)] && [regexp "cpf|upf" $vars(INTEL_POWER_FORMAT)]} {
    set_db generate_special_via_create_max_row_cut_via 1
    set_db generate_special_via_allow_wire_shape_change false
     eval_legacy {set pwStripeStapling    1 }
  } else {
    eval_legacy {set pwStripeStapling 3 }
  }
  
  if { [file exists ./scripts] == 0 } {
    mkdir ./scripts
  }
  set OUTPUT_PG_GRID_FILE ./scripts/pg_grid.tcl
  
  P_create_pg_grid -out_command_file $OUTPUT_PG_GRID_FILE -pg_grid_config $vars(INTEL_PG_GRID_CONFIG) -max_pg_layer $vars(INTEL_MAX_PG_LAYER) -power_format $vars(INTEL_POWER_FORMAT) -gnd_net $vars(INTEL_GROUND_NET) -power_net $vars(INTEL_POWER_NET) -tile_config $vars(INTEL_TILE_CONFIG) -lp_power_dict $vars(lp_power_dict)
  
  source $OUTPUT_PG_GRID_FILE
  
  set_db generate_special_via_preferred_vias_only keep

  # Color PG mesh
  # ----------------------------------------------------------------------------------------------------------------------
  #add_power_mesh_colors -reverse_with_non_default_width 1
  add_power_mesh_colors
  
  # Get all cuts that have masks greater than/equal to 2 and color them appropriately.
  # ----------------------------------------------------------------------------------------------------------------------
  foreach cut [get_db [get_db [get_db layers -if .type==cut] -if .num_masks>=2] .name] {
    switch -- $cut {
      v1 { 
        set_db [get_db [get_db [get_db pg_nets -if .is_power  ] .special_vias] -if .via_def.cut_layer.name==v1 ] .cut_mask 2
        set_db [get_db [get_db [get_db pg_nets -if .is_ground  ] .special_vias] -if .via_def.cut_layer.name==v1 ] .cut_mask 1
      }
      v2 { set_db [get_db [get_db [get_db pg_nets -if .is_ground ] .special_vias] -if .via_def.cut_layer.name==v2 ] .cut_mask 2}
      v3 { set_db [get_db [get_db [get_db pg_nets -if .is_ground ] .special_vias] -if .via_def.cut_layer.name==v3 ] .cut_mask 2}
    }
  }
  
 
}

