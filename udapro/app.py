#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import sys
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort 
from flask_moment import Moment
import logging
from flask_migrate import Migrate
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from models import db, Artist, Venue, Show
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
db.init_app(app)
# connecting to a local postgresql database
app.config.from_object('config')
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

# Implementing Show and Artist models, and complete all model relationships and properties, as a database migration.


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime



#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # replacing with real venues data.
 
    data_areas = []

    areas = Venue.query \
        .with_entities(Venue.city, Venue.state) \
        .group_by(Venue.city, Venue.state) \
        .all()

    for area in areas:
        data_venues = []

        venues = Venue.query \
            .filter_by(state=area.state) \
            .filter_by(city=area.city) \
            .all()

        for venue in venues:
            upcoming_shows = db.session \
                    .query(Show) \
                    .filter(Show.venue_id == venue.id) \
                    .filter(Show.start_time > datetime.now()) \
                    .all()

            data_venues.append({
                'id': venue.id,
                'name': venue.name,
                'num_upcoming_shows': len(upcoming_shows)
            })

        data_areas.append({
            'city': area.city,
            'state': area.state,
            'venues': data_venues
        })

    return render_template('pages/venues.html', areas=data_areas)


@app.route('/venues/search', methods=['POST'])
def search_venues():
  # implementing search on artists with partial string search. 

    search_term = request.form['search_term']
    search = "%{}%".format(search_term)

    venues = Venue.query \
        .with_entities(Venue.id, Venue.name) \
        .filter(Venue.name.match(search)) \
        .all()

    data_venues = []
    for venue in venues:
        upcoming_shows = db.session \
                .query(Show) \
                .filter(Show.venue_id == venue.id) \
                .filter(Show.start_time > datetime.now()) \
                .all()

        data_venues.append({
            'id': venue.id,
            'name': venue.name,
            'num_upcoming_shows': len(upcoming_shows)
        })

    results = {
        'venues': data_venues,
        'count': len(venues)
    }

    return render_template(
      'pages/search_venues.html',
      results=results,
      search_term=search_term
    )


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # showing the venue page with the given venue_id
  # getting real venue data from the venues table, using venue_id
    data_venue = Venue.query.filter(Venue.id == venue_id).first()

    upcoming_shows = Show.query \
        .filter(Show.venue_id == venue_id) \
        .filter(Show.start_time > datetime.now()) \
        .all()

    if len(upcoming_shows) > 0:
        data_upcoming_shows = []

        for upcoming_show in upcoming_shows:
            artist = Artist.query \
                .filter(Artist.id == upcoming_show.artist_id) \
                .first()

            data_upcoming_shows.append({
                'artist_id': artist.id,
                'artist_name': artist.name,
                'artist_image_link': artist.image_link,
                'start_time': str(upcoming_show.start_time),
            })

        data_venue.upcoming_shows = data_upcoming_shows
        data_venue.upcoming_shows_count = len(data_upcoming_shows)

    past_shows = Show.query \
        .filter(Show.venue_id == venue_id) \
        .filter(Show.start_time < datetime.now()) \
        .all()

    if len(past_shows) > 0:
        data_past_shows = []

        for past_show in past_shows:
            artist = Artist.query \
                .filter(Artist.id == past_show.artist_id) \
                .first()

            data_past_shows.append({
                'artist_id': artist.id,
                'artist_name': artist.name,
                'artist_image_link': artist.image_link,
                'start_time': str(past_show.start_time),
            })

        data_venue.past_shows = data_past_shows
        data_venue.past_shows_count = len(data_past_shows)

    return render_template('pages/show_venue.html', venue=data_venue)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # inserting form data 
    error = False
    form = VenueForm()


    # modifying data to be the data object returned from db insertion
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    facebook_link = request.form['facebook_link']
    website_link = request.form['website_link']
    seeking_talent = True if 'seeking_talent' in request.form else False
    seeking_description = request.form['seeking_description']
    image_link = request.form['image_link']

    try:
        venue = Venue(
          name=name,
          city=city,
          state=state,
          address=address,
          phone=phone,
          genres=genres,
          facebook_link=facebook_link,
          website_link=website_link,
          seeking_talent=seeking_talent,
          seeking_description=seeking_description,
          image_link=image_link
        )

        db.session.add(venue)
        db.session.commit()
    except Exception:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    # flash success
    if not error:
        flash("Venue " + name + " was successfully listed!")
