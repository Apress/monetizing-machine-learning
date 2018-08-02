#!/usr/bin/env python
from flask import Flask, render_template, flash, request, jsonify, Markup
import logging, io, os, sys
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
import scipy
import pickle

# EB looks for an 'application' callable by default.
application = Flask(__name__)

# model related variables
gbm_model = None
features = ['fixed acidity',
			 'volatile acidity',
			 'citric acid',
			 'residual sugar',
			 'chlorides',
			 'free sulfur dioxide',
			 'total sulfur dioxide',
			 'density',
			 'pH',
			 'sulphates',
			 'alcohol',
			 'color']
 
def get_wine_image_to_show(wine_color, wine_quality):
	if wine_color == 0:
		wine_color_str = 'white'
	else:
		wine_color_str = 'red'
	return('/static/images/wine_' + wine_color_str + '_' + str(wine_quality) + '.jpg')

@application.before_first_request
def startup():
	global gbm_model 

	# load saved model from web app root directory
	gbm_model = pickle.load(open("static/pickles/gbm_model_dump.p",'rb'))
 

@application.errorhandler(500)
def server_error(e):
    logging.exception('some eror')
    return """
    And internal error <pre>{}</pre>
    """.format(e), 500

@application.route('/background_process', methods=['POST', 'GET'])
def background_process():
	fixed_acidity = float(request.args.get('fixed_acidity'))
	volatile_acidity = float(request.args.get('volatile_acidity'))
	citric_acid = float(request.args.get('citric_acid'))
	residual_sugar = float(request.args.get('residual_sugar'))
	chlorides = float(request.args.get('chlorides'))
	free_sulfur_dioxide = float(request.args.get('free_sulfur_dioxide'))
	total_sulfur_dioxide = float(request.args.get('total_sulfur_dioxide'))
	density = float(request.args.get('density'))
	pH = float(request.args.get('pH'))
	sulphates = float(request.args.get('sulphates'))
	alcohol = float(request.args.get('alcohol'))
	color = int(request.args.get('color'))


	# create data set of new data
	x_test_tmp = pd.DataFrame([[fixed_acidity,
		volatile_acidity,
		citric_acid,
		residual_sugar,
		chlorides,
		free_sulfur_dioxide,
		total_sulfur_dioxide,
		density,
		pH,
		sulphates,
		alcohol,
		color]], columns = features)


	# predict quality based on incoming values
	preds = gbm_model.predict_proba(x_test_tmp[features])

	# get best quality prediction from original quality scale
	predicted_quality = [3,6,9][np.argmax(preds[0])]
	return jsonify({'quality_prediction':predicted_quality, 'image_name': get_wine_image_to_show(color, predicted_quality)})


@application.route("/", methods=['POST', 'GET'])
def index():
	logging.warning("index!")
	# on load set form with defaults
	return render_template('index.html', quality_prediction=1, image_name='/static/images/wine_red_6.jpg')
 
# when running app locally
if __name__ == '__main__':
    application.debug = True
    application.run()

