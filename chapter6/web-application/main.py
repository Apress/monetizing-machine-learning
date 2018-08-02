#!/usr/bin/env python
from flask import Flask, render_template, flash, request
import logging, io, base64, os, datetime
from datetime import timedelta

# global variables
crime_horizon_df = None
src = 'D:\home\site\wwwroot\static\sf-crime-horizon.csv'

app = Flask(__name__)

def LoadCrimeHorizon():
    from numpy import genfromtxt
    crime_horizon_df = genfromtxt(src, delimiter=',', names = True, dtype = None,)
    return crime_horizon_df


def GetCrimeEstimates(horizon_date, horizon_time_segment):
    Day_of_month = int(horizon_date.split('/')[1])
    Month_of_year = int(horizon_date.split('/')[0])
    Day_Segment = int(horizon_time_segment) # 0,1,2
    crime_horizon_df_tmp = crime_horizon_df[(crime_horizon_df['Day_of_month'] == Day_of_month) & 
                                            (crime_horizon_df['Month_of_year']==Month_of_year) &
                                            (crime_horizon_df['Day_Segment'] == Day_Segment)]


    
    # build latlng string for google maps
    LatLngString = ''
    for lat, lon in zip(crime_horizon_df_tmp['Latitude'], crime_horizon_df_tmp['Longitude']): 
        LatLngString += "new google.maps.LatLng(" + str(lat) + "," + str(lon) + "),"
     
    return (LatLngString)


@app.before_first_request
def startup():
    global crime_horizon_df

     # prepare crime data
    crime_horizon_df = LoadCrimeHorizon()


@app.route("/", methods=['POST', 'GET'])
def build_page():
        if request.method == 'POST':

            horizon_date_int = int(request.form.get('slider_crime_horizon'))
            # offering 3 months horizon over 270 points - 3 per day to account for time segments
            date_int = int(horizon_date_int / 3)
            time_segment_int = int(horizon_date_int % 3)

            if (time_segment_int == 0):
                image_source = 'static/images/morning.jpg'
            elif (time_segment_int == 1):
                image_source = 'static/images/afternoon.jpg'
            else:
                image_source = 'static/images/night.jpg'


            date_horizon = datetime.datetime.today() + timedelta(days=date_int)

            return render_template('index.html',
                date_horizon = date_horizon.strftime('%m/%d/%Y'),
                time_segment_int = time_segment_int, 
                crime_horizon = GetCrimeEstimates(date_horizon.strftime('%m/%d/%Y'), time_segment_int),
                current_value=horizon_date_int,
                image_source=image_source)
 
        else:
            # set default passenger settings
            return render_template('index.html',
                date_horizon = datetime.datetime.today().strftime('%m/%d/%Y'),
                time_segment_int = 0, 
                crime_horizon = '',
                current_value=0,
                image_source='static/images/morning.jpg')

 

if __name__=='__main__':
    # when running on local machine override with local directory path
    src = 'static//sf-crime-horizon.csv'
    app.run(debug=True)


