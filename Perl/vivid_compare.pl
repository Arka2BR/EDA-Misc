#!/usr/bin/perl
#===============================================================================
#
#         FILE: vivid_compare.pl
#
#        USAGE: ./vivid_compare.pl <dir or metric>
#
#  DESCRIPTION: Compare multiple Vivid metrics files
#
#       AUTHOR: Kevin Croysdale <croysdal@cadence.com>
#                Based on vivid_compare Michael Hartman
# ORGANIZATION: Cadence Design Systems
#      VERSION: 0.8
#      CREATED: 2020-06-04 
#===============================================================================

use strict;
use warnings;


my ($help, $debug, $test, $open, $strip_name, $mail, $keep_script) ;
my $output   = "/tmp/qor_metrics_$ENV{USER}.html";
my $user_script   = "/tmp/vivid_compare_$ENV{USER}.tcl";
my $vivid_config;
my $generate_path_groups;
my $flowtool;
my $red        = "[31m";
my $end_color  = "[0m";
my $firefox_opt = "--new-window";
my $new_tab;
my $all_version;
my $opt_strip_run_dir=0;

$ENV{PATH}  = "$ENV{PATH}:/grid/common/pkgs/python/v3.7.2/bin";

$open = 1;
my $no_open = 0;
use Getopt::Long;
&GetOptions(
    "strip_name:s"         => \$strip_name,
    "output:s"             => \$output,
    "user_script:s"        => \$user_script,
    "open"                 => \$open,
    "new_tab"              => \$new_tab,
    "new-tab"              => \$new_tab,
    "no_open"              => \$no_open,
    "test"                 => \$test,
    "keep_script"          => \$keep_script,
    "all_version"          => \$all_version,
    "generate_path_groups" => \$generate_path_groups,
    "flowtool"             => \$flowtool,
    "mail"                 => \$mail,
    "help"                 => \$help,
    "config:s"             => \$vivid_config,
    "debug"                => \$debug
) || exit -1;


$keep_script = 1 if $test;

my @files = @ARGV;

if (@files == 0) { 
    print "No files or directories given. Exiting.\n\n";
    $help = 1;
}

if ($open && ! $no_open && -r $output) {
    if ($ENV{DISPLAY} eq "") {
        print "${red}ERROR: DISPLAY not set.${end_color}\n";
        exit -1;
    }
}

if ($help) {
#===  FUNCTION  ================================================================
#         NAME: print_help
#      PURPOSE: Print help for -help
#===============================================================================
    print "Usage: $0 [OPTION] <list of directories or flow.metrics>

Generate combined Vivid Metrics HTML from multiple runs

    --help                Print help message
    --test                Create user.script but do not run flowtool
    --no_open             Do not open HTML in new Firefox tab
    --mail                Mail HTML to myself
    --output=STRING       Used a specific Vivid HTML file
    --config=STRING       Use a vivid config file (write_vivid_config -format vivid)
    --strip_name=STRING   Strip string from all run names
    --output=STRING       Output file to generate. Default: $output
    --keep_script         Keep script file 


 Example usage:
    vivid_compare.pl flow_run1 flow_run2 flow_run3/run_dir.new/flow.metrics
    vivid_compare.pl slow_run fast_run --config /home/croysdal/bin/tools_vivid/vivid_config_small.txt
    ";
    exit 0;
}

if ($output !~ /html$/) {
    $output .= ".html";
}

open  my $user_script_fh, '>', $user_script
    or die  "$0 : failed to open  output file '$user_script' : $!\n";


print STDOUT "Writing $user_script\n";
# Example script:
# read_metric -id run1  a53_run1/run_dir/flow.metrics
# read_metric -id run2  a53_run1_newdef_flat/run_dir/flow.metrics
# report_metric -format vivid  -id "run1 run2" -file my_report.html

my $success = 0;
my $run_num = 0;
my @runs = ();

if (defined $generate_path_groups) {
    my $new_config = "/tmp/path_groups_vivid_config.txt";

    ##  Generate new config using @path_groups
    $vivid_config = $new_config;
}

if ($vivid_config and -r $vivid_config) { 
    print STDERR "Using config: vivid $vivid_config\n";

    ## Disable NFS locking
    print $user_script_fh "source ~croysdal/bin/tools_flowtool/nfs_lock.tcl\n";
    print $user_script_fh "read_metric_config -format vivid $vivid_config\n";
}

