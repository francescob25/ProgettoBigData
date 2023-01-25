from flask import Flask, render_template
import main

# istruzioni terminale per avviare il progetto
# set FLASK_APP=app
# set FLASK_ENV=development
# flask --app app.py --debug run

app = Flask(__name__)

currentReviews = main.reviews
filteredByPositive = False
filteredByNegative = False
orderedByShorter = False
orderedByLonger = False

@app.route('/')
def index():
    global currentReviews, filteredByPositive, filteredByNegative, orderedByShorter, orderedByLonger
    filteredByPositive = False
    filteredByNegative = False
    orderedByShorter = False
    orderedByLonger = False
    currentReviews = main.reviews
    return render_template('index.html', reviews=currentReviews.take(6))

@app.route('/positive')
def getPositive():
    global currentReviews, filteredByPositive, filteredByNegative, orderedByShorter, orderedByLonger
    if (not filteredByPositive):
        currentReviews = main.filterByPositive(main.reviews)
    else:
        currentReviews = main.reviews
    filteredByPositive = not filteredByPositive
    filteredByNegative = False
    # controlliamo se era stato effettuato l'ordinamento precedentemente
    if (orderedByShorter):
        currentReviews = main.orderByShortReviews(currentReviews)
    elif (orderedByLonger):
        currentReviews = main.orderByLongReviews(currentReviews)
    return render_template('index.html', reviews=currentReviews.take(6))

@app.route('/negative')
def getNegative():
    global currentReviews, filteredByNegative, filteredByPositive, orderedByShorter, orderedByLonger
    if (not filteredByNegative):
        currentReviews = main.filterByNegative(main.reviews)
    else:
        currentReviews = main.reviews
    filteredByNegative = not filteredByNegative
    filteredByPositive = False
    # controlliamo se era stato effettuato l'ordinamento precedentemente
    if (orderedByShorter):
        currentReviews = main.orderByShortReviews(currentReviews)
    elif (orderedByLonger):
        currentReviews = main.orderByLongReviews(currentReviews)
    return render_template('index.html', reviews=currentReviews.take(6))

@app.route('/shorter')
def orderByShorterReviews():
    global currentReviews, orderedByShorter, orderedByLonger, filteredByPositive, filteredByNegative
    if (not orderedByShorter):
        currentReviews = main.orderByShortReviews(currentReviews)
    else:
        if (filteredByPositive): currentReviews = main.filterByPositive(main.reviews)
        elif (filteredByNegative): currentReviews = main.filterByNegative(main.reviews)
        else: currentReviews = main.reviews
    orderedByShorter = not orderedByShorter
    orderedByLonger = False
    return render_template('index.html', reviews=currentReviews.take(6))

@app.route('/longer')
def orderByLongerReviews():
    global currentReviews, orderedByLonger, orderedByShorter, filteredByPositive, filteredByNegative
    if (not orderedByLonger):
        currentReviews = main.orderByLongReviews(currentReviews)
    else:
        if (filteredByPositive): currentReviews = main.filterByPositive(main.reviews)
        elif (filteredByNegative): currentReviews = main.filterByNegative(main.reviews)
        else: currentReviews = main.reviews
    orderedByLonger = not orderedByLonger
    orderedByShorter = False
    return render_template('index.html', reviews=currentReviews.take(6))