from flask import Flask, render_template, request, g, redirect, session, url_for, flash
import pandas as pd
from sqlite3 import dbapi2 as sqlite3
import os
from contextlib import closing
from werkzeug.security import generate_password_hash, check_password_hash


def connect_db():
    """Returns a new connection to the database."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "data/user.db")
    return sqlite3.connect(file_path)


def init_db():
    """Creates the database tables."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "data/schema.sql")
    print(file_path)
    with closing(connect_db()) as db:
        with app.open_resource(file_path, mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


app = Flask(__name__)
app.secret_key = "ie481-final"
init_db()

combined = pd.read_csv('./data/combined.csv', delimiter=',', encoding='utf-8')
combined = combined.drop(columns=['Unnamed: 0'])
sleepTime = combined.sleeptime.values.tolist()
for i in range(len(sleepTime)):
    sleepTime[i] = int(sleepTime[i].split(':')[0]) + int(sleepTime[i].split(':')[1]) / 60
combined['sleeptime'] = sleepTime


detail_score=pd.read_csv('./data/detail_score_final.csv', delimiter=',', encoding='utf-8')

@app.route('/home')
def home():
    if not g.user:
        return redirect(url_for('login'))
    return render_template('init.html', flag=None, uid=g.user['uid'])


@app.route('/state')
def state():
    uid = session['uid']
    df = combined.drop(combined[combined['UID'] != uid].index)
    score_df=detail_score.drop(detail_score[detail_score['UID']!=uid].index)
    dstate = df.d_state.values.tolist()
    esm = df.ESM.values.tolist()
    date = df.timestamp.values.tolist()
    valence=score_df.Valence.values.tolist()
    arousal=score_df.Arousal.values.tolist()
    stress= score_df.Stress.values.tolist()
    return render_template('depression_state.html', flag='depression_state', uid=uid, dstate=dstate, esm=esm, date=date, valence=valence, arousal=arousal, stress=stress)


@app.route('/relation')
def relation():
    uid = session['uid']
    df = combined.drop(combined[combined['UID'] != uid].index)
    labels = df.groupby(['d_state'])['app_usage'].mean().index.tolist()
    walking = df.groupby(['d_state'])['walking'].mean().values.tolist()
    running = df.groupby(['d_state'])['running'].mean().values.tolist()
    bicycle = df.groupby(['d_state'])['bicycle'].mean().values.tolist()
    app_usage = df.groupby(['d_state'])['app_usage'].mean().values.tolist()
    sleeptime = df.groupby(['d_state'])['sleeptime'].mean().values.tolist()

    return render_template('depression_state.html', flag='relation', labels=labels, walking=walking,
                           running=running, bicycle=bicycle, app_usage=app_usage, sleeptime=sleeptime, uid=uid)


@app.route('/recommendation', methods=["GET", "POST"])
def recommendation():
    uid = session['uid']
    df = combined.drop(combined[combined['UID'] != uid].index)

    if request.method == "POST":
        score = request.form['score']
        sleeptime = request.form['sleeptime']
        apptime = request.form['apptime']
        activitytime = request.form['activitytime']
        if not (sleeptime.isdigit() or apptime.isdigit() or activitytime.isdigit()):
            return render_template('depression_state.html', flag='recommendation', uid=uid, score=0, sleeptime=0,
                                   apptime=0, activitytime=0, app_mean=0, sleep_mean=0, activity_mean=0,
                                   dstatetext='', sleeptext='', activitytext='', apptext='')
        score = float(score)
        if len(df.groupby(['ESM']).filter(lambda group: group.ESM > score)) == 0:
            dstatetext = 'Now you are in the best condition!!'
            sleeptext = 'You need no recommendation for now.'
            activitytext = 'Just do as you are doing now!'
            apptext = '^____________________________^'
            return render_template('depression_state.html', flag='recommendation', uid=uid, score=0, sleeptime=0,
                                   apptime=0, activitytime=0, app_mean=0, sleep_mean=0, activity_mean=0,
                                   dstatetext=dstatetext, sleeptext=sleeptext, activitytext=activitytext,
                                   apptext=apptext)

        sleeptime = float(sleeptime)
        apptime = float(apptime)
        activitytime = float(activitytime)
        app_mean = df.groupby(['ESM']).filter(lambda group: group.ESM > score)['app_usage'].mean()
        sleep_mean = df.groupby(['ESM']).filter(lambda group: group.ESM > score)['sleeptime'].mean()
        activity_mean = df.groupby(['ESM']).filter(lambda group: group.ESM > score)['walking'].mean() \
                        + df.groupby(['ESM']).filter(lambda group: group.ESM > score)['walking'].mean() \
                        + df.groupby(['ESM']).filter(lambda group: group.ESM > score)['walking'].mean()

        if score > 1:
            dstate = 'Excited State'
        elif score > -1:
            dstate = 'Neutral State'
        elif score > -3:
            dstate = 'level1'
        elif score > -5:
            dstate = 'level2'
        elif score > -7:
            dstate = 'level3'
        elif score > -9:
            dstate = 'level4'
        else:
            dstate = 'Unknown'

        dstatetext = "Now you are in {}".format(dstate)

        if sleeptime >= sleep_mean:
            sleeptext = "You slept well! Great Job!!"
        else:
            sleeptext = "You lack sleep. Sleeping {} more hours can help you feel better".format(
                round(sleep_mean - sleeptime, 3))

        if activitytime >= activity_mean:
            activitytext = "You were active today! Great Job!!"
        else:
            activitytext = "You are not active enough. Walk/Run/Bicycle {} more hours can help you feel better".format(
                round(activity_mean - activitytime, 3))

        if apptime <= app_mean:
            apptext = "You used app less! Great Job!!"
        else:
            apptext = "You used smartphone too much. Reducing {} hours can help you feel better".format(
                round(apptime - app_mean, 3))

        return render_template('depression_state.html', flag='recommendation', uid=uid, score=score,
                               sleeptime=sleeptime, apptime=apptime, activitytime=activitytime,
                               app_mean=app_mean, sleep_mean=sleep_mean, activity_mean=activity_mean,
                               dstatetext=dstatetext, sleeptext=sleeptext, activitytext=activitytext, apptext=apptext)

    else:
        return render_template('depression_state.html', flag='recommendation', uid=uid, score=0, sleeptime=0,
                               apptime=0, activitytime=0, app_mean=0, sleep_mean=0, activity_mean=0,
                               dstatetext='', sleeptext='', activitytext='', apptext='')


@app.route('/', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('home'))
    error = None
    if request.method == 'POST':
        User = query_db('''select * from user where
            uid = ?''', [request.form['uid']], one=True)
        if User is None:
            error = 'Invalid username'
        elif not check_password_hash(User['pw_hash'],
                                     request.form['password']):
            error = 'Invalid password'
        else:
            flash('You were logged in')
            session['uid'] = User['uid']
            return redirect(url_for('home'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    """Logs the user out."""
    flash('You were logged out')
    session.pop('uid', None)
    return redirect(url_for('login'))


@app.before_request
def before_request():
    """Make sure we are connected to the database each request and look
    up the current user so that we know he's there.
    """
    g.db = connect_db()
    g.user = None
    if 'uid' in session:
        g.user = query_db('select * from user where uid = ?',
                          [session['uid']], one=True)


@app.teardown_request
def teardown_request(exception):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'db'):
        g.db.close()


def query_db(query, args=(), one=False):
    """Queries the database and returns a list of dictionaries."""
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv


if __name__ == '__main__':
    app.run()
