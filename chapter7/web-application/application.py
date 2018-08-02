#!/usr/bin/env python
from flask import Flask, render_template, flash, request, jsonify, Markup
import logging, io, base64, os, datetime, sys
import pandas as pd
import numpy as np
from datetime import timedelta
from sklearn.naive_bayes import GaussianNB
import requests
import urllib.parse

# Global variables
golf_df = None
naive_bayes = None

# EB looks for an 'application' callable by default.
application = Flask(__name__)


def BuildGolfDataSet():
    golf_data_header = ['Outlook', 'Temperature_Numeric', 'Temperature_Nominal', 'Humidity_Numeric', 'Humidity_Nominal', 'Windy', 'Play']

    golf_data_set = [['overcast',83,'hot',86,'high',False,True],
    ['overcast',64,'cool',65,'normal',True,True],
    ['overcast',72,'mild',90,'high',True,True],
    ['overcast',81,'hot',75,'normal',False,True],
    ['rainy',70,'mild',96,'high',False,True],
    ['rainy',68,'cool',80,'normal',False,True],
    ['rainy',65,'cool',70,'normal',True,False],
    ['rainy',75,'mild',80,'normal',False,True],
    ['rainy',71,'mild',91,'high',True,False],
    ['sunny',85,'hot',85,'high',False,False],
    ['sunny',80,'hot',90,'high',True,False],
    ['sunny',72,'mild',95,'high',False,False],
    ['sunny',69,'cool',70,'normal',False,True],
    ['sunny',75,'mild',70,'normal',True,True]]

    golf_df = pd.DataFrame(golf_data_set, columns=golf_data_header)

    # convert  bool to ints
    golf_df[['Windy','Play']] = golf_df[['Windy','Play']].astype(int)

    return golf_df

def PrepareDataForModel(raw_dataframe, target_columns, drop_first = False, make_na_col = False):
    # dummy all categorical fields 
    dataframe_dummy = pd.get_dummies(raw_dataframe, columns=target_columns, 
                                     drop_first=drop_first, 
                                     dummy_na=make_na_col)
    return (dataframe_dummy)


def GetWeatherOutlookAndWeatherIcon(main_weather_icon):
    # truncate third char - day or night not needed
    main_weather_icon_tail = main_weather_icon[2:] + ".png"
    main_weather_icon = main_weather_icon[0:2]
    
    # return "Golf|Weather Data" variable and daytime icon
    if (main_weather_icon in ["01", "02"]):
        return("sunny", main_weather_icon + main_weather_icon_tail)
    elif (main_weather_icon in ["03", "04", "50"]):
        return("overcast", main_weather_icon + main_weather_icon_tail)
    else:
        return("rain", main_weather_icon + main_weather_icon_tail)
     

def GetNominalTemparature(temp_fahrenheit):
    if (temp_fahrenheit < 70):
        return "cool"
    elif (temp_fahrenheit < 80):
        return "mild"
    else:
        return "hot"


def GetNominalHumidity(humidity_percent):
     if (humidity_percent > 80):
        return "high"
     else:
        return "normal"


def GetWindyBoolean(wind_meter_second):
    if (wind_meter_second > 10.8):
        return(True)
    else:
        return(False)


@application.before_first_request
def startup():
    global golf_df, naive_bayes

    # prepare golf data set
    golf_df = BuildGolfDataSet()

    # create dummy features 
    golf_df_ready = PrepareDataForModel(golf_df, target_columns=['Outlook', 'Temperature_Nominal', 'Humidity_Nominal'])
    golf_df_ready = golf_df_ready.dropna() 

    # build feature set
    features = [feat for feat in list(golf_df_ready) if feat != 'Play']

    # run bayesian model 
    naive_bayes = GaussianNB()
    naive_bayes.fit(golf_df_ready[features], np.ravel(golf_df_ready[['Play']]))
 

