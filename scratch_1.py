from flask import Flask, render_template, request, g, redirect, session, url_for, flash
import pandas as pd
from sqlite3 import dbapi2 as sqlite3
import os
from contextlib import closing
from werkzeug.security import generate_password_hash, check_password_hash


def connect_db():
    """Returns a new connection to the database."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "user.db")
    print(file_path)
    return sqlite3.connect(file_path)


def init_db():
    """Creates the database tables."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "schema.sql")
    print(file_path)
    with closing(connect_db()) as db:
        with open(file_path, 'r') as f:
            db.cursor().executescript(f.read())
        db.commit()


init_db()
combined = pd.read_csv('combined.csv', delimiter=',', encoding='utf-8')
combined = combined.drop(columns=['Unnamed: 0'])
uidlist = combined['UID'].values.tolist()
with closing(connect_db()) as db:
    for ids in uidlist:
        db.execute('''insert into user (
                        uid, pw_hash) values ( ?, ?)''',
                   [ids, generate_password_hash("a{}".format(ids))])
    db.commit()
