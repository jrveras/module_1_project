import sqlite3
import logging
import sys

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

dbConnCount = 0

class Error(Exception):
    """Base class for other exceptions"""
    pass

class TableNotExists(Error):
    """Raised when the table does not exists"""
    pass

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    global dbConnCount
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    dbConnCount += 1
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        app.logger.debug("Article with ID " + str(post_id) + " not found!")
        return render_template('404.html'), 404
    else:
        app.logger.debug("Article " + post['title'] + " retrieved!")
        # print (post['title'])
        return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.debug("The 'About Us' page is retrieved")
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()

            app.logger.debug("The article " + title + " is created")

            return redirect(url_for('index'))

    return render_template('create.html')

@app.route('/healthz')
def health():
    try:
        connection = get_db_connection()
        tableExists = connection.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='posts'").fetchone()
        connection.close()

        if tableExists[0] == 0:
            raise TableNotExists
        
        response = app.response_class(
            response=json.dumps({ "result": "OK - healthy" }),
            status=200,
            mimetype='application/json'
        )
    except sqlite3.Error as e:
        response = app.response_class(
            response=json.dumps({ "result": "ERROR - unhealthy" }),
            status=500,
            mimetype='application/json'
        )
    except TableNotExists as e:
        connection.close()
        response = app.response_class(
            response=json.dumps({ "result": "ERROR - unhealthy" }),
            status=500,
            mimetype='application/json'
        )
    except Exception as e:
        connection.close()
        response = app.response_class(
            response=json.dumps({ "result": "ERROR - unhealthy", "error": format(e) }),
            status=500,
            mimetype='application/json'
        )
    return response

@app.route('/metrics')
def metrics():
    connection = get_db_connection()
    postsCount = connection.execute('SELECT COUNT(*) FROM posts').fetchone()
    connection.close()

    response = app.response_class(
        response=json.dumps(
            {
                "status":"success",
                "code":0,
                "data": {"db_connection_count": dbConnCount, "post_count": postsCount[0]}
            }
        ),
        status=200,
        mimetype='application/json'
    )
    app.logger.debug("Article retrieved!")
    return response

# start the application on port 3111
if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout,
                        level=logging.DEBUG,
                        format='%(asctime)s:%(levelname)s:%(name)s:[%(filename)s.%(funcName)s:%(lineno)d]:%(message)s')

    app.run(host='0.0.0.0', port='3111')
