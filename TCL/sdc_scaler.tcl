proc isnumber {value} {
    # return 1 if 'value' is a number
    if {![catch {expr {abs($value)}}]} {
        return 1
    }
    return 0
}

proc setNewVal {inList i base_frequency new_freq} {
    set newVal [expr [lindex $inList $i] * $base_frequency / $new_freq]
    set newVal [format "%.2f" $newVal]
    return $newVal
}

proc translate_freq {base_frequency new_freq data outFile} {
    # delete old output files
    if {[file exists $outFile] == 1} {
        file delete $outFile
    }
    # write header to new output files
    set new_sdc [open $outFile w]
    puts $new_sdc "# This is the sdc file created by mmmc_translate_sdc.tcl"
    # set systemTime [clock seconds]
    # puts $new_sdc "# [clock format $systemTime -format %H:%M:%S] on [clock format $systemTime -format %D]"
    # begin process
    foreach line $data {
        set lineList [regexp -all -inline {\S+} $line]
        # case1: create_clock
        if {[expr {[lindex $lineList 0] eq "create_clock"}] == 1} {
            for {set i 0} {$i < [expr {[llength $lineList]}]} {incr i} {
                if {$i > 0 && [expr {[lindex $lineList [expr {$i - 1}]] eq "-period"}] == 1} {
                    lset lineList $i [setNewVal $lineList $i $base_frequency $new_freq]
                }
                if {$i > 0 && [expr {[lindex $lineList [expr {$i - 1}]] eq "-waveform"}] == 1} {
                    set newList [split [lindex $lineList $i] "\{"]
                    lset lineList $i "\{[setNewVal $newList 1 $base_frequency $new_freq]"
                }
                if {$i > 1 && [expr {[lindex $lineList [expr {$i - 2}]] eq "-waveform"}] == 1} {
                    set newList [split [lindex $lineList $i] "\}"]
                    lset lineList $i "[setNewVal $newList 0 $base_frequency $new_freq]\}"
                }
            }
            for {set i 0} {$i < [expr {[llength $lineList]}]} {incr i} {
                if {$i < [expr {[llength $lineList] - 1}]} {
                    puts -nonewline $new_sdc [lindex $lineList $i]
                    puts -nonewline $new_sdc " "
                } else {
                    puts $new_sdc [lindex $lineList $i]
                }
            }
        } elseif {[expr {[lindex $lineList 0] eq "set_clock_transition"}] == 1 || [expr {[lindex $lineList 0] eq "set_max_transition"}] == 1 || [expr {[lindex $lineList 0] eq "set_driving_cell"}] == 1 || [expr {[lindex $lineList 0] eq "set_clock_uncertainty"}] == 1 || [expr {[lindex $lineList 0] eq "set_input_delay"}] == 1 || [expr {[lindex $lineList 0] eq "set_output_delay"}] == 1} {
        # case2: set_clock_transition || set_max_transition || set_driving_cell || set_clock_uncertainty || set_input_delay || set_output_delay
            for {set i 0} {$i < [expr {[llength $lineList]}]} {incr i} {
                if {[expr [isnumber [lindex $lineList $i]]] == 1} {
                    lset lineList $i [setNewVal $lineList $i $base_frequency $new_freq]
                }
                if {$i < [expr {[llength $lineList] - 1}]} {
                    puts -nonewline $new_sdc [lindex $lineList $i]
                    puts -nonewline $new_sdc " "
                } else {
                    puts $new_sdc [lindex $lineList $i]
                }
            }
        } else {
            puts $new_sdc $line
        }
    }
    # close output files
    close $new_sdc
    puts "$outFile Translation DONE!"
}

# check input
if {$argc == 1 && [expr {[lindex $argv 0] eq "-help"}] == 1} {
    puts "########################################"
    puts "# Help Information for SDC Translation #"
    puts "########################################"
    puts "Usage:\n\tmmmc_translate_sdc.tcl -degisn \$design_name"
    puts "Vars to define:\n\tPlese define your frequencies under Section # define frequencies\n\tFor example:\n\tset base_frequency 1.8\n\tset ss_freq 1.2\n\tset new_frequency 2.3"
    puts "*Notice*:\n\tMake sure your current working directory is in “genus” dir so that the script can look into the outputs/ folder for the input sdc.gz"
    exit 0
}

if {$argc != 2 || [expr {[lindex $argv 0] eq "-design"}] != 1} {
    puts stderr "ERROR: Invalid input arguments!\n\tUsage: mmmc_translate_sdc.tcl -design \$design_name"
    exit 1
}

# Edited by Arka
set inFile     "/nfs/site/disks/x5e2d_tmp_disk001/users/aadhika1/lnr_testing/sdc_scaling/par_fmav0_func.max_0p650_100.ttttctyptttt_100.tttt.sdc"
set outFile_ff "/nfs/site/disks/x5e2d_tmp_disk001/users/aadhika1/lnr_testing/sdc_scaling/par_fmav0_func.max_0p650_100.ttttctyptttt_100.tttt.scaled.sdc"

# define frequencies
#
set base_frequency 3.3112
set new_frequency 3.3898

puts "##################################"
puts "# Begin SDC Translation For MMMC #"
puts "##################################"
puts "Design Name: [lindex $argv 1]\n\tBase_Freq = $base_frequency\n\tNew_Freq = $new_frequency"
# throws exception when original .sdc.gz file does not exist
if {[file exists $inFile] == 0} {
    puts stderr "ERROR: Could NOT find $inFile"
    exit 1
}
#
puts "Reading $inFile from\n"
# read original .sdc
set fp [open $inFile r]
set file_data [read $fp]
close $fp
set data [split $file_data "\n"]
puts "Translating ..."
translate_freq $base_frequency $new_frequency $data "$outFile_ff"
