from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import fields, ValidationError

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:654U7jsv@localhost/playlist'
db = SQLAlchemy(app)
ma = Marshmallow(app)

class Song(db.Model):
    __tablename__ = 'songs'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    artist = db.Column(db.String(255), nullable=False)
    genre = db.Column(db.String(255), nullable=False)

class SongSchema(ma.Schema):
    title = fields.String(required=True)
    artist = fields.String(required=True)
    genre = fields.String(required=True)

    class Meta:
        fields = ('title', 'artist', 'genre', 'id')

song_schema = SongSchema()
songs_schema = SongSchema(many=True)


class Playlist(db.Model):
    __tablename__ = 'playlists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)

class PlaylistSchema(ma.Schema):
    name = fields.String(required=True)
    description = fields.String(required=True)

    class Meta:
        fields = ('name', 'description', 'id')

playlist_schema = PlaylistSchema()
playlists_schema = PlaylistSchema(many=True)


class PlaylistSong(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlists.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('songs.id'), nullable=False)


class PlaylistSongSchema(ma.Schema):
    playlist_id = fields.Integer(required=True)
    song_id = fields.Integer(required=True)

    class Meta:
        fields = ('playlist_id', 'song_id')

playlist_song_schema = PlaylistSongSchema()
playlist_song_schemas = PlaylistSongSchema(many=True)

#Playlist Endpoints

@app.route('/playlist/create', methods=["POST"])
def add_playlist():
    try:
        playlist_data = playlist_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    new_playlist = Playlist(name = playlist_data['name'], description = playlist_data['description'])
    db.session.add(new_playlist)
    db.session.commit()

    return jsonify({'message': "New playlist added successfully"}), 201


@app.route('/playlist/<playlist_id>', methods=["GET"])
def get_playlist(playlist_id):
    playlist = Playlist.query.get(playlist_id)
    if not playlist:
        return jsonify({'message': 'Playlist not found'}), 404
    return playlist_schema.jsonify(playlist)


@app.route('/playlist/update/<playlist_id>', methods=["PUT"])
def update_playlist(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    try:
        playlist_data = playlist_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    playlist.name = playlist_data['name']
    playlist.description = playlist_data['description']
    db.session.commit()

    return jsonify({'message': 'Playlist updated successfully'}), 200


@app.route('/playlist/delete/<id>', methods=["DELETE"])
def delete_playlist(id):
    playlist = Playlist.query.get_or_404(id)
    db.session.delete(playlist)
    db.session.commit()

    return jsonify({"message": 'Playlist deleted successfully'}), 200



#Song Endpoints 

@app.route('/playlist/<playlist_id>/add_song/<song_id>', methods=['POST'])
def add_song(playlist_id, song_id):
    try:
        song_data = song_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    new_song = Song(id=song_id, title=song_data['title'], artist=song_data['artist'], genre=song_data['genre'])
    db.session.add(new_song)
    db.session.commit()
    
    playlist_song = PlaylistSong(playlist_id=playlist_id, song_id=song_id)
    db.session.add(playlist_song)
    db.session.commit()

    return jsonify({'message': "New song added successfully to the playlist"}), 201



@app.route('/playlist/<playlist_id>/remove_song/<song_id>', methods = ['DELETE'])
def delete_song(playlist_id, song_id):
    playlist_song = PlaylistSong.query.filter_by(playlist_id=playlist_id, song_id=song_id).first_or_404()
    db.session.delete(playlist_song)
    db.session.commit()

    return jsonify({"message": 'Song removed from playlist successfully'}), 200

@app.route('/playlist/search/<title>', methods=['GET'])
def binary_search(arr, target):
    low = 0
    high = len(arr) - 1

    while low <= high:
        mid = (low + high) // 2
        if arr[mid]['title'] == target:
            return arr[mid]
        elif arr[mid]['title'] < target:
            low = mid + 1
        else:
            high = mid - 1

    return None

def search_songs():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "No search query provided"}), 400

    songs = Song.query.order_by(Song.title).all()
    songs_list = songs_schema.dump(songs)

    result = binary_search(songs_list, query)
    if result:
        return jsonify(result)
    else:
        return jsonify({"message": "No songs found with that title"}), 404
    