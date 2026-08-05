# Shared immutable string/list constants.
import re

_IP_SCAN_ROOT_ = '/prj/qct/chips/rolasp/roc/tapeout/r0_tsmcn3e/hm'
_REGISTER_TERMS_ = ['_sdf', '_s2df']
_MEMORY_TERMS_ = ['qcsram', 'qcrf']
_LATCH_TERMS_ = ['ndlat']

_STARTPOINT_REGEX_ = re.compile(r'^\s*Startpoint:\s*(.+?)\s*$')
_ENDPOINT_REGEX_ = re.compile(r'^\s*Endpoint:\s*(.+?)\s*$')
_LAST_COMMON_PIN_REGEX_ = re.compile(r'^\s*Last common pin:\s*(.+?)\s*$')
_PATH_GROUP_REGEX_ = re.compile(r'^\s*Path Group:\s*(.+?)\s*$')
_PATH_TYPE_REGEX_ = re.compile(r'^\s*Path Type:\s*(\S+)\s*$')
_CLOCK_EDGE_REGEX_ = re.compile(r'^\s*clock\s+(.+?)\s*\((rise|fall) edge\)\s*(.*)$')
_CLOCK_NETWORK_DELAY_REGEX_ = re.compile(r'^\s*clock network delay \(propagated\)\s*(.*)$')
_CPPR_REGEX_ = re.compile(r'^\s*clock reconvergence pessimism\s+([+-]?\d+(?:\.\d+)?)')
_UNCERTAINTY_REGEX_ = re.compile(r'^\s*(clock uncertainty|inter-clock uncertainty)\s+([+-]?\d+(?:\.\d+)?)', re.IGNORECASE)
_LIBRARY_TIME_REGEX_ = re.compile(r'^\s*library\s+([a-zA-Z]+)\s+time\s+([+-]?\d+(?:\.\d+)?)', re.IGNORECASE)
_PATH_MARGIN_REGEX_ = re.compile(r'^\s*path margin\s+([+-]?\d+(?:\.\d+)?)', re.IGNORECASE)
_SLACK_REGEX_ = re.compile(r'^\s*slack\s*\([^)]*\)\s+([+-]?\d+(?:\.\d+)?)\s*$')
_FLOAT_NUMBER_REGEX_ = re.compile(r'([+-]?\d+(?:\.\d+)?)')
_POINT_HEADER_REGEX_ = re.compile(r'^\s*Point\s+')
_STAGE_LINE_REGEX_ = re.compile(r'^\s*(.+?)\s+\(([^()]*)\)\s*(.*)$')
_CELL_REF_SUFFIX_REGEX_ = re.compile(r'[0-9][pqxz][0-9]{2}$', re.IGNORECASE)
_TRAILING_LOCATION_REGEX_ = re.compile(r'\(\s*[-+]?\d+(?:\.\d+)?\s*,\s*[-+]?\d+(?:\.\d+)?\s*\)\s*$')
_REPORT_FILE_REGEX_ = re.compile(r'^rpt_\d+\.txt$')

_NA_TEXT_ = 'NA'
_TOP_TEXT_ = 'top'

_CAT_WITHIN_HM_ = 'Within HM'
_CAT_HM_TO_HM_ = 'HM to HM'
_CAT_TOP_TO_HM_ = 'Top to HM'
_CAT_OTHER_ = 'Other'

_DIR_HM_INTERNAL_ = 'HM Internal'
_DIR_HM_TO_HM_ = 'HM to HM'
_DIR_TOP_TO_HM_ = 'Top to HM'
_DIR_HM_TO_TOP_ = 'HM to Top'

_STATUS_FIXABLE_ = 'FIXABLE'
_STATUS_FIXABLE_BUF_REMOVE_ = 'FIXABLE_BY_BUFFER_CHAIN_REDUCTION'
_STATUS_UNFIXABLE_ = 'UNFIXABLE'
_STATUS_SKIPPED_ = 'SKIPPED'

_INTERFACE_DOMINANT_TEXT_ = 'INTERFACE'

_XLSX_IMPORT_ERROR_ = 'ERROR: xlsxwriter is required. Install with: pip install XlsxWriter'

_OUTPUT_VALIDATION_ALL_ = 'validation_all.csv'
_OUTPUT_VALIDATION_MISMATCH_ = 'validation_mismatch.csv'

