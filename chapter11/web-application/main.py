#!/usr/bin/env python
from flask import Flask, render_template, flash, request, jsonify, Markup
import numpy as np
import logging
import pickle
app = Flask(__name__)

smp_spam_actuals = None
smp_spam_predictions = None
src = 'D:\home\site\wwwroot\static\pickles\spam_model_output.p'

def rescale(orig_value, orig_set1, new_set2):
	oldRange = max(orig_set1) - min(orig_set1)
	newRange = max(new_set2) - min(new_set2)
	return(((orig_value -  min(orig_set1)) * newRange / oldRange) + min(new_set2))

@app.before_first_request
def startup():
	global smp_spam_actuals, smp_spam_predictions
	# load saved model from web app root directory
	spam_pickles = pickle.load(open(src,'rb'))
	smp_spam_actuals = np.array(spam_pickles[0])
	smp_spam_predictions = np.array(spam_pickles[1])

@app.route('/background_process', methods=['POST', 'GET'])
def background_process():
	x_image_coord = int(request.args.get('new_x_coord'))
	y_image_coord = int(request.args.get('new_y_coord'))

	new_thres = 0.0
	# translate coordinates to threshold
	if (y_image_coord >= 360 and y_image_coord < 390):
		new_thres = 0.1
	elif (y_image_coord >= 340 and y_image_coord < 360):
		new_thres = 0.2
	elif (y_image_coord >= 290 and y_image_coord < 340):
		new_thres = 0.3
	elif (y_image_coord >= 260 and y_image_coord < 290):
		new_thres = 0.4
	elif (y_image_coord >= 220 and y_image_coord < 260):
		new_thres = 0.5
	elif (y_image_coord >= 185 and y_image_coord < 220):
		new_thres = 0.6
	elif (y_image_coord >= 150 and y_image_coord < 185):
		new_thres = 0.7
	elif (y_image_coord >= 115 and y_image_coord < 150):
		new_thres = 0.8
	elif (y_image_coord >= 75 and y_image_coord < 115):
		new_thres = 0.9
	elif (y_image_coord < 75):
		new_thres = 1

	# create data set of new data
	prediction_tmp = np.array([1 if x >= new_thres else 0 for x in smp_spam_predictions])
	# correctly predicted as Ham
	tp = np.sum(np.logical_and(prediction_tmp == 1, smp_spam_actuals == 1))
	# correctly predicted as Spam
	tn = np.sum(np.logical_and(prediction_tmp == 0, smp_spam_actuals == 0))
	# incorrectly predicted as Ham when it was Spam - nuisance...
	fp = np.sum(np.logical_and(prediction_tmp == 1, smp_spam_actuals == 0))
	# incorrectly predicted as Spam when it was Ham - those hurt!
	fn = np.sum(np.logical_and(prediction_tmp == 0, smp_spam_actuals == 1))

	# figure out how do devy up the paper stacks per confusion matrix results
	cm_details = [tp,tn,fp,fn]
	cm_scaled_details = []
	for cm_val in cm_details:
		if (cm_val > 0):
			cm_scaled_details.append(int(round(rescale(cm_val,[min(cm_details), max(cm_details)], [1, 10]))))
		else:
			cm_scaled_details.append(0)

	# possible images
	images_choice = ['00', '01', '02', '04', '06', '08', '10', '12', '14', '16', '18']
	image_tp = '/static/images/' + images_choice[cm_scaled_details[0]]  + '.png'
	image_tn = '/static/images/' + images_choice[cm_scaled_details[1]]  + '.png'
	image_fp = '/static/images/' + images_choice[cm_scaled_details[2]]  + '.png'
	image_fn = '/static/images/' + images_choice[cm_scaled_details[3]]  + '.png'

	# change values to percentages for easier readability
	n = float(len(smp_spam_predictions))
	tp = round(round(tp / n, 4) * 100, 2)
	tn = round(round(tn / n, 4) * 100, 2)
	fp = round(round(fp / n, 4) * 100, 2)
	fn = round(round(fn / n, 4) * 100, 2)
	return jsonify({'threshold':new_thres, 'tp':tp, 'tn':tn, 'fp':fp, 'fn':fn, 'image_tp':image_tp, 'image_tn':image_tn, 'image_fp':image_fp, 'image_fn':image_fn})

@app.route("/", methods=['POST', 'GET'])
def index():
	# on load set form with defaults
	return render_template('index.html')
 
# when running app locally
if __name__ == '__main__':
	# when running on local machine you local directory path
    src = 'static//pickles//spam_model_output.p'
    app.debug = True
    app.run()

