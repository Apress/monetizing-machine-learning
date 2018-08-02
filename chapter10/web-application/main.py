#!/usr/bin/env python
from flask import Flask, render_template, flash, request, jsonify, Markup
import logging, io, base64, os
import pandas as pd
import numpy as np
from scipy.sparse.linalg import svds
import scipy.sparse as sps
import wikipedia

MOVIE_GENRES = ["Action", "Adventure", "Animation", "Children", "Comedy", "Crime",
							 "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror",
							 "IMAX", "Musical", "Mystery", "Romance", "Sci-Fi", "Thriller",
							 "War", "Western"]

def GetMoviesByGenres(movies_df, genre):
	# Returns a list of all movies and movie IDs for a particular genre. 
	# It is called whenever a user changes the "Movie Genre" drop-down box

	movies_of_type = movies_df[movies_df['genres'].str.contains(genre)].sort_values('title')
	movie_ids = list(movies_of_type['movieId'].values)
	movie_titles = [str(x)[0:50] for x in list(movies_of_type['title'].values)]
  
	return (movie_ids, movie_titles)

def GetSparseSVD(ratings_centered_matrix, K):
    '''
    ratings_centered_matrix
    # Compute the largest k singular values/vectors for a sparse matrix.
    # k : int, optional
    # Number of singular values and vectors to compute. Must be 1 <= k < min(A.shape)
    
    Returns
    u : ndarray, shape=(M, k) Unitary matrix having left singular vectors as columns 
    sigma : ndarray, shape=(k,k) Diagonal singular values.
    vt : ndarray, shape=(k, N)Unitary matrix having right singular vectors as rows
    '''

    u, s, vt = svds(ratings_centered_matrix, k=K)
    # get it back in k diagongal format for matrix multiplication
    sigma = np.diag(s)
    return u, sigma, vt

def GetRecommendedMovies(ratings_df, movies_df, user_history_movie_ids):
	# add back to ratings_matrix_centered
	ratings_df_cp = ratings_df.copy()

	# create a new user id - add 1 to current largest
	new_user_id = np.max(ratings_df_cp['userId']) + 1

	new_user_movie_ids = user_history_movie_ids
	new_user_ratings = 	[4.5] * len(new_user_movie_ids)

	# fix index to be multilevel with userId and movieId
	ratings_df_cp.set_index(['userId', 'movieId'], inplace=True)

	for idx in range(len(new_user_movie_ids)):
		# add new movie rating as a pandas series and insert new row at end of ratings_df_cp
		row_to_append = pd.Series([new_user_ratings[idx]])
		cols = ['rating']
		ratings_df_cp.loc[(new_user_id, new_user_movie_ids[idx]), cols] = row_to_append.values

	# create new ratings_matrix
	ratings_matrix_plus = sps.csr_matrix((ratings_df_cp.rating, 
	                      (ratings_df_cp.index.labels[0], ratings_df_cp.index.labels[1]))).todense()

	user_ratings_mean = np.mean(ratings_matrix_plus, axis = 1)
	ratings_matrix_centered = ratings_matrix_plus - user_ratings_mean.reshape(-1, 1)

	Ua, sigma, Vt = GetSparseSVD(ratings_matrix_centered, K=50)
	all_user_predicted_ratings = np.dot(np.dot(Ua, sigma), Vt) + user_ratings_mean.reshape(-1, 1)
	# predictions_df based on row/col ids, not original movie ids
	predictions_df = pd.DataFrame(all_user_predicted_ratings, columns = movies_df.index)  

	# Get and sort the user's predictions
	sorted_user_predictions = predictions_df.iloc[new_user_id].sort_values(ascending=False)
	sorted_user_predictions = pd.DataFrame(sorted_user_predictions).reset_index()
	sorted_user_predictions.columns = ['movieId', 'predictions']
	sorted_user_predictions = sorted_user_predictions.merge(movies_df, left_on='movieId', right_on='movieId', how='inner').sort_values('predictions', ascending=False)
	sorted_user_predictions = sorted_user_predictions[~sorted_user_predictions['movieId'].isin(new_user_movie_ids)]
	movie_titles = [str(x)[0:50] for x in list(sorted_user_predictions['title'].values)][0:3]
	return(movie_titles[0], movie_titles[1], movie_titles[2])



def GetWikipediaData(title_name):
	# extract wiki bio

	description = wikipedia.page(title_name).content
	description = description.split('\n\n')[0]
	
	image = 'https://www.wikipedia.org/static/apple-touch/wikipedia.png'

	try:
		images = wikipedia.page(title_name).images
		for image in images:
			if ('jpeg' in image) or ('jpg' in image) or ('png' in image):
				break;
	except:
		print('error getting wikipedia poster image')

 
	# keep only intro paragraph
	return(description, image)
 

ratings_df = None
movies_df = None
genres = None

app = Flask(__name__)

