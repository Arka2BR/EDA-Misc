# Settings
set SEARCH_IDX 9
set CHAR_SEARCH	"p"
set CHAR_REPLACE "q"
set INST_FILTER 0
set BLOCK_NAME "falcon_core"
#Find all insts

# Re-map
if {$INST_FILTER == 1} {
	set inst_lst [get_db insts]
	foreach inst $inst_lst {
		set inst_base_cell_name [get_db $inst .base_cell.name]

		#puts $inst_base_cell_name
		#puts [string index $inst_base_cell_name 9]
		if {[string index $inst_base_cell_name $SEARCH_IDX]==$CHAR_SEARCH} {
			#puts $inst_base_cell_name
			puts $inst	>> sup2_instances.rpt
			#set updated_name [string replace $inst_base_cell_name $SEARCH_IDX $SEARCH_IDX $CHAR_REPLACE]
			#puts $updated_name
			#set_db $inst .base_cell.name $updated_name
		}

	}
} else {
	set filter_file [open sup2_instances.rpt]
	set lines [split [read $filter_file] "\n"]
	set block_offset [string length $BLOCK_NAME]
	set inst_start [expr {6 + $block_offset}]
	set count 0
	#puts $inst_start
	close $filter_file
	

	foreach line $lines {
		if {[regexp ^inst.* $line]} {
			set count [expr {$count + 1}] 
			set inst_base_cell_name [get_db $line .base_cell.name]
			set updated_name [string replace $inst_base_cell_name $SEARCH_IDX $SEARCH_IDX $CHAR_REPLACE]
			set inst_name [string range $line $inst_start 9999999]
			puts "$count eco_update_cell -inst $inst_name -cell $updated_name"
			#puts $updated_name
			eco_update_cell -inst $inst_name -cell $updated_name
		}
	}
}
