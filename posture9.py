import csv
import statistics
import matplotlib.pyplot as plt
import numpy as np
import requests
import io
import os
from urllib.parse import quote

matrixin=[]

# original raw_url can be a github blob URL or a raw.githubusercontent URL
raw_url = 'https://github.com/clarkkeithf-sketch/Posturography/blob/main/Sample.Table%202_17_10_25_06_47.csv'
local_path = r'c:\PosturePLC\Posturography\Sample.Table 2_17_10_25_06_47.csv'

# convert a github "blob" URL into a raw.githubusercontent URL (and percent-encode the path)
if 'github.com' in raw_url and '/blob/' in raw_url:
    base, tail = raw_url.split('/blob/', 1)                 # base = https://github.com/user/repo
    base = base.replace('https://github.com/', 'https://raw.githubusercontent.com/')
    raw_url = base + '/' + quote(tail, safe='/')           # quote but keep '/' separators

csvfile_obj = None
try:
    resp = requests.get(raw_url, timeout=10)
    if resp.status_code == 200:
        csvfile_obj = io.StringIO(resp.text)
    else:
        print(f"Remote returned {resp.status_code} for URL: {raw_url}")
except requests.RequestException as e:
    print(f"Request failed: {e}")

if csvfile_obj is None:
    if os.path.exists(local_path):
        print(f"Falling back to local file: {local_path}")
        csvfile_obj = open(local_path, 'r', newline='')
    else:
        raise SystemExit(f"File not found remotely or locally.\nTried: {raw_url}\nLocal: {local_path}")

# create the CSV reader used below
csv_reader = csv.reader(csvfile_obj)

for i, row in enumerate(csv_reader):
  current_angle=row[3]
  if current_angle != '0':
   matrixin.append(row)

matrix = list(zip(*matrixin))

rowsm = matrix[0]
rowsm_list=list(rowsm)
rowsm_temp=[int(s) for s in rowsm_list[1:]]
rowsm=rowsm_temp

left = matrix[1]
left_list=list(left)
left_temp=[int(s) for s in left_list[1:]]
left=left_temp

right = matrix[2]
right_list=list(right)
right_temp=[int(s) for s in right_list[1:]]
right=right_temp

angle= matrix[3]
angle_list=list(angle)
angle_temp=[int(s) for s in angle_list[1:]]
angle=[x/100 for x in angle_temp]

"""print ("ROWS ", rowsm)
print ("LEFT ", left)
print ("RIGHT", right)
print ("ANGLE " ,angle)"""
# AT this point there are 4 lists holding data for entire run that need to be 
# analyzed for each run pulling off segments 10/sec determined by change in angle

#check for current angle and use this to get the analysis for the current angle
trials = 0 #ow many angles were tested
total_samples = 1 # total iterations fist time to figure out how many seconds at 10 samples per second
start_marker = 20 # and outlandish number to start chek on how many
angle_list = []
for pos, item in enumerate(angle):
  if start_marker == item:
    total_samples = total_samples + 1 #increment check on number of samples per test or how many seconds
  if pos == 0: #first time
    current_angle=item
    angle_list.append(item)
    trials = trials + 1
    start_marker = item #set first angle marker and total first set to determine how many per test angle
  if pos >= 1: #every other time new angle comes up
    if current_angle != item:
     current_angle = item
     angle_list.append(item)
     trials=trials + 1
     

# Here there is now a count of how many samples per angle and a list of angles_list, trials is number of angles tested, total_samples is 
# number of samples per angle  10=1 sec  20=2 sec etc
print ("number of angle trials= ", trials, "# samples each angle= ", total_samples) 
print (" ")

left_stdev = []
right_stdev = []

for i in range(0,trials):
 if i == 0:
  start_index = 0
  end_index = total_samples
 else:
  start_index = start_index + total_samples
  end_index = end_index + total_samples

 left1 = left[start_index:end_index]
 right1 = right[start_index:end_index]

 lstdev = statistics.stdev(left1)
 lstdev = round(lstdev)
 left_stdev.append(lstdev)
 print(f"LEFT SENSOR  Pval:  {left_stdev[i]:.0f}")

 rstdev = statistics.stdev(right1)
 rstdev = round(rstdev)
 right_stdev.append(rstdev)
 print(f"RIGHT SENSOR Pval: {right_stdev[i]:.0f}")

 print(f"Angle: {angle_list[i]:.2f} degrees")

 if angle_list[i] < 0:
  print("LEFT LEG\n")
 else:
  print("RIGHT LEG\n")

'''Here we have lists for bar graph angle_list, right_stdev, left_stdev
print (angle_list)
print (left_stdev)
print (right_stdev)'''
sum_stdev = []
#sum the standard deviations
for i in range(trials):
  std_val = left_stdev[i] + right_stdev[i]
  sum_stdev.append(std_val)


#plotting the bar   graph of standard deviations at each angle   most important graph
# Create the bar chart
bars = plt.bar(angle_list, sum_stdev, width=0.3, color='skyblue')

#bar_label
plt.bar_label(bars)
plt.xticks(angle_list)
# Add labels and title
plt.xlabel('Angle Tested -left  +right')
plt.ylabel('Pvalue Sum')
plt.title('Sensor Pvalue for each angle tested')

# Display the  bar plot
plt.show()

#plotting individual angle sensor line graph
list_sec = []
#create x axis record of ticks per sec
for s in range(total_samples):
 list_sec.append(s+1)
       
for i in range(trials): #graphs or angles tested
  leftx = left[i*total_samples:total_samples*(i+1)]
  rightx = right[i*total_samples:total_samples*(i+1)]

  # Data for the first line
  x1 = np.array(list_sec)
  y1 = np.array(leftx)

  # Data for the second line
  x2 = np.array(list_sec)
  y2 = np.array(rightx)

  # Plot the first line
  plt.plot(x1, y1, label='Left Sensor', color='blue', linestyle='-')

  # Plot the second line
  plt.plot(x2, y2, label='Right Sensor', color='red', linestyle='--')

  # Add labels and title
  plt.xlabel("Tenths of SECONDS")
  plt.ylabel("Sensor Response")
  tit = "Posturography - Footfoundation  " + str(angle_list[i]) + " Degrees"
  plt.title(tit)

  # Add a legend to distinguish the lines
  plt.legend()

  # Display the plot
  plt.show()
