#!/usr/bin/env python
from flask import Flask, render_template, flash, request, jsonify, Markup
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io, base64, os
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
 

# default traveler constants
DEFAULT_EMBARKED = 'Southampton'
DEFAULT_FARE = 33
DEFAULT_AGE = 30
DEFAULT_GENDER = 'Female'
DEFAULT_TITLE = 'Mrs.'
DEFAULT_CLASS = 'Second'
DEFAULT_CABIN = 'C'
DEFAULT_SIBSP = 0
DEFAULT_PARCH = 0

# initializing constant vars
average_survival_rate = 0
# logistic regression modeling
lr_model = LogisticRegression()

app = Flask(__name__)


@app.before_first_request
def startup():
    global average_survival_rate, lr_model 

    from numpy import genfromtxt
    titanic_array = genfromtxt('titanic3.csv', delimiter=',')
    average_survival_rate = (np.mean([item[0] for item in titanic_array]) * 100)

    X_train, X_test, y_train, y_test = train_test_split([item[1:] for item in titanic_array], 
                                                 [item[0] for item in titanic_array], test_size=0.5, random_state=42)


    # fit model only once
    lr_model.fit(X_train, y_train)

@app.route("/", methods=['POST', 'GET'])
def submit_new_profile():
    model_results = ''
    if request.method == 'POST':
        selected_embarked = request.form['selected_embarked']
        selected_fare = request.form['selected_fare']
        selected_age = request.form['selected_age']
        selected_gender = request.form['selected_gender']
        selected_title = request.form['selected_title']
        selected_class = request.form['selected_class']
        selected_cabin = request.form['selected_cabin']
        selected_sibsp = request.form['selected_sibsp']
        selected_parch = request.form['selected_parch']

        # assign new variables to live data for prediction
        age = int(selected_age)
        isfemale = 1 if selected_gender == 'Female' else 0
        sibsp = int(selected_sibsp)
        parch = int(selected_parch)
        fare = int(selected_fare)
        
        # point of embarcation
        embarked_Q = 1
        embarked_S = 0
        embarked_Unknown = 0 
        embarked_nan = 0
        if (selected_embarked[0]=='Q'):
            embarked_Q = 1
        if (selected_embarked[0]=='S'):
            embarked_S = 1

        # class
        pclass_Second = 0
        pclass_Third = 0
        pclass_nan = 0
        if (selected_class=='Second'):
            pclass_Second = 0
        if (selected_class=='Third'):
            pclass_Third = 0

        # title
        title_Master = 0
        title_Miss = 0
        title_Mr = 0
        title_Mrs = 0
        title_Rev = 0
        title_Unknown = 0
        title_nan = 0
        if (selected_title=='Master.'):
            title_Master = 1
        if (selected_title=='Miss.'):
            title_Miss = 1
        if (selected_title=='Mr.'):
            title_Mr = 1
        if (selected_title=='Mrs.'):
            title_Mrs = 1
        if (selected_title=='Rev.'):
            title_Master = 1
        if (selected_title=='Unknown'):
            title_Unknown = 1
 
        # cabin
        cabin_B = 0
        cabin_C = 0  
        cabin_D = 0  
        cabin_E = 0
        cabin_F = 0
        cabin_G = 0
        cabin_T = 0
        cabin_Unknown = 0
        cabin_nan = 0
        if (selected_cabin=='B'):
            cabin_B = 1
        if (selected_cabin=='C'):
            cabin_C = 1
        if (selected_cabin=='D'):
            cabin_D = 1
        if (selected_cabin=='E'):
            cabin_E = 1
        if (selected_cabin=='F'):
            cabin_F = 1
        if (selected_cabin=='G'):
            cabin_G = 1
        if (selected_cabin=='T'):
            cabin_T = 1
        if (selected_cabin=='Unknown'):
            cabin_Unknown = 1
 
        # build new array to be in same format as modeled data so we can feed it right into the predictor
        user_designed_passenger = [[age, sibsp, parch, fare, isfemale, pclass_Second, pclass_Third, pclass_nan, cabin_B, cabin_C, cabin_D, cabin_E, cabin_F, cabin_G, cabin_T, cabin_Unknown, cabin_nan, embarked_Q, embarked_S, embarked_Unknown, embarked_nan, title_Master, title_Miss, title_Mr, title_Mrs, title_Rev, title_Unknown, title_nan]]
 

        # add user desinged passenger to predict function
        Y_pred = lr_model.predict_proba(user_designed_passenger)
        probability_of_surviving_fictional_character = Y_pred[0][1] * 100

        fig = plt.figure()
        objects = ('Average Survival Rate', 'Fictional Traveler')
        y_pos = np.arange(len(objects))
        performance = [average_survival_rate, probability_of_surviving_fictional_character]

        ax = fig.add_subplot(111)
        colors = ['gray', 'blue']
        plt.bar(y_pos, performance, align='center', color = colors, alpha=0.5)
        plt.xticks(y_pos, objects)
        plt.axhline(average_survival_rate, color="r")
        plt.ylim([0,100])
        plt.ylabel('Survival Probability')
        plt.title('How Did Your Fictional Traveler Do? \n ' + str(round(probability_of_surviving_fictional_character,2)) + '% of Surviving!')
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()

        return render_template('index.html',
            model_results = model_results,
            model_plot = Markup('<img src="data:image/png;base64,{}">'.format(plot_url)),
            selected_embarked = selected_embarked,
            selected_fare = selected_fare,
            selected_age = selected_age,
            selected_gender = selected_gender,
            selected_title = selected_title,
            selected_class = selected_class,
            selected_cabin = selected_cabin,
            selected_sibsp = selected_sibsp,
            selected_parch = selected_parch)
    else:
        # set default passenger settings
        return render_template('index.html',
            model_results = '',
            model_plot = '',
            selected_embarked = DEFAULT_EMBARKED,
            selected_fare = DEFAULT_FARE,
            selected_age = DEFAULT_AGE,
            selected_gender = DEFAULT_GENDER,
            selected_title = DEFAULT_TITLE,
            selected_class = DEFAULT_CLASS,
            selected_cabin = DEFAULT_CABIN,
            selected_sibsp = DEFAULT_SIBSP,
            selected_parch = DEFAULT_PARCH)

if __name__=='__main__':
	app.run(debug=False)