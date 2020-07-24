# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import logging
from logging import Formatter, FileHandler

import babel
import dateutil.parser
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import PickleType

from forms import *

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    genres = db.Column(PickleType)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))
    image_link = db.Column(db.String(500))
    website = db.Column(db.String())
    facebook_link = db.Column(db.String(120))

    shows = db.relationship('Show', backref='venue', lazy=True)


class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))
    image_link = db.Column(db.String(500))
    website = db.Column(db.String())
    facebook_link = db.Column(db.String(120))

    shows = db.relationship('Show', backref='artist', lazy=True)


class Show(db.Model):
    __tablename__ = 'shows'

    id = db.Column(db.Integer, primary_key=True)

    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'))
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'))
    start_time = db.Column(db.DateTime, nullable=False)


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    all_venues = Venue.query.all()
    data = []
    locations = []
    current_date = datetime.now()

    for venue in all_venues:
        num_upcoming_shows = Show.query.filter_by(venue_id=venue.id).filter(Show.start_time > current_date).all()
        location = {
            "city": venue.city,
            "state": venue.state
        }

        if location not in locations:
            locations.append(location)
            venue_data = {
                "venues": [{
                    "id": venue.id,
                    "name": venue.name,
                    "num_upcoming_shows": len(num_upcoming_shows)
                }]
            }
            data.append(dict(list(location.items()) + list(venue_data.items())))

        else:
            for dt in data:
                if dt.get('city') == venue.city and dt.get('state') == venue.state:
                    dt['venues'].append({
                        "id": venue.id,
                        "name": venue.name,
                        "num_upcoming_shows": len(num_upcoming_shows)
                    })

    return render_template('pages/venues.html', areas=data);


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_str = request.form.get('search_term')
    search_query = Venue.query.filter(Venue.name.ilike('%{}%'.format(search_str))).all()

    data = []
    current_date = datetime.now()

    for venue in search_query:
        num_upcoming_shows = Show.query.filter_by(venue_id=venue.id).filter(Show.start_time > current_date).all()
        data_object = {
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": num_upcoming_shows,
        }

        data.append(data_object)

    response = {
        "count": len(search_query),
        "data": data
    }

    return render_template('pages/search_venues.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    current_date = datetime.now()

    venue = Venue.query.get(venue_id)

    past_shows = Show.query.filter_by(venue_id=venue_id).filter(Show.start_time < current_date).all()
    past_shows_data = []

    for past in past_shows:
        artist_show = Artist.query.get(past.artist_id)
        past_show_obj = {
            "artist_id": past.artist_id,
            "artist_name": artist_show.name,
            "artist_image_link": artist_show.image_link,
            "start_time": past.start_time
        }

        past_shows_data.append(past_show_obj)

    upcoming_shows = Show.query.filter_by(venue_id=venue_id).filter(Show.start_time > current_date).all()
    upcoming_shows_data = []

    for upcoming in upcoming_shows:
        artist_show = Artist.query.get(upcoming.artist_id)
        upcoming_show_obj = {
            "artist_id": upcoming.artist_id,
            "artist_name": artist_show.name,
            "artist_image_link": artist_show.image_link,
            "start_time": upcoming.start_time
        }

        upcoming_shows_data.append(upcoming_show_obj)

    data = {
        "id": venue_id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_shows_data,
        "upcoming_shows": upcoming_shows_data,
        "past_shows_count": len(past_shows_data),
        "upcoming_shows_count": len(upcoming_shows_data),
    }

    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm()
    if form.validate():
        try:
            new_venue = Venue(name=form.name.data,
                              genres=form.genres.data,
                              city=form.city.data,
                              state=form.state.data,
                              address=form.address.data,
                              phone=form.phone.data,
                              seeking_talent=form.seeking_talent.data,
                              seeking_description=form.seeking_description.data,
                              image_link=form.image_link.data,
                              website=form.website.data,
                              facebook_link=form.facebook_link.data
                              )
            db.session.add(new_venue)
            db.session.commit()
            flash('Venue ' + request.form['name'] + ' was successfully listed!')
        except:
            flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
            db.session.rollback()
        finally:
            db.session.close()
    else:
        flash('There is a form error')
        return render_template('forms/new_venue.html', form=form)

    return render_template('pages/home.html')


@app.route('/venues/<int:venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        Venue.query.filter_by(id=venue_id).delete()
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()

    return redirect(url_for('index'))


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    artists_query = Artist.query.all()
    data = []

    for artist in artists_query:
        artist_data = {
            "id": artist.id,
            "name": artist.name
        }
        data.append(artist_data)

    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_str = request.form.get('search_term')
    search_query = Artist.query.filter(Artist.name.ilike('%{}%'.format(search_str))).all()

    current_date = datetime.now()
    data = []

    for artist in search_query:
        upcoming_shows = Show.query.filter_by(artist_id=artist.id).filter(Show.start_time > current_date).all()

        artist_data = {
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": len(upcoming_shows)
        }

        data.append(artist_data)

    response = {
        "count": len(search_query),
        "data": data
    }
    return render_template('pages/search_artists.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    current_date = datetime.now()

    past_shows = Show.query.filter_by(artist_id=artist_id).filter(Show.start_time < current_date).all()
    past_shows_data = []

    for past in past_shows:
        venue_show = Venue.query.get(past.venue_id)
        past_show_obj = {
            "venue_id": past.artist_id,
            "venue_name": venue_show.name,
            "venue_image_link": venue_show.image_link,
            "start_time": past.start_time
        }

        past_shows_data.append(past_show_obj)

    upcoming_shows = Show.query.filter_by(artist_id=artist_id).filter(Show.start_time > current_date).all()
    upcoming_shows_data = []

    for upcoming in upcoming_shows:
        venue_show = Venue.query.get(upcoming.venue_id)
        upcoming_show_obj = {
            "venue_id": upcoming.artist_id,
            "venue_name": venue_show.name,
            "venue_image_link": venue_show.image_link,
            "start_time": upcoming.start_time
        }

        upcoming_shows_data.append(upcoming_show_obj)

    artist = Artist.query.get(artist_id)

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows_data,
        "upcoming_shows": upcoming_shows_data,
        "past_shows_count": len(past_shows_data),
        "upcoming_shows_count": len(upcoming_shows_data),
    }

    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)

    if form.validate():
        try:
            artist.name = form.name.data
            artist.city = form.city.data
            artist.state = form.state.data
            artist.phone = form.phone.data
            artist.genres = form.genres.data
            artist.seeking_venue = form.seeking_venue.data
            artist.seeking_description = form.seeking_description.data
            artist.image_link = form.image_link.data
            artist.website = form.website.data
            artist.facebook_link = form.facebook_link.data

            db.session.commit()
        except:
            db.session.rollback()
        finally:
            db.session.close()
    else:
        flash('There is a form error')
        return render_template('forms/edit_artist.html', form=form, artist=artist)

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = {
        "id": 1,
        "name": "The Musical Hop",
        "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
        "address": "1015 Folsom Street",
        "city": "San Francisco",
        "state": "CA",
        "phone": "123-123-1234",
        "website": "https://www.themusicalhop.com",
        "facebook_link": "https://www.facebook.com/TheMusicalHop",
        "seeking_talent": True,
        "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
        "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
    }
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion

    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    data = [{
        "venue_id": 1,
        "venue_name": "The Musical Hop",
        "artist_id": 4,
        "artist_name": "Guns N Petals",
        "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
        "start_time": "2019-05-21T21:30:00.000Z"
    }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "artist_id": 5,
        "artist_name": "Matt Quevedo",
        "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
        "start_time": "2019-06-15T23:00:00.000Z"
    }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "artist_id": 6,
        "artist_name": "The Wild Sax Band",
        "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
        "start_time": "2035-04-01T20:00:00.000Z"
    }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "artist_id": 6,
        "artist_name": "The Wild Sax Band",
        "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
        "start_time": "2035-04-08T20:00:00.000Z"
    }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "artist_id": 6,
        "artist_name": "The Wild Sax Band",
        "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
        "start_time": "2035-04-15T20:00:00.000Z"
    }]
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead

    # on successful db insert, flash success
    flash('Show was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
