import os


path = "/nfs/site/disks/w.ssubba.505/ENYO_RESULTS/Python_VENV/issue_completed_runs/enyo_issue_78.3i0s_0.5beta_swp_5.4_3.5_200/reports/postroute/setup.gba.rpt"

N 	= 50

SLACK_LST = []

with open(path, 'r') as f:
	for i,line in enumerate(f.readlines()):
		line_data = line.strip().split()
		print(line_data)
		if line.strip().startswith('Group') and line_data[1]== 'reg2reg':
			slack_line = f.readlines()[i + 19]
			SLACK_LST.append(float(slack_line.split()[1]))

#AvgN slack is nothing but the average of the slacks of first N paths from the Setup GBA report.
#This value is never based on Hold GBA report.
#Setup is the time the data signal must be stable for the clock pulse to arrive to get captured.
#Hold is the time the data signal must be stable after the clock pulse has arrived to get successfully latched.
#So, the time required to capture signals is deciding operating frequency.
#So, if the top slacks can be reduced, then the AvgN slack will go down			
			
AvgN_Slack 	= sum(SLACK_LST[:N])	

Nth_slack	= SLACK_LST[N]
	
print(AvgN_Slack, Nth_slack)
			
