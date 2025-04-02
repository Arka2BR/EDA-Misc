proc get_jog_count { } {
     set ALL_Mx_LAYERS [get_layers -filter "layer_type == interconnect && mask_name =~ metal*"]
     puts "Layer Name, No of jogs"
foreach_in_collection  i $ALL_Mx_LAYERS { 
      set lyrName [get_attribute $i name] ;
      set lyrDir [get_attribute $i routing_direction] 
      if { $lyrDir eq "vertical" } {
       set  jogs [ get_shapes -quiet -filter "layer.name == $lyrName && is_vertical != true"] 
      } else {
       set  jogs [ get_shapes -quiet -filter "layer.name == $lyrName && is_horizontal != true"] 
       }
      puts "[get_attribute $i name], [sizeof_collection $jogs]"                      }

}
