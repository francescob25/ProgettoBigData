from flask import Flask, render_template
import main

# istruzioni terminale per avviare il progetto
# set FLASK_APP=app
# set FLASK_ENV=development
# flask run

app = Flask(__name__)

@app.route('/')
def index():
    positiveReviews = main.filterByPositive(main.reviews).take(6)
    allReviews = main.reviews.take(6)
    return render_template('index.html', allReviews = allReviews, positiveReviews = positiveReviews)