
# 3rd-party imports
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import re
import ast
from datetime import datetime
import pandas as pd
import numpy as np
import os


### global params ###
URL_BASE = "https://192.168.10.104/"
QUERY_BASE = URL_BASE + "webChart/query/data/history"
username = "lwerner"
password = "Transformer2022"

def format_datetime(dt: datetime):
    '''Returns a datetime as it appears in the query URL.'''
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f-07:00")


def encode_query(url: str):
    '''Given a normally-written URL, converts special characters to their equivalent hex codes 
    as they appear in the query URL and returns the converted URL.'''
    code_book = [
        ("-", "$2d"),
        ("/", "$2f"),
        (".", "$2e"),
        (":", "$3a"),
        ("?", "$3f"),
        ("=", "$3d"),
        (";", "$3b"),
    ]
    for code in code_book:
        url = url.replace(code[0], code[1])
    return url


def generate_query_base(jace: str, meter: str):
    '''Generates a standard query URL.'''
    q = f":/{jace}/{meter}_"
    return QUERY_BASE + encode_query(q)

def generate_gas_query_base(jace: str):
    '''Generates a standard query URL for a gas meter.'''
    q = f":/{jace}/"
    return QUERY_BASE + encode_query(q)

def generate_query_measurement(measurement: str):
    '''Generates the component of the query URL denoting the desired measurement.'''
    q = f"{measurement}?"
    return encode_query(q)

def generate_query_time(start: datetime, end: datetime):
    '''Generates the component of the query URL indicating the start and end time for the timeseries
    to be requested.'''
    q = f"start={format_datetime(start)};end={format_datetime(end)}"
    return encode_query(q)


def parse_data(page_source):
    '''Converts a page into a dataframe.'''
    # strip <> headers from HTML and split on newline characters
    data = re.sub('<[^<]+?>', '', page_source).splitlines()

    # convert strings to dicts
    data = [ast.literal_eval(s) for s in data]
    for dict in data:
        if not('s' in dict.keys()):
            dict['s'] = 0
        if not('r' in dict.keys()):
            dict['r'] = 0

    # convert to dataframe
    df = pd.DataFrame(data)
    df = df.set_index('t')

    return df

def is_water_meter(meter):
    '''Checks whether a given meter name corresponds to a water meter.'''
    return meter[:3] == 'BTU' or meter[:4] == 'CHWM' or meter[:4] == 'HHWM' or 'Btu' in meter

def is_electric_meter(meter):
    '''Checks whether a given meter name corresponds to an electric meter.'''
    return meter[:2] == 'EM'

def is_pulse_meter(meter):
    '''Checks whether a given meter name corresponds to a Pulse Meter.'''
    return meter == 'Pulse'

def is_gas_meter(meter):
    '''Checks whether a given meter name corresponds to a gas meter.'''
    return ('gas' in meter)


