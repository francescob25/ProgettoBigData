from flask import Flask, render_template
import main

# istruzioni terminale per avviare il progetto
# set FLASK_APP=app
# set FLASK_ENV=development
# flask run

app = Flask(__name__)

@app.route('/positive')
def getPositive():
    positive=main.filterByPositive(main.reviews).take(6)
    return render_template('index.html', reviews = positive)

@app.route('/')
def index():
    reviews=main.reviews.take(6)
    return render_template('index.html', reviews = reviews)