@app.before_first_request
def startup():
	global ratings_df, movies_df, genres
	# load data sets
	# fix all userIds and movieIds
	movies_df_raw = pd.read_csv('movies.csv')
	# movies_df_raw['movieId_new'] = movies_df_raw.index
	 
	# remove timestamp from original ratings_df_raw
	ratings_df_raw = pd.read_csv('ratings.csv')
	ratings_df_raw = ratings_df_raw[['userId', 'movieId', 'rating']]

	# remove any movies not found in the ratings set
	movies_df_raw = movies_df_raw[movies_df_raw['movieId'].isin(ratings_df_raw['movieId'])]

	# reset index
	movies_df_raw = movies_df_raw.reset_index(drop=True)
	movies_df_raw['movieId_new'] = movies_df_raw.index
 
	# make all ratings movieIds the same
	ratings_df_raw = ratings_df_raw.merge(movies_df_raw[['movieId', 'movieId_new']], on='movieId', how='inner') 
	ratings_df_raw = ratings_df_raw[['userId',  'movieId_new', 'rating']]
	ratings_df_raw.columns = ['userId',  'movieId', 'rating']
	# clean up userids to start at 0 not 1
	ratings_df_raw['userId'] -= 1

	movies_df_raw = movies_df_raw[['movieId_new', 'title', 'genres']]
	movies_df_raw.columns = ['movieId', 'title', 'genres']
	movies_df = movies_df_raw.copy()

	# set userId and movieId as indexes in order to make them as x and y axis of sparse matrix
	ratings_df = ratings_df_raw.copy()
 
@app.route("/", methods=['POST', 'GET'])
def ready():
	selected_genre = 'Select movie genre'
	selected_movie_title1 = 'Select first movie you liked'
	selected_movie_title2 = 'Select second movie you liked'
	selected_movie_title3 = 'Select third movie you liked'
	selected_movie_id1 = -1
	selected_movie_id2 = -1
	selected_movie_id3 = -1
	options_movie_ids = []
	options_movie_titles = []
	recommended_title_1 = ''
	recommended_title_2 = ''
	recommended_title_3 = ''
	wiki_movie_description = ''
	wiki_movie_poster = 'https://www.wikipedia.org/static/apple-touch/wikipedia.png'

	if request.method == 'POST':
		
		selected_genre = request.form['selected_genres']
		selected_movie_id1 = request.form['selected_movie_id1']
		selected_movie_id2 = request.form['selected_movie_id2']
		selected_movie_id3 = request.form['selected_movie_id3']
		options_movie_ids, options_movie_titles = GetMoviesByGenres(movies_df, selected_genre)
		options_movie_ids = [str(idx) + '||' + mv for idx,mv in zip(options_movie_ids, options_movie_titles)]
		
		user_movie_ids = []

		movie_id = int(selected_movie_id1.split('||')[0])
		if (movie_id >= 0):
			selected_movie_title1 = selected_movie_id1.split('||')[1]
			user_movie_ids.append(movie_id)

		movie_id = int(selected_movie_id2.split('||')[0])
		if (movie_id >= 0):
			selected_movie_title2 = selected_movie_id2.split('||')[1]
			user_movie_ids.append(movie_id)

		movie_id = int(selected_movie_id3.split('||')[0])
		if (movie_id >= 0):
			selected_movie_title3 = selected_movie_id3.split('||')[1]
			user_movie_ids.append(movie_id)
			
		if (len(user_movie_ids) > 0):
			recommended_title_1, recommended_title_2, recommended_title_3 = GetRecommendedMovies(ratings_df, movies_df, user_movie_ids)
			wiki_movie_description, wiki_movie_poster = GetWikipediaData(recommended_title_1 + ' film')
 

	return render_template('index.html',
		options_movie_genres = MOVIE_GENRES,
		selected_genre = selected_genre,
		options_movie_ids = options_movie_ids,
		options_movie_titles = options_movie_titles,
		selected_movie_title1 = selected_movie_title1,
		selected_movie_title2 = selected_movie_title2,
		selected_movie_title3 = selected_movie_title3,
		selected_movie_id1 = selected_movie_id1,
		selected_movie_id2 = selected_movie_id2,
		selected_movie_id3 = selected_movie_id3,
		wiki_movie_description = wiki_movie_description,
		wiki_movie_poster = wiki_movie_poster,
		recommended_title_1 = recommended_title_1,
		recommended_title_2 = recommended_title_2,
		recommended_title_3 = recommended_title_3)
	
 
 
@app.route('/background_process', methods=['POST', 'GET'])
def background_process():
	# get recommendations for another movie after user clicks on new title
	movie_title = request.args.get('movie_title')
	wiki_movie_description, wiki_movie_poster = GetWikipediaData(movie_title + ' film') 
 
	return jsonify({'wiki_movie_description':wiki_movie_description, 'wiki_movie_poster':  wiki_movie_poster})
	

 
if __name__=='__main__':
	app.run(debug=True)
