# Copyright placeholder
# Author: Lucien Werner
# Date: July 27, 2022

'''
Calculates voltage, current, and power imbalances at all electrical meters in bms_inventory.csv

Definitions for voltage unbalance from here: https://ieeexplore.ieee.org/document/4402352
Current and power unbalanaces computed using the phase unbalance rating concept

We create a new directory in the same parent directory as dataDir with subfolders for each electrical meter
For each electrical meter, we create timeseries of unbalances for voltage, current, and power

Note: we only have line-line voltages in the data. This limits the definitions we can use.

'''

# 3rd-party imports
import os
import pandas as pd
import csv
import math

# global parameters
DIR_PATH = ''
DATA_DIR = 'C:/Users/enoch/Documents/GitHub/caltech-twin/digitaltwin/bms_csv_data/cleaned_data/'  # subfolders for each meter, raw data here

# functions
def voltage_unbalance_nema(vAB, vBC, vCA):
    '''
    Computes the voltage imbalance using the NEMA defintion
    The unit is %-LVUR (line voltage unbalance rating)
    :param vAB: float
    :param vBC: float
    :param vCA: float
    :return:
    '''

    vAve = (vAB + vBC + vCA) / 3

    if vAve == 0:
        return 0

    maxDiff = max(abs(vAB - vAve), abs(vBC - vAve), abs(vCA - vAve))

    return maxDiff * 100 / vAve

def current_unbalance(ampsA, ampsB, ampsC):
    '''
    Calculates the current unbalance using the same principle as the %-PVUR IEEE voltage definition
    :param ampsA:
    :param ampsB:
    :param ampsC:
    :return:
    '''

    cAve = (ampsA + ampsB + ampsC) / 3

    if cAve == 0:
        return 0

    maxDiff = max(abs(ampsA - cAve), abs(ampsB - cAve), abs(ampsC - cAve))

    return maxDiff * 100 / cAve

def power_unbalance(kvaA, kvaB, kvaC):
    '''
    Calculates the complex power unbalance using the same principle as the %-PVUR IEEE voltage definition
    :param vaA: tuple (vAB, ampsA)
    :param vaB: tuple (vBC, ampsB)
    :param vaC: tuple (vCA, ampsC)
    :return:
    '''

    # multiply current and voltage magnitudes to get complex power magnitude
    kvaA = kvaA[0] * kvaA[1]
    kvaB = kvaB[0] * kvaB[1]
    kvaC = kvaC[0] * kvaC[1]

    pAve = (kvaA + kvaB + kvaC) / 3

    if pAve == 0:
        return 0

    maxDiff = max(abs(kvaA - pAve), abs(kvaB - pAve), abs(kvaC - pAve))

    return maxDiff * 100 / pAve

def get_meter_data(meterName):
    '''
    Takes in directory of meter csv's and returns three timeseries for voltages and three timeseries for currents

    :param meterDir:
    :return:
    '''

    fileNamesDirectory = os.listdir(DATA_DIR + meterName)

    # voltages
    voltageSuffixes = ['AB', 'BC', 'CA']
    voltageTimeseries = ([], [], [])
    timestamps = []
    for suffix in voltageSuffixes:
        # form file path name
        fileName = [file for file in fileNamesDirectory if file[-11:] == 'Volts' + suffix + '.csv'][0]

        with open(DATA_DIR + meterName + '/' + fileName, 'r') as file:
            csv_reader = csv.reader(file)
            rows = list(csv_reader)

        headerRow = rows[0]
        for row in rows[1:]:
            if suffix == 'AB':
                timestamps.append(row[0])
                voltageTimeseries[0].append(row[1])
            elif suffix == 'BC':
                voltageTimeseries[1].append(row[1])
            elif suffix == 'CA':
                voltageTimeseries[2].append(row[1])
            else:
                raise ValueError

    currentSuffixes = ['A', 'B', 'C']
    currentTimeseries = ([], [], [])
    for suffix in currentSuffixes:
        # form file path name
        fileName = [file for file in fileNamesDirectory if file[-9:] == 'Amps' + suffix + '.csv'][0]

        with open(DATA_DIR + meterName + '/' + fileName, 'r') as file:
            csv_reader = csv.reader(file)
            rows = list(csv_reader)

        headerRow = rows[0]
        for row in rows[1:]:
            if suffix == 'A':
                currentTimeseries[0].append(row[1])
            elif suffix == 'B':
                currentTimeseries[1].append(row[1])
            elif suffix == 'C':
                currentTimeseries[2].append(row[1])
            else:
                raise ValueError

    return timestamps, voltageTimeseries, currentTimeseries  # [timestamps], ([voltsAB], [voltsBC], [voltsCA]), ([AmpsA], [AmpsB], [AmpsC])


