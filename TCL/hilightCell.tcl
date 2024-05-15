
#*************************************************************************#
# DISCLAIMER: The code is provided for Cadence customers                  #
# to use at their own risk. The code may require modification to          #
# satisfy the requirements of any user. The code and any modifications    #
# to the code may not be compatible with current or future versions of    #
# Cadence products. THE CODE IS PROVIDED \"AS IS\" AND WITH NO WARRANTIES,# 
# INCLUDING WITHOUT LIMITATION ANY EXPRESS WARRANTIES OR IMPLIED          #
# WARRANTIES OF MERCHANTABILITY OR FITNESS FOR A PARTICULAR USE.          #
#*************************************************************************#

proc hiliteCellTypeInBox {{cellType default} {cellFindFile default}} {
    ##developed to be able to find latches in an area selected by mouse
    ## default cell type *lat*
    ## default file name cell_highlite.txt
    ## usage hiliteCellTypeInBox   <cellType>  <file name>
    ##     cell type default :: *lat*
    ##     file name default :: cell_highlite.txt

    puts ""
    puts "Click two points,  DO NOT DRAG MOUSE"
    puts ""
    puts "########################################"

    puts "cellType $cellType"
    puts "cellFindFile $cellFindFile"
    
    puts "hello"
    if { $cellType == "default" } {
        set cellTypeName "*lat*"
    } elseif { ($cellType == "-h" || $cellType == "-help") } {
        puts "\nUSAGE ::"
        puts "hiliteCellTypeInArea \<Cell Type \(wildscards valid\)\> \<File Name\>"
        puts "default celltype \"*lat*\",  default file name \"cell_highlite.txt\""
       puts "\n"
        puts "########################################"
        return
    } else {
        set cellTypeName "$cellType"
    }

    if { $cellFindFile == "default" } {
        set cellFindFile "cell_highlite.txt"
    }
    set file1 [open ${cellFindFile} w]
    puts $file1 "\# cell in area box"
    
    dehighlight
    set mouseArea [uiGetBox]
    set mArea_x1 [lindex [split $mouseArea " "] 0 ]
    set mArea_y1 [lindex [split $mouseArea " "] 1 ]
    set mArea_x2 [lindex [split $mouseArea " "] 2 ]
    set mArea_y2 [lindex [split $mouseArea " "] 3 ]
    puts $file1 "\#    $mouseArea"
    puts "Area Box::  $mouseArea"
   
    ##find cells in area
    set instNames [dbGet [dbGet [dbQuery -area $mouseArea].cell.name $cellTypeName -p2].name]
 
    set cnt 0
    if {$instNames != "0x0" } {
        foreach i $instNames {
            selectInst $i
            set objIns    [dbGet [dbGet -p top.insts.name $i]]
            dbHiliteObj $objIns 1
            #puts $i
            puts $file1 "$i"
            set cnt [expr $cnt + 1]
        }
    }
    deselectAll
    
    #zoomBox $mArea_x1 $mArea_y1 $mArea_x2 $mArea_y2
    #zoomOut
    
    if {$cnt > 0 } {
        puts "\nFound $cnt cells of type :: $cellTypeName."
        puts "cell instance names saved in file"
        puts "    $cellFindFile"
    } else {
        puts "\nDid not find any cells of type $cellTypeName."
        puts "Change name or wildcards to help search."
    }
    puts "########################################"
    puts "\n"
    close $file1
 
}