_EXPECTED_TOP_TOP_WITHIN_ = 'top_top_as_within_hm'
_EXPECTED_WITHIN_SUFFIX_ = 'within_hm_same_or_suffix'
_EXPECTED_TOP_HM_ = 'top_hm'
_EXPECTED_HM_TOP_ = 'hm_top'
_EXPECTED_HM_HM_ = 'hm_hm'
_EXPECTED_UNKNOWN_ = 'unknown'

_MAIN_HEADER_ = [
    'Startpoint', 'Endpoint', 'Last Common Pin', 'Path Group',
    'Path Type',
    'Start HM/IP', 'End HM/IP', 'HM Interface', 'Middle IPs',
    'Output Port Pin', 'Output Port HM', 'Input Port Pin', 'Input Port HM',
    'Launch Clock', 'Capture Clock',
    'Launch Latency', 'Capture Latency',
    'Clock Period', 'Uncertainty', 'CPPR',
    'Library Setup/Hold Time', 'Path Margin', 'Data Required Time', 'Data Arrival Time', 'Slack',
    'Skew', 'Path Depth', 'Buffer Count', 'Inverter Count',
    'Back-to-Back Inverter Count', 'Logic Inversion',
    'Pure Combinational Depth',
    'Total Data Path Delay', 'Total Net Delay', 'Total Cell Delay',
    'Highest Crosstalk', 'Total Crosstalk',
    'Highest Transition',
    'Top Cell Delay', 'Top Net Delay',
    'reg2io Total Delay', 'io2io Total Delay', 'io2reg Total Delay',
    'reg2io Logic Depth', 'io2io Logic Depth', 'io2reg Logic Depth',
    'reg2io Pure Comb Depth', 'io2io Pure Comb Depth', 'io2reg Pure Comb Depth',
    'reg2io Top Cell Delay', 'io2io Top Cell Delay', 'io2reg Top Cell Delay',
    'reg2io Top Net Delay', 'io2io Top Net Delay', 'io2reg Top Net Delay',
    'Highest Fanout', 'Highest Capacitance',
    'reg2io Top Cap', 'io2io Top Cap', 'io2reg Top Cap',
    'reg2io Highest Fanout', 'io2io Highest Fanout', 'io2reg Highest Fanout'
]

_SPECIAL_FOR_INTERFACE_ = [
    'Output Port Pin', 'Output Port HM', 'Input Port Pin', 'Input Port HM',
    'reg2io Total Delay', 'io2io Total Delay', 'io2reg Total Delay',
    'reg2io Logic Depth', 'io2io Logic Depth', 'io2reg Logic Depth',
    'reg2io Pure Comb Depth', 'io2io Pure Comb Depth', 'io2reg Pure Comb Depth',
    'reg2io Top Cap', 'io2io Top Cap', 'io2reg Top Cap',
    'reg2io Top Cell Delay', 'io2io Top Cell Delay', 'io2reg Top Cell Delay',
    'reg2io Top Net Delay', 'io2io Top Net Delay', 'io2reg Top Net Delay',
    'reg2io Highest Fanout', 'io2io Highest Fanout', 'io2reg Highest Fanout',
]

_SPECIAL_FOR_WITHIN_HM_ = [
    'Start HM/IP', 'End HM/IP', 'HM Interface',
    'Middle IPs',
    'Output Port Pin', 'Output Port HM', 'Input Port Pin', 'Input Port HM',
    'reg2io Total Delay', 'io2io Total Delay', 'io2reg Total Delay',
    'reg2io Logic Depth', 'io2io Logic Depth', 'io2reg Logic Depth',
    'reg2io Pure Comb Depth', 'io2io Pure Comb Depth', 'io2reg Pure Comb Depth',
    'reg2io Top Cap', 'io2io Top Cap', 'io2reg Top Cap',
    'reg2io Top Cell Delay', 'io2io Top Cell Delay', 'io2reg Top Cell Delay',
    'reg2io Top Net Delay', 'io2io Top Net Delay', 'io2reg Top Net Delay',
    'reg2io Highest Fanout', 'io2io Highest Fanout', 'io2reg Highest Fanout',
]

