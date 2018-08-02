#!/usr/bin/env python
from flask import Flask, render_template, flash, request, jsonify, Markup
import mysql.connector
from mysql.connector import MySQLConnection, Error
import logging, uuid, random

app = Flask(__name__)

# NOTE: You need to replace all the <<ENTER-YOUR-DATABASE-USERNAME>> in 
# the code - there are a total of 6 places where you need to enter your 
# own PythonAnywhere database name
mysql_account='<<ENTER-YOUR-DATABASE-USERNAME>>'
mysql_password='thesecret'
mysql_database='<<ENTER-YOUR-DATABASE-USERNAME>>$ABTesting'
mysql_host="<<ENTER-YOUR-DATABASE-USERNAME>>.mysql.pythonanywhere-services.com"

def GetUUID():
    return (str(uuid.uuid4()))

def InsertInitialVisit(uuid_, pageid):
    try:
        cnx = mysql.connector.connect(user=mysql_account, password=mysql_password, database=mysql_database, host=mysql_host)
        cursor = cnx.cursor()
        query = "INSERT INTO <<ENTER-YOUR-DATABASE-USERNAME>>$ABTesting.tblFrontPageOptions (uuid, liked, pageid) VALUES (%s,%s,%s);"
        args = (uuid_, 0, pageid)
        cursor.execute(query, args)
        cursor.close()
        cnx.commit()
        cnx.close()
    except mysql.connector.Error as err:
        app.logger.error("Something went wrong: {}".format(err))


def UpdateVisitWithLike(uuid_):
    try:
        cnx = mysql.connector.connect(user=mysql_account, password=mysql_password, database=mysql_database, host=mysql_host)
        cursor = cnx.cursor()
        query = "UPDATE <<ENTER-YOUR-DATABASE-USERNAME>>$ABTesting.tblFrontPageOptions SET liked = %s WHERE uuid = %s;"
        args = (1, uuid_)
        cursor.execute(query, args)
        cursor.close()
        cnx.commit()
        cnx.close()
    except mysql.connector.Error as err:
        app.logger.error("Something went wrong: {}".format(err))


def GetVoteResults():
    results = ''
    total_votes = 0
    total_up_votes = 0
    total_up_votes_page_1 = 0
    total_up_votes_page_2 = 0
    try:
        cnx = mysql.connector.connect(user=mysql_account, password=mysql_password, database=mysql_database, host=mysql_host)
        cursor = cnx.cursor()
        query = "SELECT * FROM <<ENTER-YOUR-DATABASE-USERNAME>>$ABTesting.tblFrontPageOptions"
        cursor.execute(query)

        for (uuid_, liked, pageid, time_stamp) in cursor:
            total_votes += 1
            if liked==1 and pageid==1:
                total_up_votes_page_1 += 1
            if liked==1 and pageid==2:
                total_up_votes_page_2 += 1
            if liked == 1:
                total_up_votes += 1
            results += ("uuid: {} liked:{} pageid: {} on {:%m/%d/%Y %H:%M:%S}".format(uuid_, liked, pageid, time_stamp)) + "<br />"
        cursor.close()
        cnx.close()
    except mysql.connector.Error as err:
        app.logger.error("Something went wrong: {}".format(err))

    return (results, total_votes, total_up_votes, total_up_votes_page_1, total_up_votes_page_2)


@app.route("/", methods=['POST', 'GET'])
def index():
    uuid = GetUUID()
    # randomly select a background image
    pageid = random.randint(1, 2)
    message = "<b>If<br />you<br /> like<br /> me<br />click<br />on<br />the<br />thumb<br />to<br />turn<br />it<br />up</b>"
    thumbs="fa-thumbs-down"

    if request.method == 'POST':
        # pick up original uuid for updates
        uuid = request.form['uuid']
        pageid = int(request.form['pageid'])
        message = "<b>Thanks<br />for<br />voting!<br />.<br />.<br />.<br />.<br />.<br />.</b>"
        thumbs="fa-thumbs-up"
        UpdateVisitWithLike(uuid)
    else:
        # we assume the user didn't like the page
        InsertInitialVisit(uuid, pageid)

    # assign random background image
    background_image = 'background1.jpg'
    if (pageid==2):
        background_image = 'background2.jpg'

    return render_template('index.html',
                uuid=uuid,
                thumbs=thumbs,
                pageid = pageid,
                background_image = background_image,
                message=Markup(message))

@app.route("/admin/")
def admin():
    # show the results of the votes
    results, total_votes, total_up_votes, total_up_votes_page_1, total_up_votes_page_2 = GetVoteResults()
    total_down_votes = total_votes - total_up_votes
    return render_template('admin.html',
            results=Markup(results),
            total_votes=total_votes,
            total_up_votes = total_up_votes,
            total_down_votes = total_down_votes,
            total_up_votes_page_1 = total_up_votes_page_1,
            total_up_votes_page_2 = total_up_votes_page_2)

# when running app locally
if __name__=='__main__':
      app.run(debug=True)