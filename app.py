from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

combined = pd.read_csv('combined.csv', delimiter=',', encoding='utf-8')
combined = combined.drop(columns=['Unnamed: 0'])
sleepTime = combined.sleeptime.values.tolist()
for i in range(len(sleepTime)):
    sleepTime[i] = int(sleepTime[i].split(':')[0]) + int(sleepTime[i].split(':')[1]) / 60
combined['sleeptime'] = sleepTime


@app.route('/<int:uid>')
def home(uid):
    print(uid)
    return render_template('init.html', flag=None, uid=uid)


@app.route('/<int:uid>/state')
def state(uid):
    df = combined.drop(combined[combined['UID'] != uid].index)
    dstate = df.d_state.values.tolist()
    esm = df.ESM.values.tolist()
    date = df.timestamp.values.tolist()
    return render_template('depression_state.html', flag='depression_state', uid=uid, dstate=dstate, esm=esm, date=date)


@app.route('/<int:uid>/relation')
def relation(uid):
    df = combined.drop(combined[combined['UID'] != uid].index)
    labels = df.groupby(['d_state'])['app_usage'].mean().index.tolist()
    walking = df.groupby(['d_state'])['walking'].mean().values.tolist()
    running = df.groupby(['d_state'])['running'].mean().values.tolist()
    bicycle = df.groupby(['d_state'])['bicycle'].mean().values.tolist()
    app_usage = df.groupby(['d_state'])['app_usage'].mean().values.tolist()
    sleeptime = df.groupby(['d_state'])['sleeptime'].mean().values.tolist()

    return render_template('depression_state.html', flag='relation', labels=labels, walking=walking,
                           running=running, bicycle=bicycle, app_usage=app_usage, sleeptime=sleeptime, uid=uid)





@app.route('/<int:uid>/recommendation', methods=["GET", "POST"])
def recommendation(uid):
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
            dstatetext = 'Now you are good more than ever!'
            sleeptext = 'You need no recommendation for now.'
            activitytext = 'Just do as you are doing now!'
            apptext = '^____________________________^'
            return render_template('depression_state.html', flag='recommendation', uid=uid, score=0, sleeptime=0,
                                   apptime=0, activitytime=0, app_mean=0, sleep_mean=0, activity_mean=0,
                                   dstatetext=dstatetext, sleeptext=sleeptext, activitytext=activitytext, apptext=apptext)
        
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
            sleeptext = "You lack sleep. Sleeping {} more hours can help you feel better".format(round(sleep_mean - sleeptime, 3))

        if activitytime >= activity_mean:
            activitytext = "You were active today! Great Job!!"
        else:
            activitytext = "You are not active enough. Walk/Run/Bicycle {} more hours can help you feel better".format(round(activity_mean - activitytime, 3))

        if apptime <= app_mean:
            apptext = "You used app less! Great Job!!"
        else:
            apptext = "You used smartphone too much. Reducing {} hours can help you feel better".format(round(apptime - app_mean, 3))

        return render_template('depression_state.html', flag='recommendation', uid=uid, score=score,
                               sleeptime=sleeptime, apptime=apptime, activitytime=activitytime,
                               app_mean=app_mean, sleep_mean=sleep_mean, activity_mean=activity_mean,
                               dstatetext=dstatetext, sleeptext=sleeptext, activitytext=activitytext, apptext=apptext)

    else:
        return render_template('depression_state.html', flag='recommendation', uid=uid, score=0, sleeptime=0,
                               apptime=0, activitytime=0, app_mean=0, sleep_mean=0, activity_mean=0,
                               dstatetext='', sleeptext='', activitytext='', apptext='')


if __name__ == '__main__':
    app.run()
