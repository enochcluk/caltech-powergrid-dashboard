# Copyright placeholder
# Author: Lucien Werner
# Date: July 29, 2022

'''
Pre-compute and save building level series for
- kw (sum)
- kvar (sum)
- kva (sum)
- amps per phase (sum)
- L-L voltage per phase (average)
- power factor (average)
- frequency (average)
- kva per phase using balanced voltage assumption (sum)
- outage proportion of series per timestep per building
'''

# 3rd-party imports
import os
import pandas as pd
import csv
import math

# global parameters
DIR_PATH = ''
DATA_DIR = 'C:/Users/enoch/Documents/GitHub/caltech-twin/digitaltwin/bms_csv_data/'  # subfolders for each meter, raw data here


# functions


def get_electric_meter_data(meter, measurement):
    '''
    Takes in directory of electric meter csv's and returns the measurement timeseries

    :param
    :return:
    '''

    fileNamesDirectory = os.listdir(DATA_DIR + meter)


    fileName = [file for file in fileNamesDirectory if measurement in file][0]
    with open(DATA_DIR + meter + '/' + fileName, 'r') as file:
        csv_reader = csv.reader(file)
        rows = list(csv_reader)

    t = []
    v = []
    outages = []
    for row in rows[1:]:
        t.append(row[0])

        if len(row[1]) == 0:
            v.append(None)
        else:
            v.append(float(row[1]))

        if row[2] in [4, 16, 20] or row[3] in [2, 3] or row[1] in [-1, None]:
            outages.append(0)
        else:
            outages.append(1)

    return t, v, outages


# main
if __name__ == '__main__':

    # load bms inventory
    bmsInventory = pd.read_csv('C:/Users/enoch/Documents/GitHub/caltech-twin/digitaltwin/bms_inventory.csv')

    # create new directory to store building-level timeseries

    perBuildingDir = 'C:/Users/enoch/Documents/GitHub/caltech-twin/digitaltwin/buildings_aggregated_better/'
    if not os.path.exists(perBuildingDir):
        os.makedirs(perBuildingDir)

    # get dictionary of meters per building and sort by type
    buildings = bmsInventory['Building String'].unique().tolist()  # sort on Building String (single line name)
    buildings = [i for i in buildings if i[:10] != 'substation']  # remove substations for now
    metersByBuilding = {}

    # loop through buildings
    for b in buildings:

        print('===Building', b, 'started===')

        buildingDf = bmsInventory.loc[bmsInventory['Building String'] == b]  # subset of the bms_inventory.csv corresponding to the building

        # 1. Get electric meters
        elecMeters = [i for i in buildingDf['Meter Name'] if i[:2] == 'EM']
        if len(elecMeters) == 0:
            print('===Building', b, 'has no electric meters===')
            continue

        # define lists to store aggregate values

        aggregateValues = {}
        aggregateTimestamps = {}
        aggregateNans = {}
        aggregateErrors = {}
        # loop through measurements in electric meters
        for meter in elecMeters:

            if meter in ['EM_21_AHU_B2_3', 'EM_79_CAC1', 'EM_79_CAC2', 'EM_79_CAC3', 'EM_79_CAC4', 'EM_79_CAC5', 'EM_79_CAC6']:  # TODO: fix this, some problem with timestamps
                print('======Meter', meter, 'skipped======')
                continue

            print('======Meter', meter, 'started======')

            elecMeasurements = [i for i in buildingDf.loc[buildingDf['Meter Name'] == meter]['Measurements Cleaned']][0] # measurements present
            elecMeasurements = elecMeasurements.strip("][").split(', ')
            elecMeasurements = [eval(i) for i in elecMeasurements]
            numSeries = len(elecMeasurements)

            for measurement in elecMeasurements:

                if measurement in ['kW', 'kVar', 'kVA', 'Frequency', 'PowerFactor', 'AmpsA', 'AmpsB', 'AmpsC', 'VoltsAB', 'VoltsBC', 'VoltsCA']:

                    # get data
                    timestamps, measurementSeries, outageSeries = get_electric_meter_data(meter=meter, measurement=measurement)
                    nans = [0 if i is None else 1 for i in measurementSeries]  # counts number of valid data points

                    # add to aggregate pointwise
                    key = measurement + '_sum'
                    try:
                        aggregateValues[key] = [i + 0 if new is None else new + i for new, i in zip(measurementSeries, aggregateValues[key])]
                        aggregateNans[key] = [i + new for new, i in zip(nans, aggregateNans[key])]
                    except:
                        aggregateValues[key] = measurementSeries
                        aggregateNans[key] = nans

                    # update aggregate outage count (# of 1s = # of valid datapoints)
                    try:
                        aggregateErrors[b] = [i + new for new, i in zip(outageSeries, aggregateErrors[b])]
                    except:
                        aggregateErrors[b] = outageSeries

                    # timestamps
                    key = measurement + '_timestamps'
                    if key in aggregateTimestamps.keys():
                        assert timestamps == aggregateTimestamps[key]
                    else:
                        aggregateTimestamps[key] = timestamps

                else:
                    continue
            print('======Meter', meter, 'complete======')

        # average the series that need to be averaged
        for measurement in ['Frequency', 'PowerFactor', 'VoltsAB', 'VoltsBC', 'VoltsCA']:
            newKey = measurement + '_ave'
            oldKey = measurement + '_sum'
            aggregateValues[newKey] = [i / n for i, n in zip(aggregateValues[oldKey], aggregateNans[oldKey])]
            del aggregateValues[oldKey]

        # divide outage count by total numbers of meters
        totalSeries = len(elecMeters) * len(elecMeasurements)
        aggregateErrors[b] = [i / totalSeries for i in aggregateErrors[b]]

        # compute kva per phase |kva| = AmpsA * VoltsAB / sqrt (3)
        # this is a reasonable approximation because the voltages are so well balanced in this data
        for ip, vp in zip(['A', 'B', 'C'], ['AB', 'BC', 'CA']):
            key = 'kva' + ip + '_sum'
            timestampKey = 'kva' + ip + '_timestamps'
            voltages = aggregateValues['Amps' + ip + '_sum']
            currents = aggregateValues['Volts' + vp + '_ave']
            aggregateValues[key] = [i * v / math.sqrt(3)for i, v in zip(currents, voltages)]
            aggregateTimestamps[timestampKey] = aggregateTimestamps['Amps' + ip + '_timestamps']

        # compute outages
        # TODO: search for outage flags across all measurements across all meters in a particular building. Return this as a percentage

        # write aggregate data to csvs for each building
        # create directory for the meter
        saveDir = perBuildingDir + b + '/'
        if not os.path.exists(saveDir):
            os.makedirs(saveDir)

     

        # write electric meter outage percentage
        saveFilename = saveDir + b + '_EM_outages.csv'
        with open(saveFilename, 'w') as out:
            csv_out = csv.writer(out)
            csv_out.writerow(['t', 'outage percent'])
            value = 0
            for t, v in zip(aggregateTimestamps[timestampKey], aggregateErrors[b]):  # use arbitary timestamp sequence
                value += v
                csv_out.writerow([t, value])

        print('===Building', b, 'complete===')

    print('---------Building-level calculations complete!---------')