from flask import Flask, render_template, request, redirect, session, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
app.secret_key = 'super_secret_key'
socketio = SocketIO(app)

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'score123'
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

def is_authorized(code):
    return session.get('creator') and session.get('game_code') == code

@app.route('/')
def home():
    return "<a href='/create'>Create Game</a> | <a href='/watch'>Watch Game</a>"

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USERNAME and request.form['password'] == ADMIN_PASSWORD:
            code = request.form['game_code'].strip().upper()
            if not code or code in games:
                return "Invalid or duplicate game code. <a href='/create'>Try again</a>"
            games[code] = create_default_game()
            session['game_code'] = code
            session['creator'] = True
            return redirect(url_for('control', code=code))
        else:
            return "Invalid credentials. <a href='/create'>Try again</a>"
    return '''<form method='post'>Username: <input name='username'><br>Password: <input name='password'><br>Game Code: <input name='game_code'><br><button type='submit'>Create</button></form>'''

@app.route('/watch', methods=['GET', 'POST'])
def watch():
    if request.method == 'POST':
        code = request.form['game_code'].strip().upper()
        if code in games:
            return redirect(url_for('display', code=code))
        else:
            return "Invalid Game Code. <a href='/watch'>Try again</a>"
    return '''<form method='post'>Game Code: <input name='game_code'><br><button type='submit'>Watch</button></form>'''

@app.route('/control/<code>')
def control(code):
    if not is_authorized(code): return redirect('/create')
    return render_template('control.html', state=games[code], code=code)

@app.route('/display/<code>')
def display(code):
    return render_template('display.html', state=games[code], code=code)

@app.route('/update/<code>', methods=['POST'])
def update(code):
    if not is_authorized(code): return redirect('/create')
    team = request.form['team']
    action = request.form['action']
    if team in ['home', 'away']:
        key = f"{team}_score"
        if action == 'increment':
            games[code][key] += 1
        elif action == 'decrement' and games[code][key] > 0:
            games[code][key] -= 1
    socketio.emit('update_state', games[code], to=code)
    return redirect(url_for('control', code=code))

@app.route('/foul/<code>', methods=['POST'])
def foul(code):
    if not is_authorized(code): return redirect('/create')
    team = request.form['team']
    games[code][f"{team}_fouls"] += 1
    socketio.emit('update_state', games[code], to=code)
    return redirect(url_for('control', code=code))

@app.route('/period/<code>', methods=['POST'])
def period(code):
    if not is_authorized(code): return redirect('/create')
    games[code]['period'] += 1
    socketio.emit('update_state', games[code], to=code)
    return redirect(url_for('control', code=code))

@app.route('/reset/<code>', methods=['POST'])
def reset(code):
    if not is_authorized(code): return redirect('/create')
    games[code] = create_default_game()
    socketio.emit('update_state', games[code], to=code)
    return redirect(url_for('control', code=code))

@app.route('/set_names/<code>', methods=['POST'])
def set_names(code):
    if not is_authorized(code): return redirect('/create')
    games[code]['home_name'] = request.form['home_name']
    games[code]['away_name'] = request.form['away_name']
    socketio.emit('update_state', games[code], to=code)
    return redirect(url_for('control', code=code))

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

if __name__ == '__main__':
    socketio.run(app, debug=True)