# if there is an error instead
    else:
        flash("An error occurred. Venue " + name + " could not be listed.")
        abort(400)

    return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # To delete a record
    error = False

    try:
        Venue.query.filter_by(id=venue_id).delete()
        db.session.commit()
    except Exception as e:
        error = True
        db.session.rollback()
        print(sys.exc_info())
        return render_template('errors/500.html', error=str(e))
    finally:
        db.session.close()

    if not error:
        flash(
          'Venue was successfully deleted!'
        )

    # if there is an error
    else:
      flash(
          'An error occurred. Venue could not be deleted.'
        )
      abort(400)
        

    return render_template('pages/home.html')
#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    data = []
    # Getting data from the data base
    artists = Artist.query.with_entities(Artist.id, Artist.name).order_by('id').all()
    for artist in artists:
        # for each artists upcoming show
        upcoming_shows = db.session.query(Show).filter(Show.artist_id == artist.id).filter(Show.start_time > datetime.now()).all()

        data.append({
            'id': artist.id,
            'name': artist.name,
            'num_upcoming_shows': len(upcoming_shows)
        })

    return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # searching for artists with partial string search.
    search_term = request.form['search_term']
    search = "%{}%".format(search_term)

    artists = Artist.query.with_entities(Artist.id, Artist.name).filter(Artist.name.match(search)).all()

    data = []
    for artist in artists:
        #filtering by shows
        upcoming_shows = db.session.query(Show).filter(Show.artist_id == artist.id).filter(Show.start_time > datetime.now()).all()

        # Grouping the data
        data.append({
            'id': artist.id,
            'name': artist.name,
            'num_upcoming_shows': len(upcoming_shows)
        })

    response = {
        'data': data,
        'count': len(artists)
    }

    return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # showing the artist page with the given artist_id
  # Getting data from the artist table, using artist_id
    data = Artist.query.filter(Artist.id == artist_id).first()

    upcoming_shows = Show.query.filter(Show.artist_id == artist_id).filter(Show.start_time > datetime.now()).all()

    if len(upcoming_shows) > 0:
        upcoming_shows_queue = []

        # Getting upcoming shows and grouping by venue
        for upcoming_show in upcoming_shows:
            venue = Venue.query.filter(Venue.id == upcoming_show.venue_id).first()

            upcoming_shows_queue.append({
                'venue_id': venue.id,
                'venue_name': venue.name,
                'venue_image_link': venue.image_link,
                'start_time': str(upcoming_show.start_time),
            })

        # adding data to query
        data.upcoming_shows = upcoming_shows_queue
        data.upcoming_shows_count = len(upcoming_shows_queue)

    # Getting past shows and grouping by venue
    past_shows = Show.query.filter(Show.artist_id == artist_id).filter(Show.start_time < datetime.now()).all()

    if len(past_shows) > 0:
        data_past_shows = []

        for past_show in past_shows:
            venue = Venue.query.filter(Venue.id == upcoming_show.venue_id).first()

            data_past_shows.append({
                'venue_id': venue.id,
                'venue_name': venue.name,
                'venue_image_link': venue.image_link,
                'start_time': str(past_show.start_time),
            })

        # adding data to query
        data.past_shows = data_past_shows
        data.past_shows_count = len(data_past_shows)

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  # populate form with fields from artist with ID <artist_id>
  # Getting data from db
    artist = Artist.query.filter(Artist.id == artist_id).first()

    # getting values to replace old data
    form = ArtistForm()
    form.name.data = artist.name
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.genres.data = artist.genres
    form.facebook_link.data = artist.facebook_link
    form.website_link.data = artist.website_link
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description
    form.image_link.data = artist.image_link

    return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # taking values from the form submitted, and using it to update existing
  # artist record with ID <artist_id> using the new attributes
    error = False

    # Get data from the form
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    image_link = request.form['image_link']
    facebook_link = request.form['facebook_link']
    website_link = request.form['website_link']
    seeking_venue = True if 'seeking_venue' in request.form else False
    seeking_description = request.form['seeking_description']
    image_link = request.form['image_link']

    try:
        # getting artist by artist_id
        artist = Artist.query.get(artist_id)

        # updating old data with new
        artist.name = name
        artist.city = city
        artist.state = state
        artist.phone = phone
        artist.genres = genres
        artist.facebook_link = facebook_link
        artist.website_link = website_link
        artist.seeking_venue = seeking_venue
        artist.seeking_description = seeking_description
        artist.image_link = image_link

        db.session.commit()
    except Exception:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    # if failure
    if error:
        flash(
          "An error occurred. Artist " + name + " could not be updated."
        )
        abort(400)

      # if successful
    if not error:
        flash(
          "Artist" + name + "was successfully updated!"
        )

    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  # Getting data from db
    venue = Venue.query.filter(Venue.id == venue_id).first()

    # populating form with values from venue with ID <venue_id>
    # Getting values to replace old data
    form = VenueForm()
    form.name.data = venue.name
    form.city.data = venue.city
    form.state.data = venue.state
    form.address.data = venue.address
    form.phone.data = venue.phone
    form.genres.data = venue.genres
    form.facebook_link.data = venue.facebook_link
    form.website_link.data = venue.website_link
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description
    form.image_link.data = venue.image_link

    return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    error = False

    # Getting data from the form
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    facebook_link = request.form['facebook_link']
    website_link = request.form['website_link']
    seeking_talent = True if 'seeking_talent' in request.form else False
    seeking_description = request.form['seeking_description']
    image_link = request.form['image_link']

    try:
        # Getting data from db
        venue = Venue.query.get(venue_id)

        # taking values from the form submitted, and update existing
        # Update old data with new
        venue.name = name
        venue.city = city
        venue.state = state
        venue.address = address
        venue.phone = phone
        venue.genres = genres
        venue.facebook_link = facebook_link
        venue.website_link = website_link
        venue.seeking_talent = seeking_talent
        venue.seeking_description = seeking_description
        venue.image_link = image_link

        db.session.commit()
    except Exception:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

     # if failure
    if error:
        flash(
          "An error occurred. Venue " + name + "could not be updated."
        )
        abort(400)
      # if successful
    if not error:
        flash(
          "Venue" + name + "was successfully updated!"
        )

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
    error = False
    form = ArtistForm()



     # inserting form data as a new Venue record in the db
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    facebook_link = request.form['facebook_link']
    website_link = request.form['website_link']
    seeking_venue = True if 'seeking_venue' in request.form else False
    seeking_description = request.form['seeking_description']
    image_link = request.form['image_link']

    try:
         # modifying data to be the data object returned from db insertion
        artist = Artist(
          name=name,
          city=city,
          state=state,
          phone=phone,
          genres=genres,
          image_link=image_link,
          facebook_link=facebook_link,
          website_link=website_link,
          seeking_venue=seeking_venue,
          seeking_description=seeking_description,
        )

        db.session.add(artist)
        db.session.commit()
    except Exception:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    # if failure
    if error:
        flash("An error occurred. Artist " + name + " could not be listed.")
        abort(400)

        # if successful
    if not error:
        flash("Artist " + name + " was successfully listed!")

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  
    data = []

    # Get data from db
    shows = db.session.query(
          Venue.name,
          Artist.name,
          Artist.image_link,
          Show.venue_id,
          Show.artist_id,
          Show.start_time
        ).filter(Venue.id == Show.venue_id, Artist.id == Show.artist_id)

    # implementing data from the db into our display
    for show in shows:
        show = {'venue_name': Venue.name,
          'artist_name': Artist.name,
          'artist_image_link': Artist.image_link,
          'venue_id': Show.venue_id,
          'artist_id': Show.artist_id,
          'start_time': Show.start_time}
        data.append(show)

    return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form

  # inserting form data as a new Show record in the db

    error = False
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    start_time = request.form['start_time']

    try:
        # modifying data to be the data object returned from db insertion
        show = Show(
          artist_id=artist_id,
          venue_id=venue_id,
          start_time=start_time,
        )

        db.session.add(show)
        db.session.commit()
    except Exception:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    # If failure
    if error:
        flash(
          "An error occurred. Show could not be listed."
        )
        abort(400)
        # if successful
    if not error:
        flash(
          "Show was successfully listed!"
        )

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
