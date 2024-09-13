from flask import Flask, request, render_template, redirect, url_for, jsonify
from pymongo import MongoClient
from bson.json_util import dumps
import pandas as pd
from datetime import datetime

app = Flask(__name__)

# Configure MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client.budgetTracker
income_collection = db.Income
expense_collection = db.Expense

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_income', methods=['GET', 'POST'])
def add_income():
    if request.method == 'POST':
        date_str = request.form['date']
        amount = float(request.form['amount'])
        category = request.form['category']
        description = request.form['description']

        # Convert date string to datetime object
        date = datetime.strptime(date_str, '%Y-%m-%d')

        record = {
            'date': date,
            'amount': amount,
            'category': category,
            'description': description
        }
        income_collection.insert_one(record)
        return redirect(url_for('index'))
    return render_template('add_income.html')

@app.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    if request.method == 'POST':
        date_str = request.form['date']
        amount = float(request.form['amount'])
        category = request.form['category']
        description = request.form['description']

        # Convert date string to datetime object
        date = datetime.strptime(date_str, '%Y-%m-%d')

        record = {
            'date': date,
            'amount': amount,
            'category': category,
            'description': description
        }
        expense_collection.insert_one(record)
        return redirect(url_for('index'))
    return render_template('add_expense.html')

@app.route('/view/<collection_name>')
def view_data(collection_name):
    if collection_name == 'Income':
        data = list(income_collection.find())
    else:
        data = list(expense_collection.find())

    return render_template('view_data.html', data=data, collection_name=collection_name)

@app.route('/analysis')
def analysis():
    return render_template('analysis.html')

@app.route('/monthly_spending', methods=['GET', 'POST'])
def monthly_spending():
    selected_month = request.form.get('month', datetime.now().strftime('%Y-%m'))  # Default to current month
    year, month = map(int, selected_month.split('-'))
    # Aggregate expense data
    expenses = db.Expense.aggregate([
        {
            '$match': {
                'date': {
                    '$gte': datetime(year, month, 1),
                    '$lt': datetime(year, month + 1, 1)
                }
            }
        },
        {
            '$group': {
                '_id': '$category',
                'total': {'$sum': '$amount'}
            }
        }
    ])
    # Convert cursor to list
    expenses_list = list(expenses)
    # Pass data to template
    return render_template('monthly_spending.html', year=year, month=month, expenses_list=expenses_list)

@app.route('/yearly_spending_analysis', methods=['GET'])
def yearly_spending_analysis():
    year = int(request.args.get('year', datetime.now().year))

    # Aggregation pipeline to get total income by category
    income_pipeline = [
        {
            '$match': {
                'date': {
                    '$gte': datetime(year, 1, 1),
                    '$lt': datetime(year + 1, 1, 1)
                }
            }
        },
        {
            '$group': {
                '_id': '$category',
                'total_income': {'$sum': '$amount'}
            }
        },
        {
            '$sort': {'total_income': -1}  # Sort by total income in descending order
        }
    ]
    
    # Aggregation pipeline to get total expenses by category
    expense_pipeline = [
        {
            '$match': {
                'date': {
                    '$gte': datetime(year, 1, 1),
                    '$lt': datetime(year + 1, 1, 1)
                }
            }
        },
        {
            '$group': {
                '_id': '$category',
                'total_expense': {'$sum': '$amount'}
            }
        },
        {
            '$sort': {'total_expense': -1}  # Sort by total expense in descending order
        }
    ]

    # Execute the pipelines
    income_results = list(db.Income.aggregate(income_pipeline))
    expense_results = list(db.Expense.aggregate(expense_pipeline))

    # Convert results into dictionaries for easy access
    income_by_category = {result['_id']: result['total_income'] for result in income_results}
    expense_by_category = {result['_id']: result['total_expense'] for result in expense_results}

    return render_template('yearly_spending_analysis.html', year=year, income_by_category=income_by_category, expense_by_category=expense_by_category)

@app.route('/monthly_income_expense')
def monthly_income_expense():
    # Aggregate monthly income data
    income = db.Income.aggregate([
        {
            '$group': {
                '_id': {'$month': '$date'},
                'total': {'$sum': '$amount'}
            }
        },
        {
            '$sort': {'_id': 1}  # Sort by month in ascending order
        }
    ])
    # Aggregate monthly expense data
    expenses = db.Expense.aggregate([
        {
            '$group': {
                '_id': {'$month': '$date'},
                'total': {'$sum': '$amount'}
            }
        },
        {
            '$sort': {'_id': 1}  # Sort by month in ascending order
        }
    ])  
    # Convert cursors to lists
    income_list = list(income)
    expenses_list = list(expenses)
    
    # Pass data to template
    return render_template('monthly_income_expense.html', income=income_list, expenses=expenses_list)

if __name__ == '__main__':
    app.run(debug=True)