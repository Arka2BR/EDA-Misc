set max_fanout 24
set hfo_pin_path [get_db pins -if {.fanout >=$max_fanout}]

foreach pin_path $hfo_pin_path {
	set hfo_inst [get_db $pin_path .inst]
	set hfo_pin_name [get_db $pin_path .base_pin.base_name]
	set hfo_cell [get_db $hfo_inst .base_cell.base_name]
	set fanout [get_db $pin_path .fanout]

	puts "Instance: $hfo_inst Pin: $hfo_pin_name Cell: $hfo_cell Fanout: $fanout"

}
