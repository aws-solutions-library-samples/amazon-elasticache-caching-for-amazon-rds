# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import datetime
import json
import os
import glob
import re
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from rich import print
from tqdm import tqdm

# -------------------------------------------------------------------------------------------------------

def get_folders(folder: str) -> list:
    return [f for f in os.listdir(folder) if os.path.isdir(os.path.join(folder, f))]


def get_files(folder: str) -> list:
    return [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]


# -------------------------------------------------------------------------------------------------------
def analyze_logs(folder: str, scenario: str, data: dict):
    # Loop through each directory and process each file.
    boxes = get_folders(folder)
    for box in tqdm(boxes):
        files = get_files(os.path.join(folder, box))
        for file in files:
            if re.match(scenario, file):
                with open(os.path.join(folder, box, file), 'r', encoding="utf-8") as f:
                    file_data = json.loads(f.read())
                    for timestamp in file_data.keys():
                        # format = f"%Y-%m-%d %H:%M:%S"
                        format = f"%H:%M:%S"
                        datetime_str = datetime.datetime.fromtimestamp(int(timestamp)).strftime(format)      
                        if datetime_str not in data.keys():
                            # Add a new entry but make sure no division by 0
                            if file_data[timestamp]['count'] == 0:
                                avg_time = 0
                            else:
                                avg_time = file_data[timestamp]['query_time'] / file_data[timestamp]['count']
                            data[datetime_str] = {
                                'count': file_data[timestamp]['count'],
                                'query_time': file_data[timestamp]['query_time'],
                                'min_time': file_data[timestamp]['min_time'],
                                'max_time': file_data[timestamp]['max_time'],
                                'avg_time': avg_time,
                            }
                        else:
                            # An entry for this time stamp exists update the values
                            data[datetime_str]['count'] += file_data[timestamp]['count']
                            data[datetime_str]['query_time'] += file_data[timestamp]['query_time']                                                
                            if file_data[timestamp]['min_time'] < data[datetime_str]['min_time']:
                                data[datetime_str]['min_time'] = file_data[timestamp]['min_time']                            
                            if file_data[timestamp]['max_time'] > data[datetime_str]['max_time']:
                                data[datetime_str]['max_time'] = file_data[timestamp]['max_time']                        
                            data[datetime_str]['avg_time'] = data[datetime_str]['query_time']/data[datetime_str]['count']
                        last_time = datetime_str
                    # print(data[last_time])


# -------------------------------------------------------------------------------------------------------
def plot_charts(df, title, plot_file):
    # Convert the index to a DateTimeIndex
    # df.index = pd.to_datetime(df.index, format=f"%H:%M:%S")
    fig, axs = plt.subplots(2, 1, layout='constrained')
    plt.title(f"{title}")
    # Create a time series plot with multiple lines
    plt.plot(figsize=(12, 12))
    # -------------------------------------------------------------------------------------------------------
    # Add first chart with data series for count per second
    axs[0].plot(df.index, df['count'], label='count')
    # axs[0].plot(df.index, df['query_time'], label='query_time')
    # Add labels and title
    # axs[0].ylim(0, 20000)
    axs[0].set_xlabel('Time')
    axs[0].set_ylabel('QPS')
    axs[0].tick_params(axis='x', rotation=90)
    # axs[0].title(f"{title} QPS (Count)")
    # Show the legend
    axs[0].legend()
    # -------------------------------------------------------------------------------------------------------
    # Add second chart with response times
    # axs[1].ylim(0, 0.5)
    axs[1].plot(df.index, df['min_time'], label='min_time')
    axs[1].plot(df.index, df['avg_time'], label='avg_time')
    # axs[1].plot(df.index, df['max_time'], label='max_time')
    # Add labels and title
    axs[1].set_xlabel('Time')
    axs[1].set_ylabel('Seconds')
    # axs[1].title(f"{title} Response Time (sec)")
    axs[1].tick_params(axis='x', rotation=90)
    # Show the legend
    axs[1].legend()
    # Save the plot
    plt.savefig(f"{plot_file}", dpi=300)
    # Show the plot
    # plt.show()


# -------------------------------------------------------------------------------------------------------
def create_charts(rdbms: str, read_rate: int, file_name: str, log_ext: str):
    read_rate = int(read_rate * 100)
    write_rate = 100 - read_rate
    # RDS Oracle server XL server instance + EC 60:40 200 threads 10k execution
    # scenario is the re to only process the correct log file. I.E. the files copied by the copy_logfiles
    # scenario = '^scenario02_ORCL_.*_1685138.*$'
    folder = 'logs'
    plot_file = file_name.split('.')[0]
    scenario = f"^harness_{rdbms}_.*_{log_ext}.*$"
    # print(scenario)
    
    data = {}
    analyze_logs(folder=folder, scenario=scenario, data=data)
    dataKeys = list(data.keys())
    dataKeys.sort()
    sortedData = {i: data[i] for i in dataKeys}
    data = sortedData
    # print(data)

    # Convert the dictionary to a Pandas DataFrame
    title = f"{rdbms} + EC {read_rate}:{write_rate} R/W"
    df = pd.DataFrame.from_dict(data, orient='index')
    print(df.head())
    plot_charts(df, title, plot_file)
