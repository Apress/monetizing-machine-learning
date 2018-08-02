#!/usr/bin/env python
from flask import Flask, render_template, flash, request, jsonify, Markup
import logging, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io, base64, os 
import numpy as np
from array import array
from base64 import decodestring
from PIL import Image
import tensorflow as tf

# global variables
app = Flask(__name__)

# full path to check point
tensorflow_ckpt_file = 'model.ckpt'
 

def GetDigitPrediction(img):
	# restore the saved session

	def weight_variable(shape):
	  initial = tf.truncated_normal(shape, stddev=0.1)
	  return tf.Variable(initial)

	def bias_variable(shape):
	  initial = tf.constant(0.1, shape=shape)
	  return tf.Variable(initial)

	def conv2d(x, W):
	  return tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='SAME')

	def max_pool_2x2(x):
	  return tf.nn.max_pool(x, ksize=[1, 2, 2, 1],
	                        strides=[1, 2, 2, 1], padding='SAME')


	# Input layer
	tf.reset_default_graph()
	x  = tf.placeholder(tf.float32, [None, 784], name='x')
	y_ = tf.placeholder(tf.float32, [None, 10],  name='y_')
	x_image = tf.reshape(x, [-1, 28, 28, 1])

	# Convolutional layer 1
	W_conv1 = weight_variable([5, 5, 1, 32])
	b_conv1 = bias_variable([32])

	h_conv1 = tf.nn.relu(conv2d(x_image, W_conv1) + b_conv1)
	h_pool1 = max_pool_2x2(h_conv1)

	# Convolutional layer 2
	W_conv2 = weight_variable([5, 5, 32, 64])
	b_conv2 = bias_variable([64])

	h_conv2 = tf.nn.relu(conv2d(h_pool1, W_conv2) + b_conv2)
	h_pool2 = max_pool_2x2(h_conv2)

	# Fully connected layer 1
	h_pool2_flat = tf.reshape(h_pool2, [-1, 7*7*64])

	W_fc1 = weight_variable([7 * 7 * 64, 1024])
	b_fc1 = bias_variable([1024])

	h_fc1 = tf.nn.relu(tf.matmul(h_pool2_flat, W_fc1) + b_fc1)

	# Dropout
	keep_prob  = tf.placeholder(tf.float32)
	h_fc1_drop = tf.nn.dropout(h_fc1, keep_prob)

	# Fully connected layer 2 (Output layer)
	W_fc2 = weight_variable([1024, 10])
	b_fc2 = bias_variable([10])

	y = tf.nn.softmax(tf.matmul(h_fc1_drop, W_fc2) + b_fc2, name='y')

	# Evaluation functions
	cross_entropy = tf.reduce_mean(-tf.reduce_sum(y_ * tf.log(y), reduction_indices=[1]))

	correct_prediction = tf.equal(tf.argmax(y, 1), tf.argmax(y_, 1))
	accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32), name='accuracy')

	# Training algorithm
	train_step = tf.train.AdamOptimizer(1e-4).minimize(cross_entropy)
	  

	# Training steps
	saver = tf.train.Saver()
	with tf.Session() as sess:
		sess.run(tf.global_variables_initializer())

		saver.restore(sess, tensorflow_ckpt_file)
		classification = sess.run(tf.argmax(y, 1), feed_dict={x: [img], keep_prob: 1.0})
		return(classification[0])
 

@app.route("/", methods=['POST', 'GET'])
def DrawAndPredict():
	# initial call to set up a blank drawing canvas with an interrogation
	# mark in the wizard's hat

    drawing_data = ''
    prediction = '?'
 
    # set up page with blanks
    return render_template('index.html',
        drawing_data = drawing_data,
        prediction = prediction)

@app.route('/background_process', methods=['POST', 'GET'])
def background_process():
	prediction = -1
	try:
		drawing_data_original = request.form['drawing_data'] 
		user_drawn_image = drawing_data_original.split(',')[1]
		if len(user_drawn_image) > 0:
			buf = io.BytesIO(base64.b64decode(user_drawn_image))
			img = Image.open(buf)
			img = img.resize([28,28])

			# these are transparent images so apply a white background
			corrected_img = Image.new("RGBA", (28, 28), "white")
			corrected_img.paste(img, (0,0), img)
			corrected_img = np.asarray(corrected_img)
			# remove color dimensions
			corrected_img = corrected_img[:, :, 0]
			corrected_img = np.invert(corrected_img)
			# flatten
			corrected_img = corrected_img.reshape([784])
			# center around 0-1
			corrected_img = np.asarray(corrected_img, dtype=np.float32) / 255.

			drawing_data = Markup('<img id="old" src="data:image/png;base64,{}" height="20%" width="20%" >'.format(user_drawn_image))
			prediction = int(GetDigitPrediction(corrected_img))
	except:  
		# something didn't go right - message isn't used but you can plug it in
		# to the return statement if you want to extend this web application
		e = sys.exc_info()[0]
		prediction = e
		message = "Error with prediction, please try again"

	return jsonify({'prediction':prediction})


if __name__=='__main__':
    app.run(debug=True)


