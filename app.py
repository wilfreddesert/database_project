from flask import Flask, g, render_template, request,flash, redirect, url_for
import sqlite3
import os

DATABASE = "fpl.sqlite"

# Create app
app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'super-secret'

# check if the database exist, if not create the table and insert a few lines of data
if not os.path.exists(DATABASE):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("CREATE TABLE users (fname TEXT, lname TEXT, age INTEGER);")
    conn.commit()
    cur.execute("INSERT INTO users VALUES('Mike', 'Tyson', '40');")
    cur.execute("INSERT INTO users VALUES('Thomas', 'Jasper', '40');")
    cur.execute("INSERT INTO users VALUES('Jerry', 'Mouse', '40');")
    cur.execute("INSERT INTO users VALUES('Peter', 'Pan', '40');")
    conn.commit()
    conn.close()


# helper method to get the database since calls are per thread,
# and everything function is a new thread when called
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


# helper to close
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route("/")
def index():
    cur = get_db().cursor()
    res = cur.execute("select * from players")
    return render_template("index.html", players = res)

def get_item(id):
    team = get_db().execute(
        'select id, name, code, short_name from teams where id = ?',(id,)
    ).fetchone()

    return team

def get_player(id):
    player = get_db().execute(
        'select * from players where id = ?',(id,)
    ).fetchone()

    return player


@app.route("/teams")
def teams():
    cur = get_db().cursor()
    res = cur.execute("select * from teams")
    return render_template("teams.html", teams = res)

@app.route("/roles")
def roles():
    cur = get_db().cursor()
    res = cur.execute("select * from roles")
    return render_template("roles.html", roles = res)


@app.route('/add', methods=('GET', 'POST'))
def add():
    """Create a new post for the current user."""
    if request.method == 'POST':
        name = request.form['name']
        code = request.form['code']
        short_name = request.form['short_name']

        if not name:
            error = 'Name is required'

        
        else:
            db = get_db()
            db.execute(
                'INSERT INTO teams (id, name, code,short_name)'
                ' VALUES (?, ?, ?,?)',
                (None, name, code, short_name)
            )
            db.commit()
            return redirect(url_for('teams'))

    return render_template('add.html')

@app.route('/add_player', methods=('GET', 'POST'))
def add_player():
    """Create a new post for the current user."""
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        squad_number = request.form['squad_number']

        if not first_name:
            error = 'Name is required'

        
        else:
            db = get_db()
            db.execute(
                'INSERT INTO players (id, first_name, second_name,squad_number)'
                ' VALUES (?, ?, ?,?)',
                (None, first_name, last_name, squad_number)
            )
            db.commit()
            return redirect(url_for('index'))

    return render_template('add_player.html')

@app.route('/<int:id>/edit', methods=('GET', 'POST'))
def edit(id):
    """Update a post if the current user is the author."""
    team = get_item(id)
    if request.method == 'POST':
        name = request.form['name']
        code = request.form['code']
        short_name = request.form['short_name']

        if not name:
            error = 'Name is required.'

        else:
            db = get_db()
            db.execute(
                'UPDATE teams SET name = ?, code = ?, short_name = ? WHERE id = ?',
                (name, code, short_name, id)
            )
            db.commit()
            return redirect(url_for('teams'))

    return render_template('edit.html', team = team)

@app.route('/<int:id>/edit_player', methods=('GET', 'POST'))
def edit_player(id):
    """Update a post if the current user is the author."""
    player = get_player(id)
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        squad_number = request.form['squad_number']

        if not first_name or not last_name:
            error = 'Name is required.'

        else:
            db = get_db()
            db.execute(
                'UPDATE players SET first_name = ?, second_name = ?, squad_number = ? WHERE id = ?',
                (first_name, last_name, squad_number, id)
            )
            db.commit()
            return redirect(url_for('index'))

    return render_template('edit_player.html', player = player)


@app.route('/<int:id>/delete', methods=('POST',))
def delete(id):
    """Delete a post.
    Ensures that the post exists and that the logged in user is the
    author of the post.
    """
    get_item(id)
    db = get_db()
    db.execute('DELETE FROM teams WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('teams'))

@app.route('/<int:id>/delete_player', methods=('POST',))
def delete_player(id):
    """Delete a post.
    Ensures that the post exists and that the logged in user is the
    author of the post.
    """
    get_player(id)
    db = get_db()
    db.execute('DELETE FROM players WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('index'))

@app.route("/top")
def top_players():
    cur = get_db().cursor()
    sql = '''select
  p.web_name,
  t.name                as club,
  r.singular_name_short as position,
  max(p.total_points)   as total_points
from players p left join teams t on p.team = t.id
  left join roles r on p.element_type = r.id
group by p.team order by p.total_points DESC'''

    res = cur.execute(sql)
    return render_template("top_players.html", players = res)

@app.route("/search",methods=('GET','POST'))
def search():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        team = request.form['team']
        min_points = request.form['min_points']
        
        return redirect(url_for('search_results', name = first_name, surname = last_name, club = team, threshold = min_points))
    return render_template("search.html")

@app.route("/search_results")
def search_results():
    first_name = request.args.get('name')
    last_name = request.args.get('surname')
    team = request.args.get('club')
    min_points = request.args.get('threshold')
    cur = get_db().cursor()
    sql =  '''
    select
  p.first_name,
  p.second_name,
  t.name,
  p.total_points
from players p left join teams t on p.team = t.id '''
    params = []

    if last_name or first_name or team or min_points:
        sql+= "where"

    if last_name:
        sql+= ''' p.second_name = ? '''
        params+=[last_name]
    if first_name:
        add = " and p.first_name = ?" if len(params) > 0 else " p.first_name = ?"
        sql+=add
        params+=[first_name]
    if team:
        add = " and t.name = ?" if len(params) > 0 else " t.name = ?"
        sql+=add
        params+=[team]
    if min_points:
        add = " and p.total_points>=?" if len(params) > 0 else " p.total_points>=?"
        sql+=add
        params+=[min_points]
    res = cur.execute(sql, params)
    return render_template("search_results.html",results = res)


@app.route("/top_from_club")
def top_players_from_club():
    cur = get_db().cursor()
    sql = '''select
  p.web_name,
  p.now_cost,
  t.name                as club,
  r.singular_name_short as position,
  max(p.total_points)   as total_points
from players p left join teams t on p.team = t.id
  left join roles r on p.element_type = r.id
group by p.team order by total_points DESC;'''

    res = cur.execute(sql)
    return render_template("top_players_from_club.html", players = res)


if __name__ == "__main__":
    """
	Use python sqlite3 to create a local database, insert some basic data and then
	display the data using the flask templating.
	
	http://flask.pocoo.org/docs/0.12/patterns/sqlite3/
    """
    app.run()