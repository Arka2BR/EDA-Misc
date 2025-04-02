proc get_jog_count { } {
     set ALL_Mx_LAYERS [get_db layers -if {.type==routing && .backside==false}]
     puts "Layer Name, Direction, Total Shapes, No of jogs, Jog Ratio (%)"
     foreach i $ALL_Mx_LAYERS { 
           set lyrName [get_db $i .name] ;
           set lyrDir [get_db $i .direction] ;
            set all_nets [get_db nets .wires -if {.layer==$i}] ;
            set net_count [expr double([llength $all_nets])] ;
           if { ($lyrDir == "vertical")} {
                 set  jogs [get_db nets .wires -if {.layer==$i && .direction!=vertical}] ;
           } else {
                 set  jogs [ get_db nets .wires -if {.layer==$i && .direction!=horizontal}] ;
            }
           set jog_count [expr double([llength $jogs])] ;
           set float jog_ratio [expr {$jog_count*100/$net_count]];
           puts "$lyrName, $lyrDir, $net_count, $jog_count, [format %.2f $jog_ratio]"
      }
}