my @path_groups;
foreach my $file (@files) {

    ## Get a list of all path groups
       #  View : ALL                  *  -78.318  -4798.755  1172  
       #     Group : in2reg           *  -12.858   -447.588   143  
       #     Group : rams2reg         *  -19.492  -1006.216   223  
       #     Group : reg2cgate        *  -19.302   -897.689   162  
       #     Group : reg2out          *   -1.007     -1.007     1  
       #     Group : reg2rams         *  -14.626   -414.640    67  
       #     Group : reg2reg          *  -78.318  -2085.586   605  
    if (defined $generate_path_groups) {
        my @rpt_files = glob "$file/run_dir/reports/*/setup.analysis_summary.rpt";
        @rpt_files    = sort { -M "$a" <=> -M "$b" } @rpt_files;
        if ( defined $rpt_files[0] && -r $rpt_files[0] ) {
           my $rpt_file = $rpt_files[0];
           print "Generated path_groups from $file\n";
       }
    }

    ## If $file is a logfile, change to directory to see only reports that reached a specific stage
    ##     vivid_compare.pl */logs/opt_signoff.log
    if ( $file =~ m:(.*)/logs/.*log:) {
        $file = $1;
    }

    ## If $file is a directory, look for the metrics file
    if (-d $file) { 
        # Look for flow.metrics. Pick first one
        my @glob_files  = glob "$file/*/flow.metrics";
        push @glob_files, "$file/flow.metrics" if -r "$file/flow.metrics";
        push @glob_files, "$file/metrics.json" if -r "$file/metrics.json";
        push @glob_files, glob "$file/runs/*/*/*/outputs/*/flow.metrics";

        if (@glob_files > 1) { 
            print "Found these metrics files. Most recent is used:\n\t";
            print join "\n\t", @glob_files;
            print "\n";
        }

        ## Get the most recent metrics file
        @glob_files = sort { -M "$a" <=> -M "$b" } @glob_files;
        if ( defined $glob_files[0] && -r $glob_files[0] ) {
           $file = $glob_files[0];
        } else {
            print "Skipping:\t$file\n";
            next;
        }
    } 


    if (!-r $file) {
        print STDERR  "${red}Unable to read $file${end_color}\n";
        next;
    }
    print "Reading:\t$file\n";

    $success = 1;
    my $name = $file;
    ## TODO : Fix assumption of run_tag = run_dir
    #
    if ($opt_strip_run_dir) {
        if ($file =~ m:(\S+)/run_dir[^/]*/: ) {
            $name = $1;
        } elsif ($file =~ m:(\S+)/flow.metrics:) {
            $name = $1;
        }
    }
    $name =~ s/$strip_name// if defined $strip_name;

    print $user_script_fh "read_metric -id $name  $file\n";
    #print $user_script_fh "set_metric_header -id $name  -name run_name -value { $name : $file }\n";
    print $user_script_fh "set_metric_header -id $name  -name run_name -value { $name }\n";

    # $name =~ s:run_dir/flow.metrics::; 
    push @runs, $name;
}

if (defined $generate_path_groups) {
    my $new_config = "/tmp/croysdal_vivid_config.txt";

    ##  Generate new config using @path_groups

    $vivid_config = $new_config;

}

print $user_script_fh "report_metric -format vivid -file ${output} -id \"";
print $user_script_fh join " ", @runs;
print $user_script_fh "\"\n";

print STDERR "${red}No runs found${end_color}\n" and exit if ! $success;


my $cmd;

if (defined $flowtool) {
    $cmd  = $flowtool;
} else {
    $cmd  = "flowtool ";
    ## Cadence setting
    if (-x "/icd/flow/INNOVUS/INNOVUS211/21.14-e006_1/lnx86/bin/flowtool") {
        $cmd  = "/icd/flow/INNOVUS/INNOVUS211/21.14-e006_1/lnx86/bin/flowtool ";
    }
}
my $flowtool_version = `$cmd -version`;
# Flowtool v20.10-p025_1, built 01/19/2021 04:41 PST
if ($flowtool_version !~ /v2\d\.\d/) { 
    print "Flowtool not version 2x.x.\n";
    my $flowtool_path = `which $cmd`;
    print "\t\tVerion: $flowtool_version\n";
    print "\t\tPath:   $flowtool_path\n";
    exit -1;
}
$cmd    .= " -files $user_script ";


if ($test) {
    print "$cmd\n\n";
    system ("cat $user_script");
} else {
    unlink "flow.status.lock";
    unlink "flow.metrics.lock";
    unlink $output;
    my $vivid_log="/tmp/vivid_compare_$ENV{USER}.log";
    print "Starting flowtool\n";
    system ("$cmd > $vivid_log 2> $vivid_log");
    print "Flowtool finished\n";
    print "$cmd\n\n";
    print "Flowtool log in $vivid_log\n"; 
    # system ("$cmd");
    print "Wrote: $output\n";
    if ($open && ! $no_open && -r $output) {
        $firefox_opt = "--new-tab" if defined $new_tab;
        print "Running: firefox $firefox_opt $output\n";
        system ("firefox $firefox_opt $output 2>/dev/null &");
    }
}

## Update to show perc
#d|p&amp

unlink $user_script unless $keep_script;
unlink "flow.status.lock";
unlink "flow.metrics.lock";
system ("rm -f flowtool.log*");

if ($mail) {
    system ("~croysdal/bin/send_file $output");
}

