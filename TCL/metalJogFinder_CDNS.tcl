proc get_jog_count { } {
     set ALL_Mx_LAYERS [get_db layers -if {.type==routing && .backside==false}]
     puts "Layer Name, No of jogs"
     foreach i $ALL_Mx_LAYERS { 
           set lyrName [get_db $i .name] ;
           set lyrDir [get_db $i .direction]
           if { ($lyrDir == "vertical")} {
                 set  jogs [get_db nets .wires -if {.layer==$i && .direction!=vertical}]
                 puts $jogs
           } else {
                 set  jogs [ get_db nets .wires -if {.layer==$i && .direction!=horizontal}]
                 puts $jogs
            }
           puts "[get_db $i name], [sizeof_collection $jogs]"
      }
}