# main
if __name__ == '__main__':

    # load bms inventory
    bmsInventory = pd.read_csv('C:/Users/enoch/Documents/GitHub/caltech-twin/digitaltwin/bms_inventory.csv')

    # create new directory to store unbalance timeseries
    unbalanceDir = 'C:/Users/enoch/Documents/GitHub/caltech-twin/digitaltwin/unbalances/'
    if not os.path.exists(unbalanceDir):
        os.makedirs(unbalanceDir)


    # loop through meters
    for row in bmsInventory.iterrows():

        # define meter name
        meterName = row[1][8]

        if meterName[:2] == 'EM':
            pass
            print('Starting meter', meterName)
        else:
            continue

        # get data for the meter
        try:
            timestamps, voltages, currents = get_meter_data(meterName)
        except:
            print(meterName, 'failed!')
            continue

        # check lists have same length
        assert len(timestamps) == len(voltages[0]) and len(voltages[0]) == len(voltages[1]) and len(voltages[1]) == len(voltages[2])
        assert len(timestamps) == len(currents[0]) and len(currents[0]) == len(currents[1]) and len(currents[1]) == len(currents[2])

        # loop through lists and compute unbalances pointwise
        voltageUnbalance = []
        currentUnbalance = []
        powerUnbalance = []
        powerPhases = []  # list of 3-tuples

        for idx, t in enumerate(timestamps):

            # get data for timestamp t
            voltsAB = float(voltages[0][idx])
            voltsBC = float(voltages[1][idx])
            voltsCA = float(voltages[2][idx])
            ampsA = float(currents[0][idx])
            ampsB = float(currents[1][idx])
            ampsC = float(currents[2][idx])

            vu = voltage_unbalance_nema(voltsAB, voltsBC, voltsCA)
            voltageUnbalance.append((t, vu))

            cu = current_unbalance(ampsA, ampsB, ampsC)
            currentUnbalance.append((t, cu))

            pu = power_unbalance((voltsAB, ampsA), (voltsBC, ampsB), (voltsCA, ampsC))
            powerUnbalance.append((t, pu))

            # division by sqrt(3) appropriate due the balanced voltages
            pp = (voltsAB * ampsA / math.sqrt(3), voltsBC * ampsB / math.sqrt(3), voltsCA * ampsC / math.sqrt(3))
            powerPhases.append((t,) + pp)

        # create directory for the meter
        saveDir = unbalanceDir + meterName + '/'
        if not os.path.exists(saveDir):
            os.makedirs(saveDir)

        # save voltage
        with open(saveDir + meterName + '_voltageUnbalance.csv', 'w') as out:
            csv_out = csv.writer(out)
            csv_out.writerow(['t', 'vu'])
            for r in voltageUnbalance:
                csv_out.writerow(r)

        # save current
        with open(saveDir + meterName + '_currentUnbalance.csv', 'w') as out:
            csv_out = csv.writer(out)
            csv_out.writerow(['t', 'cu'])
            for r in currentUnbalance:
                csv_out.writerow(r)

        # save power
        with open(saveDir + meterName + '_powerUnbalance.csv', 'w') as out:
            csv_out = csv.writer(out)
            csv_out.writerow(['t', 'pu'])
            for r in powerUnbalance:
                csv_out.writerow(r)

        # save phase powers
        with open(saveDir + meterName + '_powerPhases.csv', 'w') as out:
            csv_out = csv.writer(out)
            csv_out.writerow(['t', 'kvaA', 'kvaB', 'kvaC'])
            for r in powerPhases:
                csv_out.writerow(r)


    print('---------Unbalances completes!---------')