if __name__ == '__main__':

    # Arrays of measurement types for the different meter types
    electricMeasurementNamesCA = ['kW', 'kVar', 'kVA','AmpsA','AmpsB','AmpsC','VoltsAB','VoltsBC','VoltsCA','Frequency','PowerFactor']
    electricMeasurementNamesAC = ['kW', 'kVar', 'kVA','AmpsA','AmpsB','AmpsC','VoltsAB','VoltsBC','VoltsAC','Frequency','PowerFactor']
    waterMeasurementNames = ['FlowRate', 'SupplyTemp', 'EnergyRate', 'ReturnTemp', 'TotalEnergy']
    pulseMeasurementNames = ['ResColdWtrUsed', 'ResHwUsed', 'NatGasUsed']
    gasMeasurementNames = ['MiscIO_3_2_CO2M_3_1', 'MiscIO_3_2_CO2M_3_1_Total', 'MiscIO_3_2_CO4_3_1', 'MiscIO_3_2_CO4_3_1_Total', 'MiscIO_3_2_O2M_3_1', 
                            'MiscIO_3_2_O2M_3_1_Total', 'MiscIO_3_2_NGES_3_North', 'MiscIO_3_3_CO2M_3_2', 'MiscIO_3_3_CO2M_3_2_Total', 'MiscIO_3_3_N2M_3_1', 'MiscIO_3_3_N2M_3_1_Total', 
                            'MiscIO_3_3_O2M_3_2', 'MiscIO_3_3_O2M_3_2_Total', 'MiscIO_3_3_NGES_3_East', 'MiscIO_2_4_CO4M_2_1', 'MiscIO_2_4_CO4M_2_1_Total', 'MiscIO_2_4_CO2M_2_1', 
                            'MiscIO_2_4_CO2M_2_1_Total', 'MiscIO_2_4_NGES_2_North', 'MiscIO_2_1_CO2M_2_2', 'MiscIO_2_1_CO2M_2_2_Total', 'MiscIO_2_1_CO4M_2_2', 
                            'MiscIO_2_1_CO4M_2_2_Total', 'MiscIO_2_1_N2M_2_1', 'MiscIO_2_1_N2M_2_1_Total', 'MiscIO_2_1_O2M_2_1', 'MiscIO_2_1_O2M_2_1_Total', 'MiscIO_2_1_NGES_2_East', 
                            'MiscIO_B1_3_CO2M_B1_2', 'MiscIO_B1_3_CO2M_B1_2_Total', 'MiscIO_B1_3_N2M_B1_1', 'MiscIO_B1_3_N2M_B1_1_Total', 'MiscIO_B1_3_NGES_B1_North', 
                            'MiscIO_B1_1_CO2M_B1_1', 'MiscIO_B1_1_CO2M_B1_1_Total', 'MiscIO_B1_1_CO2M_B1_1', 'MiscIO_B1_1_CO4M_B1_1_Total', 'MiscIO_B1_1_NGES_B1_East', 
                            'MEP_System_2B_N2M_B2_1', 'MEP_System_2B_N2M_B2_1_Total', 'MEP_System_2B_CO2M_B2_1', 'MEP_System_2B_CO2M_B2_1_Total']

    # Convert measurements as written above into dictionaries to speed up repeated query generation
    electricDictCA = {}
    for measurement in electricMeasurementNamesCA:
        electricDictCA[measurement] = generate_query_measurement(measurement=measurement)

    electricDictAC = {}
    for measurement in electricMeasurementNamesAC:
        electricDictAC[measurement] = generate_query_measurement(measurement=measurement)

    waterDict = {}
    for measurement in waterMeasurementNames:
        waterDict[measurement] = generate_query_measurement(measurement=measurement)

    pulseDict = {}
    for measurement in pulseMeasurementNames:
        pulseDict[measurement] = generate_query_measurement(measurement=measurement)

    gasDict = {}
    for measurement in gasMeasurementNames:
        gasDict[measurement] = generate_query_measurement(measurement=measurement)


    start_year = 2022
    start_month = 4
    start_day = 1
    end_year = 2022
    end_month = 6
    end_day = 1


    ### Initialize Driver ###
    print('===========Initialize Driver===========')
    driverLoc = 'C:/Users/enoch/Downloads/chromedriver.exe'  # chrome driver same version as installed, CHANGE TO YOUR OWN DIRECTORY
    data = pd.read_csv('C:/Users/enoch/Documents/GitHub/caltech-twin/digitaltwin/bms_inventory.csv')  # CHANGE TO YOUR OWN DIRECTORY
    download_directory_root = 'C:/Users/enoch/Documents/GitHub/caltech-twin/digitaltwin/bms_csv_data/'  # CHANGE TO YOUR OWN DIRECTORY
    download_raw_directory_extension = 'raw_data/'  # CHANGE TO YOUR OWN DIRECTORY 
    download_cleaned_directory_extension = 'cleaned_data/'  # CHANGE TO YOUR OWN DIRECTORY 
    s = Service(driverLoc)
    options = webdriver.ChromeOptions()
    options.add_argument('ignore-certificate-errors')  # certificate throws error
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=s, options=options)

    ### Login ###
    print('===========Logging In===========')

    # pre-login page
    driver.get(URL_BASE)
    driver.find_element(By.NAME, value='j_username').send_keys(username)
    driver.find_element(By.ID, value='login-submit').click()

    # login page
    driver.find_element(By.NAME, value='j_password').send_keys(password)
    driver.find_element(By.ID, value='login-submit').click()
    time.sleep(1)  #TODO: implement selenium Wait function here instead

    ### start getting data ###
    print('===========Downloading Data===========')

    # Looping through all meters

    q3 = generate_query_time(
            start=datetime(start_year, start_month, start_day),
            end=datetime(end_year, end_month, end_day)
        )
    
    url_fails = []
    url_successes = []
    check = False

    for index, row in data.iterrows():
        meter = row['Meter Name']
        jace = row['Jace']
        save_raw_filepath = download_directory_root + download_raw_directory_extension + meter
        save_cleaned_filepath = download_directory_root + download_cleaned_directory_extension + meter
        q1 = row['Query Base']

        if (not os.path.exists(save_raw_filepath)) and meter != 'skip':
            os.makedirs(save_raw_filepath)

        if (not os.path.exists(save_cleaned_filepath)) and meter != 'skip':
            os.makedirs(save_cleaned_filepath)

        if meter == 'skip':
            url_fails.append('skipped')
            url_successes.append('skipped')
            pass

        elif is_electric_meter(meter):
            fails = []
            successes = []
            electricMeasurementNames = electricMeasurementNamesAC
            electricDict = electricDictAC
            if 'VoltsCA' in row['Measurements']:
                electricMeasurementNames = electricMeasurementNamesCA
                electricDict = electricDictCA
            for measurement in electricMeasurementNames:
                if (meter == 'EM_21_AHU_B2_3') and (measurement in ['kVar', 'kVA', 'VoltsAB', 'VoltsBC', 'VoltsCA', 'VoltsAC', 'Frequency', 'PowerFactor']):
                    continue
                q1 = row['Query Base']
                q2 = electricDict[measurement]
                query = q1 + q2 + q3
                try:
                    driver.get(query)
                    df = parse_data(driver.page_source)
                    measurement_filename = measurement
                    if measurement == 'VoltsAC':
                        measurement_filename = 'VoltsCA'
                    raw_filename = download_directory_root + download_raw_directory_extension + meter + '/' + jace + '_' + meter + '_' + measurement_filename + '.csv'
                    cleaned_filename = download_directory_root + download_cleaned_directory_extension + meter + '/' + jace + '_' + meter + '_' + measurement_filename + '.csv'
                    if os.path.exists(raw_filename):
                        existing_df = pd.read_csv(raw_filename)
                        df = existing_df.merge(df,on='t',how='outer',suffixes=('_x','')).assign(v = lambda x: x['v'].fillna(x['v_x']), r = lambda x: x['r'].fillna(x['r_x']), s = lambda x: x['s'].fillna(x['s_x']))[existing_df.columns] #append new data
                        os.remove(raw_filename)
                        df = df.set_index('t')
                    df.to_csv(raw_filename, index = True)
                    if os.path.exists(cleaned_filename):
                        existing_df = pd.read_csv(cleaned_filename)
                        df = existing_df.merge(df,on='t',how='outer',suffixes=('_x','')).assign(v = lambda x: x['v'].fillna(x['v_x']), r = lambda x: x['r'].fillna(x['r_x']), s = lambda x: x['s'].fillna(x['s_x']))[existing_df.columns] #append new data
                        os.remove(cleaned_filename)
                        df = df.set_index('t')
                    df.to_csv(cleaned_filename, index = True)
                    successes.append(measurement)
                except:
                    fails.append(measurement)
                    print('measurement', measurement, 'failed!')   
            url_successes.append(successes)
            url_fails.append(fails)

        elif is_water_meter(meter):
            fails = []
            successes = []
            for measurement in waterMeasurementNames:
                q1 = row['Query Base']
                if (meter == 'CHWM_B1_1' or meter == 'HHWM_B1_1') and measurement == 'FlowRate':
                    measurement = 'VolumeRate'
                    q2 = generate_query_measurement(measurement='VolumeRate')
                else:
                    q2 = waterDict[measurement]  
                query = q1 + q2 + q3
                try:
                    driver.get(query)
                    df = parse_data(driver.page_source)
                    raw_filename = download_directory_root + download_raw_directory_extension + meter + '/' + jace + '_' + meter + '_' + measurement + '.csv'
                    cleaned_filename = download_directory_root + download_cleaned_directory_extension + meter + '/' + jace + '_' + meter + '_' + measurement + '.csv'
                    if os.path.exists(raw_filename):
                        existing_df = pd.read_csv(raw_filename)
                        df = existing_df.merge(df,on='t',how='outer',suffixes=('_x','')).assign(v = lambda x: x['v'].fillna(x['v_x']), r = lambda x: x['r'].fillna(x['r_x']), s = lambda x: x['s'].fillna(x['s_x']))[existing_df.columns] #append new data
                        os.remove(raw_filename)
                        df = df.set_index('t')
                    df.to_csv(raw_filename, index = True)
                    if os.path.exists(cleaned_filename):
                        existing_df = pd.read_csv(cleaned_filename)
                        df = existing_df.merge(df,on='t',how='outer',suffixes=('_x','')).assign(v = lambda x: x['v'].fillna(x['v_x']), r = lambda x: x['r'].fillna(x['r_x']), s = lambda x: x['s'].fillna(x['s_x']))[existing_df.columns] #append new data
                        os.remove(cleaned_filename)
                        df = df.set_index('t')
                    df.to_csv(cleaned_filename, index = True)
                    successes.append(measurement)
                except:
                    fails.append(measurement)
                    print('measurement', measurement, 'failed!')
            url_successes.append(successes)
            url_fails.append(fails)

        elif is_pulse_meter(meter):
            fails = []
            successes = []
            for measurement in pulseMeasurementNames:
                query = 'https://192.168.10.104/webChart/query/data/history$3a$2fBT14_2$2f' + pulseDict[measurement] + q3
                try:
                    driver.get(query)
                    df = parse_data(driver.page_source)
                    raw_filename = download_directory_root + download_raw_directory_extension + meter + '/' + jace + '_' + meter + '_' + measurement + '.csv'
                    cleaned_filename = download_directory_root + download_cleaned_directory_extension + meter + '/' + jace + '_' + meter + '_' + measurement + '.csv'
                    if os.path.exists(raw_filename):
                        existing_df = pd.read_csv(raw_filename)
                        df = existing_df.merge(df,on='t',how='outer',suffixes=('_x','')).assign(v = lambda x: x['v'].fillna(x['v_x']), r = lambda x: x['r'].fillna(x['r_x']), s = lambda x: x['s'].fillna(x['s_x']))[existing_df.columns] #append new data
                        os.remove(raw_filename)
                        df = df.set_index('t')
                    df.to_csv(raw_filename, index = True)
                    if os.path.exists(cleaned_filename):
                        existing_df = pd.read_csv(cleaned_filename)
                        df = existing_df.merge(df,on='t',how='outer',suffixes=('_x','')).assign(v = lambda x: x['v'].fillna(x['v_x']), r = lambda x: x['r'].fillna(x['r_x']), s = lambda x: x['s'].fillna(x['s_x']))[existing_df.columns] #append new data
                        os.remove(cleaned_filename)
                        df = df.set_index('t')
                    df.to_csv(cleaned_filename, index = True)
                    successes.append(measurement)
                except:
                    fails.append(measurement)
                    print('measurement', measurement, 'failed!')
            url_successes.append(successes)
            url_fails.append(fails)

        elif is_gas_meter(meter):
            fails = []
            successes = []
            for measurement in gasMeasurementNames:
                q1 = row['Query Base']
                q2 = gasDict[measurement]
                query = q1 + q2 + q3
                try:
                    driver.get(query)
                    df = parse_data(driver.page_source)
                    raw_filename = download_directory_root + download_raw_directory_extension + meter + '/' + jace + '_' + meter + '_' + measurement + '.csv'
                    cleaned_filename = download_directory_root + download_cleaned_directory_extension + meter + '/' + jace + '_' + meter + '_' + measurement + '.csv'
                    if os.path.exists(raw_filename):
                        existing_df = pd.read_csv(raw_filename)
                        df = existing_df.merge(df,on='t',how='outer',suffixes=('_x','')).assign(v = lambda x: x['v'].fillna(x['v_x']), r = lambda x: x['r'].fillna(x['r_x']), s = lambda x: x['s'].fillna(x['s_x']))[existing_df.columns] #append new data
                        os.remove(raw_filename)
                        df = df.set_index('t')
                    df.to_csv(raw_filename, index = True)
                    if os.path.exists(cleaned_filename):
                        existing_df = pd.read_csv(cleaned_filename)
                        df = existing_df.merge(df,on='t',how='outer',suffixes=('_x','')).assign(v = lambda x: x['v'].fillna(x['v_x']), r = lambda x: x['r'].fillna(x['r_x']), s = lambda x: x['s'].fillna(x['s_x']))[existing_df.columns] #append new data
                        os.remove(cleaned_filename)
                        df = df.set_index('t')
                    df.to_csv(cleaned_filename, index = True)
                    successes.append(measurement)
                except:
                    fails.append(measurement)
                    print('measurement', measurement, 'failed!')
            url_successes.append(successes)
            url_fails.append(fails)

        else:
            pass
    
#    data['fails'] = url_fails
#    data['successes'] = url_successes
#    data.to_csv(download_directory_root + 'bms_inventory_fails_kaushik.csv')