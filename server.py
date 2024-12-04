# app.py
from flask import Flask, render_template, request, url_for, redirect, Blueprint, send_from_directory, flash, session, jsonify
from flask_wtf import FlaskForm
from wtforms.fields import StringField, SubmitField
from wtforms.validators import DataRequired
import os
import json
from login import login_check as lc
from register import register_on_submit as rs
from models import db, Vote

main = Blueprint('main', __name__)

secret_key = str(os.urandom(24))

app = Flask(__name__)
app.config['TESTING'] = False
app.config['DEBUG'] = True
app.config['FLASK_ENV'] = 'deployment'
app.config['SECRET_KEY'] = secret_key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///votes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
app.register_blueprint(main)

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    url = StringField('DataURL', validators=[])
    submit = SubmitField('LOGIN')

first_request = True

@app.before_request
def create_tables():
    global first_request
    if first_request:
        with app.app_context():
            db.create_all()
            first_request = False

@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        url = form.url.data
        status = lc(email, url)
        if status == "Successfully Logged in!":
            session['user_email'] = email
            return redirect(url_for('vote'))
        else:
            flash(status)
            return render_template('fail.html', msg=status)
    return render_template('index.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        url = form.url.data
        status = rs(email, url)
        if status == "Registration Successful!":
            flash("Registration successful! Please login.")
            return redirect(url_for('login'))
        else:
            flash(status)
            return render_template('fail.html', msg=status)
    return render_template('register.html', form=form)

@app.route('/vote', methods=['GET', 'POST'])
def vote():
    if 'user_email' not in session:
        flash('Please login first')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            votes_data = request.form.get('votes')
            print(f"Received votes data: {votes_data}")  # Debugging line
            
            # Check if user has already voted
            existing_votes = Vote.query.filter_by(user_email=session['user_email']).first()
            if existing_votes:
                flash('You have already voted!')
                return redirect(url_for('home'))
            
            if votes_data:
                votes = json.loads(votes_data)
                # Validate that all positions are voted for
                required_positions = {'kubsa_chair', 'secretary', 'treasurer', 'non_resident'}
                if not all(position in votes for position in required_positions):
                    flash('Please vote for all positions')
                    return redirect(url_for('vote'))
                
                # Add votes to database
                try:
                    for position, candidate in votes.items():
                        new_vote = Vote(
                            user_email=session['user_email'],
                            position=position,
                            candidate=candidate
                        )
                        db.session.add(new_vote)
                    db.session.commit()
                    flash('Your votes have been recorded successfully!')
                    return redirect(url_for('home'))
                except Exception as e:
                    db.session.rollback()
                    flash('An error occurred while recording your votes. Please try again.')
                    print(f"Database error: {str(e)}")
                    return redirect(url_for('vote'))
        except Exception as e:
            flash('An error occurred while processing your votes. Please try again.')
            print(f"Error processing votes: {str(e)}")
            return redirect(url_for('vote'))
    
    form = FlaskForm()  # For CSRF protection
    return render_template('vote.html', form=form)

@app.route('/results')
def results():
    if 'admin' not in session:
        flash('Please login as admin')
        return redirect(url_for('admin_login'))
    
    try:
        votes = Vote.query.all()
        results = {}
        
        # Initialize results structure
        positions = ['kubsa_chair', 'secretary', 'treasurer', 'non_resident']
        for position in positions:
            results[position] = {}
        
        # Count votes for each position and candidate
        for vote in votes:
            if vote.position not in results:
                results[vote.position] = {}
            if vote.candidate not in results[vote.position]:
                results[vote.position][vote.candidate] = 0
            results[vote.position][vote.candidate] += 1
        
        return render_template('results.html', results=results)
    except Exception as e:
        flash('An error occurred while retrieving results.')
        print(f"Error retrieving results: {str(e)}")
        return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('user_email', None)
    session.pop('admin', None)
    flash('You have been logged out')
    return redirect(url_for('home'))

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('username') == 'admin' and request.form.get('password') == 'admin123':
            session['admin'] = True
            return redirect(url_for('results'))
        flash('Invalid credentials')
    return render_template('admin_login.html')

@app.route('/favicon.ico') 
def favicon(): 
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == "__main__":
    app.run(debug=True)