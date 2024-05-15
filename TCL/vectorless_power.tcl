# Read-DB
read_db run_dir_ext_isopp/dbs/opt_signoff.enc
# Sourcing activity
set_multi_cpu_usage -local_cpu 21
propagate_activity 
read_activity_file -reset 
set_default_switching_activity -reset
set_switching_activity -reset
set_default_switching_activity -global_activity 0.3
# Reporting Power
report_power -view func_tttt_v065_t100_max_tttt_100c > power_0p65v.rpt
report_power -view func_tttt_v110_t100_min_tttt_100c > power_1p10v.rpt
