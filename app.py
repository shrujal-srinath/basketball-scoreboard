from flask import Flask, render_template, request, redirect, session, url_for
from flask_socketio import SocketIO, emit, join_room
import os
import random

app = Flask(__name__)
app.secret_key = 'super_secret_key'

# Use threading to avoid eventlet problems
socketio = SocketIO(app, async_mode='threading')

games = {}

def create_default_game():
    return {
        'home_score': 0,
        'away_score': 0,
        'home_fouls': 0,
        'away_fouls': 0,
        'period': 1,
        'home_name': 'Home',
        'away_name': 'Away'
    }

@app.route('/')
def home():
    return "<a href='/create'>Create Game</a> | <a href='/watch'>Watch Game</a>"

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        code = request.form['game_code'].strip().upper()
        if not code or code in games:
            return "Invalid or duplicate game code. <a href='/create'>Try again</a>"
        games[code] = create_default_game()
        session['game_code'] = code
        session['creator'] = True
        return redirect(url_for('control', code=code))
    return render_template('create.html')

@app.route('/watch', methods=['GET', 'POST'])
def watch():
    if request.method == 'POST':
        code = request.form['game_code'].strip().upper()
        if code in games:
            return redirect(url_for('display', code=code))
        else:
            return "Invalid Game Code. <a href='/watch'>Try again</a>"
    return render_template('watch.html')

@app.route('/control/<code>')
def control(code):
    return render_template('control.html', state=games[code], code=code)

@app.route('/display/<code>')
def display(code):
    return render_template('display.html', state=games[code], code=code)

@socketio.on('join')
def on_join(data):
    join_room(data['room'])
    emit('update_state', games[data['room']], to=data['room'])

@socketio.on('start_game_clock')
def start_game_clock(data):
    emit('game_clock_started', room=data['room'])

@socketio.on('pause_game_clock')
def pause_game_clock(data):
    emit('game_clock_paused', room=data['room'])

@socketio.on('reset_game_clock')
def reset_game_clock(data):
    emit('game_clock_reset', room=data['room'])

@socketio.on('set_game_clock')
def set_game_clock(data):
    emit('set_game_clock', {'seconds': data['seconds']}, room=data['room'])

@socketio.on('start_shot_clock')
def start_shot_clock(data):
    emit('shot_clock_started', room=data['room'])

@socketio.on('pause_shot_clock')
def pause_shot_clock(data):
    emit('shot_clock_paused', room=data['room'])

@socketio.on('reset_shot_clock')
def reset_shot_clock(data):
    emit('shot_clock_reset', room=data['room'])

@socketio.on('set_shot_clock')
def set_shot_clock(data):
    emit('set_shot_clock', {'seconds': data['seconds']}, room=data['room'])




