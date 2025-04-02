proc get_jog_count { } {
     set ALL_Mx_LAYERS [get_db layers -if {.type==routing && .backside==false}]
     puts "Layer Name, Total Shapes, No of jogs, Jog Ratio"
     foreach i $ALL_Mx_LAYERS { 
           set lyrName [get_db $i .name] ;
           set lyrDir [get_db $i .direction] ;
            set all_nets [get_db nets .wires -if {.layer==$i}] ;
           if { ($lyrDir == "vertical")} {
                 set  jogs [get_db nets .wires -if {.layer==$i && .direction!=vertical}] ;
                 set jog_ratio expr{[llength $jogs]/[llength $all_nets]};
           } else {
                 set  jogs [ get_db nets .wires -if {.layer==$i && .direction!=horizontal}] ;
                 set jog_ratio expr{[llength $jogs]/[llength $all_nets]};
            }
           puts "$lyrName, [llength $all_nets], [llength $jogs], $jog_ratio"
      }
}