_SPECIAL_IO2IO_FOR_TOP_TO_HM_ = [
    'io2io Total Delay',
    'io2io Logic Depth',
    'io2io Pure Comb Depth',
    'io2io Top Cap',
    'io2io Top Cell Delay',
    'io2io Top Net Delay',
    'io2io Highest Fanout'
]

_WHATIF_HEADER_HM_TO_HM_ = [
    'Startpoint', 'Endpoint', 'Output Port HM', 'Input Port HM',
    'Data Required Time', 'Original Data Arrival Time', 'Original Slack', 'Max Delay Cap',
    'reg2io Original Delay', 'io2io Original Delay', 'io2reg Original Delay',
    'reg2io Capped Delay', 'io2io Capped Delay', 'io2reg Capped Delay',
    'Achievable Data Arrival Time', 'What-If Slack',
    'reg2io Post Buffer/Inv Removal', 'io2io Post Buffer/Inv Removal', 'io2reg Post Buffer/Inv Removal',
    'Achievable Arrival Post Buffer/Inv Removal', 'Slack Post Removal',
    'Dominant Post-Cap Contributor', 'Path Status'
]

_WHATIF_HEADER_TOP_TO_HM_ = [
    'Startpoint', 'Endpoint', 'Path Direction', 'HM Name',
    'Data Required Time', 'Original Data Arrival Time', 'Original Slack', 'Max Delay Cap',
    'SegmentA Original Delay', 'SegmentB Original Delay',
    'SegmentA Capped Delay', 'SegmentB Capped Delay',
    'Achievable Data Arrival Time', 'What-If Slack',
    'SegmentA Post Buffer/Inv Removal', 'SegmentB Post Buffer/Inv Removal',
    'Achievable Arrival Post Buffer/Inv Removal', 'Slack Post Removal',
    'Dominant Post-Cap Contributor', 'Path Status'
]

_WHATIF_HEADER_WITHIN_OR_OTHER_ = [
    'Startpoint', 'Endpoint', 'Output Port HM', 'Input Port HM',
    'Data Required Time', 'Original Data Arrival Time', 'Original Slack', 'Max Delay Cap',
    'Internal Original Delay', 'Internal Capped Delay',
    'Internal Delay Post Buffer/Inv Removal',
    'Achievable Data Arrival Time', 'What-If Slack',
    'Achievable Arrival Post Buffer/Inv Removal', 'Slack Post Removal',
    'Dominant Post-Cap Contributor', 'Path Status'
]

_WHATIF_HEADER_OTHER_ = [
    'Startpoint', 'Endpoint', 'Data Required Time', 'Original Data Arrival Time',
    'Original Slack', 'Max Delay Cap', 'Original Total Delay',
    'Capped Total Delay', 'Achievable Data Arrival Time', 'What-If Slack',
    'Post Buffer/Inv Removal Delay', 'Arrival Post Buffer/Inv Removal',
    'Slack Post Removal', 'Path Status'
]

_ARGPARSE_ANALYZER_DESC_ = 'PrimeTime timing report analyzer (streaming, Python 3.6).'
_ARGPARSE_VALIDATE_DESC_ = 'Validate report classification/HM detection against merged summary CSV.'

_ARGHELP_INPUT_ = 'Input timing report file or directory of reports'
_ARGHELP_OUTPUT_DIR_ = 'Output directory for generated .xlsx files'
_ARGHELP_ANALYSIS_TYPE_ = 'Analysis type to extract'
_ARGHELP_MAX_DELAY_ = 'Max stage delay cap for what-if analysis; if omitted, What-If analysis is skipped'

_ARGHELP_SUMMARY_CSV_ = 'Path to merged_reg2reg.max.clock_summary.csv'
_ARGHELP_REPORT_DIR_ = 'Directory containing rpt_*.txt reports'
_ARGHELP_VALIDATE_OUTPUT_DIR_ = 'Directory for validation CSV outputs'
_ARGHELP_VALIDATE_ANALYSIS_ = 'Path type used in report parsing'

_LOGMSG_BUILDING_IP_SET_ = 'Building IP directory leaf-name set from %s (excluding names containing "_scratch")'
_LOGMSG_INPUT_NOT_EXIST_ = 'Input path does not exist: %s'
_LOGMSG_MAX_DELAY_INVALID_ = '--max-delay must be >= 0 when provided'
_LOGMSG_COMPLETED_REPORT_ = 'Completed report %s: wrote %d paths to %s'
