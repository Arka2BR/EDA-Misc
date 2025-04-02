proc get_jog_count { } {
     set outfile [open "metal_jog_report.csv" w+]  
     set ALL_Mx_LAYERS [get_db layers -if {.type==routing && .backside==false}]
     puts $outfile "Layer Name, Direction, Total Shapes, No of jogs, Jog Ratio (%)"
     foreach i $ALL_Mx_LAYERS { 
           set lyrName [get_db $i .name] ;
           set lyrDir [get_db $i .direction] ;
            set all_nets [get_db nets .wires -if {.layer==$i}] ;
            set net_count [llength $all_nets] ;
           if { ($lyrDir == "vertical")} {
                 set  jogs [get_db nets .wires -if {.layer==$i && .direction!=vertical}] ;
           } else {
                 set  jogs [get_db nets .wires -if {.layer==$i && .direction!=horizontal}] ;
            }
           set jog_count [llength $jogs] ;
           set jog_ratio [expr $jog_count*100.0/$net_count];
           puts $outfile "$lyrName, $lyrDir, $net_count, $jog_count, [format %0.2f $jog_ratio]"
      }
      close $outfile
}
