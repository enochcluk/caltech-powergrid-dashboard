import os
from datetime import datetime, timedelta
from time import time
import pandas as pd

data_loc = 'C:/Users/enoch/Documents/GitHub/caltech-twin/digitaltwin/bms_csv_data/cleaned_data'  # CHANGE TO YOUR OWN DIRECTORY

def datetime_range(start, end, delta):
    current = start
    while current <= end:
        yield current
        current += delta

def generate_timestamps(start_day, start_month, start_year, start_hour, start_min, end_day, end_month, end_year, end_hour, end_min, delta):
    return [dt.strftime('%Y-%m-%dT%H:%M-07:00') for dt in 
       datetime_range(datetime(start_year, start_month, start_day, start_hour, start_min), 
       datetime(end_year, end_month, end_day, end_hour, end_min), 
       timedelta(minutes=delta))]

if __name__ == '__main__':

    for root, dirs, files in os.walk(data_loc):
        for file in files:
            df_old = pd.read_csv(root + '/' + file)
            df_new = pd.DataFrame(columns=['t', 'v', 's', 'r'])
            start_timestamp = df_old.at[0, 't']
            end_timestamp = df_old.at[df_old.shape[0]-1, 't']
            start_day = int(start_timestamp[8:10])
            start_month = int(start_timestamp[5:7])
            start_year = int(start_timestamp[0:4])
            start_hour = int(start_timestamp[11:13])
            start_min = int(start_timestamp[14:16])
            end_day = int(end_timestamp[8:10])
            end_month = int(end_timestamp[5:7])
            end_year = int(end_timestamp[0:4])
            end_hour = int(end_timestamp[11:13])
            end_min = int(end_timestamp[14:16])
            timestamps = generate_timestamps(start_day, start_month, start_year, start_hour, start_min, end_day, end_month, end_year, end_hour, end_min, 15)
            df_new['t'] = timestamps
            new_idx = 0
            for index, row in df_old.iterrows():
                if index != 0:
                    o_start_day = int(df_old.at[index-1, 't'][8:10])
                    o_start_month = int(df_old.at[index-1, 't'][5:7])
                    o_start_year = int(df_old.at[index-1, 't'][0:4])
                    o_start_hour = int(df_old.at[index-1, 't'][11:13])
                    o_start_min = int(df_old.at[index-1, 't'][14:16])
                    o_end_day = int(row['t'][8:10])
                    o_end_month = int(row['t'][5:7])
                    o_end_year = int(row['t'][0:4])
                    o_end_hour = int(row['t'][11:13])
                    o_end_min = int(row['t'][14:16])
                    o_start = datetime(o_start_year, o_start_month, o_start_day, o_start_hour, o_start_min)
                    o_end = datetime(o_end_year, o_end_month, o_end_day, o_end_hour, o_end_min)
                    diff = o_end - o_start
                if index != 0 and (diff.total_seconds() >= 900 or row['r'] == 1):  # r=1 indicates that at least one measurement was skipped
                    if diff.total_seconds() >= 3600:
                        while new_idx < df_new.shape[0] and df_new.at[new_idx, 't'][0:16] != row['t'][0:16]:
                            df_new.at[new_idx, 'v'] = -1
                            df_new.at[new_idx, 'r'] = 3  # r=3 indicates inability to interpolate data due to large time gap
                            df_new.at[new_idx, 's'] = 0
                            new_idx+=1
                    else:
                        if diff.total_seconds() == 1800:
                            df_new.at[new_idx, 'v'] = df_old.at[index-1, 'v'] + .5*(row['v']-df_old.at[index-1, 'v'])
                            df_new.at[new_idx, 'r'] = 2  # r=2 indicates interpolated data
                            df_new.at[new_idx, 's'] = 0
                            new_idx+=1
                        elif diff.total_seconds() == 2700:
                            df_new.at[new_idx, 'v'] = df_old.at[index-1, 'v'] + (row['v']-df_old.at[index-1, 'v'])/3
                            df_new.at[new_idx, 'r'] = 2
                            df_new.at[new_idx, 's'] = 0
                            new_idx+=1
                            df_new.at[new_idx, 'v'] = df_old.at[index-1, 'v'] + 2*(row['v']-df_old.at[index-1, 'v'])/3
                            df_new.at[new_idx, 'r'] = 2
                            df_new.at[new_idx, 's'] = 0
                            new_idx+=1
                    df_new.at[new_idx, 'v'] = row['v']
                    df_new.at[new_idx, 'r'] = row['r']
                    df_new.at[new_idx, 's'] = row['s']
                    new_idx+=1
                else:
                    df_new.at[new_idx, 'v'] = row['v']
                    df_new.at[new_idx, 'r'] = row['r']
                    df_new.at[new_idx, 's'] = row['s']
                    new_idx+=1
            df_new = df_new.set_index('t')
            df_new.to_csv(root + '/' + file, index=True)