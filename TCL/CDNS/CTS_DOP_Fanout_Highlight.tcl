set all_hilit_color [get_layer_preference  hilite -color]
set all_hilit_stipple [get_layer_preference  hilite -stipple]
set dop_list [get_db [get_db insts -if {.name=~"*glbdrv*" && .base_cell.base_name=~"GCKDOP*"}] .name]
set dop_pin_list "ckq ckfree"
set dop_color white
set picture_name DOP_Fanout_Highlight

# Containers
set prime_colors {}
set second_colors {}
set prime_stipple {}
set second_stipple {}

# Color & Stipple Shuffling
for {set i 0} {$i < [llength $all_hilit_color] } {incr i} {
	set color [lindex $all_hilit_color $i]
	set stipple [lindex $all_hilit_stipple $i]
	if {[expr {$i % 2}]==0} {
		lappend prime_colors $color
		lappend prime_stipple $stipple
	} else {
		lappend second_colors $color
		lappend second_stipple $stipple
	}

}

# Clear all Highlights
gui_clear_highlight -all
# Clear all Fly-Lines
set_layer_preference flightLine -is_visible 0
# Clear Metal Layers
set_layer_preference node_layer -is_visible 0
# Clear Rulers
clear_all_rulers

# Apply all DOP Highlight
foreach dop $dop_list {
	set dop_index [lsearch $dop_list $dop]
	foreach pin $dop_pin_list {
		set pin_index [lsearch $dop_pin_list $pin]
		if {$pin_index==0} {
			set color [lindex $prime_colors $dop_index]
			set stipple [lindex $prime_stipple $dop_index]
		} else {
			set color [lindex $second_colors $dop_index]
			set stipple [lindex $second_stipple $dop_index]
		}

		gui_highlight [all_fanout -from  $dop/$pin -only_cells ] -color $color -pattern $stipple
	}

}

# Separate highlight for DOP instances
gui_highlight [get_db insts $dop_list] -color $dop_color


# Save Picture
gui_write_picture $picture_name.png -format png
puts "Generated Picture: [pwd]/$picture_name.png !!"