@application.route("/", methods=['POST', 'GET'])
def PlayGolf():
    prediction_proba = 0.5
    prediction_actual = 0
    outlook = 'None'
    iswindy = False
    humidity = 50
    humidity_nominal = ''
    temperature = 70
    temperature_nominal = ''
    selected_location = ''
    selected_location_raw = ''
    selected_time = 0
    selected_time_bracket = ""
    outlook_icon=''
    time_stamp_date = ''
    message = ''

    if request.method == 'POST':
        selected_location = request.form['selected_location']
        selected_time = request.form['selected_time']
        
        selected_location_raw = selected_location
        # make sure text input is URL friendly
        selected_location = urllib.parse.quote_plus(selected_location)
        message = "Sorry, I cannot find that location..."

        # <<YOUR_API_KEY>> Update line with your OpenWeatherMap API key <<YOUR_API_KEY>>
        openweathermap_url = "http://api.openweathermap.org/data/2.5/forecast?q=" + selected_location + "&mode=json&APPID=<<YOUR_API_KEY>>"
        
        weather_json = []
        try:
            weather_json = requests.get(openweathermap_url).json() 
        except:  
            # couldn't find location
            e = sys.exc_info()[0]
            
 
        if (len(weather_json) > 3):
            message = ''

            # finding the right times - locate first 6AM instance
            time_stamp_start = 0
            len(weather_json['list'])
            for forc in range(len(weather_json['list'])):
                time_stamp = weather_json['list'][forc]['dt_txt']
                if time_stamp.split()[1] == "06:00:00":
                    time_stamp_start = forc 
                    time_stamp_date = time_stamp.split()[0] 
                    break;

            # find desired golfing time forecast
            #  6-9 AM = time_stamp_start
            #  9-12 PM = time_stamp_start + 1
            #  12-3 PM = time_stamp_start + 2
            #  3-6 PM = time_stamp_start + 3
            #  6-9 PM = time_stamp_start + 4
            #  9-12 AM = time_stamp_start + 5

            golf_time = time_stamp_start + 5
            selected_time_bracket = "9PM-12AM"
            if (selected_time == "6"):
                # 6 AM 
                golf_time = time_stamp_start
                selected_time_bracket = "6AM-9AM"
            elif (selected_time == "9"):
                # 9 AM 
                golf_time = time_stamp_start + 1
                selected_time_bracket = "9AM-12PM"
            elif (selected_time == "12"):
                # 12 PM  
                golf_time = time_stamp_start + 2
                selected_time_bracket = "12PM-3PM"
            elif (selected_time == "15"):
                # 15 PM 
                golf_time = time_stamp_start + 3
                selected_time_bracket = "3PM-6PM"
            elif (selected_time == "18"):
                # 18 PM 
                golf_time = time_stamp_start + 4
                selected_time_bracket = "6PM-9PM"

            forecast_data = weather_json['list'][golf_time]    

            # humidity
            humidity = forecast_data['main']['humidity']
            humidity_nominal = GetNominalHumidity(humidity)
            
            # temperature - to Fahrenheit and to nominal 
            temperature = np.round(float(forecast_data['main']['temp']) * 1.8 - 459.67,2)
            temperature_nominal = GetNominalTemparature(temperature)

            # weather icon
            outlook, outlook_icon = GetWeatherOutlookAndWeatherIcon(forecast_data['weather'][0]['icon'])
            
            # wind speed 
            iswindy = GetWindyBoolean(forecast_data['wind']['speed'])

            # pass data to bayesian model
            Temperature_Numeric = temperature
            Humidity_Numeric = humidity
            Windy = int(iswindy)
            Outlook_overcast = int(outlook=="overcast")
            Outlook_rainy = int(outlook=="rainy")
            Outlook_sunny = int(outlook=="sunny")

            Temperature_Nominal_cool = int(temperature_nominal=="cool")
            Temperature_Nominal_hot = int(temperature_nominal=="hot")
            Temperature_Nominal_mild = int(temperature_nominal=="mild")
            Humidity_Nominal_high = int(humidity_nominal=="high")
            Humidity_Nominal_normal = int(humidity_nominal=="normal")

             
            future_data = pd.DataFrame([[Temperature_Numeric,
             Humidity_Numeric,
             Windy,
             Outlook_overcast,
             Outlook_rainy,
             Outlook_sunny,
             Temperature_Nominal_cool,
             Temperature_Nominal_hot,
             Temperature_Nominal_mild,
             Humidity_Nominal_high,
             Humidity_Nominal_normal]])

            prediction_proba = naive_bayes.predict_proba(future_data)
            prediction_proba = np.round(prediction_proba[0][1] * 100,2)
            prediction_actual = naive_bayes.predict(future_data)
       

    # set default passenger settings
    return render_template('index.html',
        prediction_proba = prediction_proba,
        prediction_actual = prediction_actual,
        outlook = outlook.capitalize(),
        iswindy = iswindy,
        humidity = humidity,
        humidity_nominal = humidity_nominal.capitalize(),
        temperature = temperature,
        temperature_nominal = temperature_nominal.capitalize(),
        selected_location_raw = selected_location_raw.capitalize(),
        selected_time = selected_time,
        selected_time_bracket = selected_time_bracket,
        outlook_icon=outlook_icon,
        time_stamp_date = time_stamp_date,
        message = message)



if __name__=='__main__':
    application.run(debug=True)


