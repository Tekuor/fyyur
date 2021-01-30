#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
import datetime
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys
from sqlalchemy import func, case, desc
from datetime import date
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False, server_default="false")
    seeking_description = db.Column(db.String(500))
    genres = db.Column(db.ARRAY(db.String()))
    shows = db.relationship('Show', backref='venues', cascade="all,delete", lazy=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
      return f'<Venue {self.id} {self.name}>'

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean())
    seeking_description = db.Column(db.String(500))
    genres = db.Column(db.ARRAY(db.String()))
    shows = db.relationship('Show', backref='artists', lazy=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    start_time = db.Column(db.DateTime)
# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  if isinstance(value, str):
    date = dateutil.parser.parse(value)
  else:
    date = value
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  venues = Venue.query.order_by(desc(Venue.created_date)).limit(10).all()
  artists = Artist.query.order_by(desc(Artist.created_date)).limit(10).all()
  return render_template('pages/home.html', venues=venues, artists=artists)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data = []
  address = db.session.query(Venue).distinct('city', 'state').all()
  for value in address:
    body = {}
    body['city'] = value.city
    body['state'] = value.state
    test = db.session.query(Venue).filter(Venue.city==value.city, Venue.state==value.state).all()
    venues = db.session.query(Venue.name, Venue.id, func.count(case([(Show.start_time >= date.today(), 1)])).label('num_upcoming_shows')).outerjoin(Show).filter(Venue.city==value.city, Venue.state==value.state).group_by(Venue.id).all()
    body['venues'] = venues
    data.append(body)
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search = request.form.get('search_term', '')
  data =  db.session.query(Venue.name, Venue.id, func.count(case([(Show.start_time >= date.today(), 1)])).label('num_upcoming_shows')).outerjoin(Show).filter(Venue.name.ilike("%" + search + "%")).group_by(Venue.id).all()
  response={
    "count": len(data),
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>', methods=['GET'])
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  upcoming_shows = db.session.query(Show.artist_id, Artist.name.label("artist_name"), Artist.image_link.label("artist_image_link"), Show.start_time).join(Artist).filter(Show.venue_id == venue_id, Show.start_time >= date.today()).all()
  past_shows = db.session.query(Show.artist_id, Artist.name.label("artist_name"), Artist.image_link.label("artist_image_link"), Show.start_time).join(Artist).filter(Show.venue_id == venue_id, Show.start_time < date.today()).all()
  venue = db.session.query(Venue).filter_by(id=venue_id).first()
  data = venue
  setattr(data, 'upcoming_shows', upcoming_shows)
  setattr(data, 'past_shows', past_shows)
  setattr(data, 'past_shows_count', len(past_shows))
  setattr(data, 'upcoming_shows_count', len(upcoming_shows))
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False
  data = {}
  try:
    name =request.form.get('name', '')
    city = request.form.get('city', '')
    state = request.form.get('state', '')
    address = request.form.get('address', '')
    phone = request.form.get('phone', '')
    genres = request.form.getlist('genres')
    facebook_link = request.form.get('facebook_link', '')
    image_link = request.form.get('image_link', '')
    seeking_talent = request.form.get('seeking_talent', '')
    seeking_description = request.form.get('seeking_description', '')
    website = request.form.get('website', '')

    if seeking_talent == 'y':
      seeking_talent=True
    else:
      seeking_talent=False

    venue = Venue(
    name=name, 
    city=city, 
    state=state,
    address=address,
    phone=phone,
    facebook_link=facebook_link,
    genres=genres,
    image_link=image_link,
    seeking_talent=seeking_talent,
    seeking_description=seeking_description,
    website=website
    )
    db.session.add(venue)
    db.session.commit()
    data = venue
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    if error:
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    else:
      flash('Venue ' + data.name + ' was successfully listed!')
    db.session.close()
  # on successful db insert, flash success
  # flash('Venue ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return redirect(url_for("index"))

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  error = False
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
    if error:
      flash('An error occurred. Deleting venue')
    else:
      flash('Venue was deleted successfully!')

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return redirect(url_for("index"))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search = request.form.get('search_term', '')
  data =  db.session.query(Artist.name, Artist.id, func.count(case([(Show.start_time >= date.today(), 1)])).label('num_upcoming_shows')).outerjoin(Show).filter(Artist.name.ilike("%" + search + "%")).group_by(Artist.id).all()
  response={
    "count": len(data),
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  upcoming_shows = db.session.query(Show.venue_id.label('venue_id'), Venue.name.label("venue_name"), Venue.image_link.label("venue_image_link"), Show.start_time).join(Venue).filter(Show.artist_id == artist_id, Show.start_time >= date.today()).all()
  past_shows = db.session.query(Show.venue_id.label('venue_id'), Venue.name.label("venue_name"), Venue.image_link.label("venue_image_link"), Show.start_time).join(Venue).filter(Show.artist_id == artist_id, Show.start_time < date.today()).all()
  artist = db.session.query(Artist).filter_by(id=artist_id).first()
  data = artist
  setattr(data, 'upcoming_shows', upcoming_shows)
  setattr(data, 'past_shows', past_shows)
  setattr(data, 'past_shows_count', len(past_shows))
  setattr(data, 'upcoming_shows_count', len(upcoming_shows))
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.filter_by(id=artist_id).first()
  form = ArtistForm(obj=artist)
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  try:
    artist = Artist.query.get(artist_id)
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.genres = request.form.getlist('genres')
    artist.facebook_link = request.form['facebook_link']
    artist.image_link = request.form.get('image_link', '')
    if request.form.get('seeking_venue', '') == 'y':
      artist.seeking_venue=True
    else:
      artist.seeking_venue=False
    artist.seeking_description = request.form.get('seeking_description', '')
    artist.website = request.form.get('website', '')
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.filter_by(id=venue_id).first()
  form = VenueForm(obj=venue)
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  try:
    venue = Venue.query.get(venue_id)
    venue.name =request.form.get('name', '')
    venue.city = request.form.get('city', '')
    venue.state = request.form.get('state', '')
    venue.address = request.form.get('address', '')
    venue.phone = request.form.get('phone', '')
    venue.genres = request.form.getlist('genres')
    venue.facebook_link = request.form.get('facebook_link', '')
    venue.image_link = request.form.get('image_link', '')
    if request.form.get('seeking_talent', '') == 'y':
      venue.seeking_talent=True
    else:
      venue.seeking_talent=False
    venue.seeking_description = request.form.get('seeking_description', '')
    venue.website = request.form.get('website', '')
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
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
  error = False
  data = {}
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    facebook_link = request.form['facebook_link']
    image_link = request.form.get('image_link', '')
    seeking_venue = request.form.get('seeking_venue', '')
    seeking_description = request.form.get('seeking_description', '')
    website = request.form.get('website', '')

    if seeking_venue == 'y':
      seeking_venue=True
    else:
      seeking_venue=False

    artist = Artist(
    name=name, 
    city=city, 
    state=state,
    phone=phone,
    facebook_link=facebook_link,
    genres=genres,
    image_link=image_link,
    seeking_venue=seeking_venue,
    seeking_description=seeking_description,
    website=website
    )
    db.session.add(artist)
    db.session.commit()
    data = artist
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    if error:
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    else:
      flash('Artist ' + data.name + ' was successfully listed!')
    db.session.close()

  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return redirect(url_for("index"))

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data = db.session.query(Show.artist_id.label('artist_id'), Artist.name.label("artist_name"), Artist.image_link.label("artist_image_link"),Show.venue_id.label('venue_id'), Venue.name.label("venue_name"), Venue.image_link.label("venue_image_link"), Show.start_time).join(Venue).join(Artist).all()
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
  error = False
  body = {}
  try:
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    start_time = request.form['start_time']
    show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
    db.session.add(show)
    db.session.commit()
    body = show
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Show could not be listed.')
  else:
    flash('Show listed!')

  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return redirect(url_for("index"))
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

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
