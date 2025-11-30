import csv
import statistics
import numpy as np
from js import document
import matplotlib.pyplot as plt
import io
from typing import TYPE_CHECKING

# Don't call matplotlib.use() — let Pyodide handle the backend automatically

if TYPE_CHECKING:
    # help the type checker (no runtime effect)
    from pyodide.ffi import create_proxy  # type: ignore

try:
    from pyodide.ffi import create_proxy
except Exception:
    # fallback for local runs / static checking: a no-op proxy
    def create_proxy(fn):
        return fn

matrixin = []

processing = False  # add this flag at module level

async def load_csv(evt=None):
    global processing
    if processing:
        return  # prevent duplicate calls
    processing = True
    
    try:
        file = document.getElementById("csv_file").files.item(0)
        if not file:
            processing = False
            return
        text = await file.text()
        reader = io.StringIO(text)
        csv_reader = csv.reader(reader)

        matrixin.clear()
        for i, row in enumerate(csv_reader):
            if len(row) < 4:
                continue
            current_angle = row[3]
            if current_angle != '0':
                matrixin.append(row)

        # clear previous results/plots
        document.getElementById("results").innerHTML = ""
        try:
            plt.close('all')
        except Exception:
            pass

        process_data()
    finally:
        processing = False

def process_data():
    if not matrixin:
        document.getElementById("results").innerHTML = "No data loaded."
        return

    matrix = list(zip(*matrixin))

    rowsm = list(map(int, matrix[0][1:]))
    left = list(map(int, matrix[1][1:]))
    right = list(map(int, matrix[2][1:]))
    angle = list(map(lambda x: int(x) / 100, matrix[3][1:]))

    trials = 0
    start_marker = 20
    angle_list = []
    
    # Find angle changes to count trials
    for pos, item in enumerate(angle):
        if pos == 0:
            current_angle = item
            angle_list.append(item)
            trials += 1
            start_marker = item
        elif current_angle != item:
            current_angle = item
            angle_list.append(item)
            trials += 1

    # Calculate total_samples correctly: total data points / number of trials
    total_samples = len(angle) // trials

    left_stdev = []
    right_stdev = []

    for i in range(trials):
        start_index = i * total_samples
        end_index = start_index + total_samples

        left1 = left[start_index:end_index]
        right1 = right[start_index:end_index]

        if len(left1) < 2 or len(right1) < 2:
            lstdev = 0
            rstdev = 0
        else:
            lstdev = round(statistics.stdev(left1))
            rstdev = round(statistics.stdev(right1))

        left_stdev.append(lstdev)
        right_stdev.append(rstdev)

        update_results(angle_list[i], lstdev, rstdev)

    plot_data(angle_list, left_stdev, right_stdev, left, right, total_samples, trials)

def update_results(angle, left_stdev_val, right_stdev_val):
    result_div = document.getElementById("results")
    result_div.innerHTML += f"Angle: {angle:.2f} degrees<br>"
    result_div.innerHTML += f"LEFT SENSOR Pval: {left_stdev_val:.0f}<br>"
    result_div.innerHTML += f"RIGHT SENSOR Pval: {right_stdev_val:.0f}<br>"
    result_div.innerHTML += "<br>"

def plot_data(angle_list, left_stdev, right_stdev, left, right, total_samples, trials):
    sum_stdev = [left_stdev[i] + right_stdev[i] for i in range(len(angle_list))]

    # First graph - bar chart
    plt.figure(figsize=(6,4))
    bars = plt.bar(angle_list, sum_stdev, width=0.3, color='skyblue')
    try:
        plt.bar_label(bars)
    except Exception:
        pass
    plt.xlabel('Angle Tested - left + right')
    plt.ylabel('Pvalue Sum')
    plt.title('Sensor Pvalue for each angle tested')
    plt.show()
    plt.close()

    # Second set of graphs - individual line graphs per angle
    list_sec = list(range(1, total_samples + 1))
           
    for i in range(trials):
        leftx = left[i*total_samples:total_samples*(i+1)]
        rightx = right[i*total_samples:total_samples*(i+1)]

        x1 = np.array(list_sec)
        y1 = np.array(leftx)
        x2 = np.array(list_sec)
        y2 = np.array(rightx)

        plt.figure(figsize=(8, 5))
        plt.plot(x1, y1, label='Left Sensor', color='blue', linestyle='-')
        plt.plot(x2, y2, label='Right Sensor', color='red', linestyle='--')
        plt.xlabel("Tenths of SECONDS")
        plt.ylabel("Sensor Response")
        plt.title(f"Posturography - Footfoundation {angle_list[i]} Degrees")
        plt.legend()
        plt.show()
        plt.close()