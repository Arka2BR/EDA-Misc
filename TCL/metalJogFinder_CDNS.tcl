proc get_jog_count { } {
     #set ALL_Mx_LAYERS [get_layers -filter "layer_type == interconnect && mask_name =~ metal*"]
     set ALL_Mx_LAYERS [get_db layers -if {.type==routing && .backside==false}]
     puts "Layer Name, No of jogs"
foreach_in_collection  i $ALL_Mx_LAYERS { 
      set lyrName [get_db $i .name] ;
      set lyrDir [get_db $i .direction]
      if { ($lyrDir eq "vertical") && () } {
            set  jogs [get_db nets .wires -if {.layer==$i && .direction!=vertical}] 
      } else {
            set  jogs [ get_db nets .wires -if {.layer==$i && .direction!=horizontal}] 
       }
      puts "[get_attribute $i name], [sizeof_collection $jogs]"                      }

}
