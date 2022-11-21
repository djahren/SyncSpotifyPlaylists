from time import sleep
import spotipy
import yaml
from spotipy.oauth2 import SpotifyOAuth


def get_playlist_tracks(playlist_id):
    playlist_contents = []
    offset = 0
    while True:
        results = sp.playlist_tracks(playlist_id, offset=offset)
        offset += 100
        for track in results['items']:
            playlist_contents.append(track['track']['id'])
        if results['next'] is None:
            break
    return playlist_contents


def get_unique_tracks(input_list, compare_list=[]):
    unique_list = []
    for item in input_list:
        if item not in unique_list and item not in compare_list:
            unique_list.append(item)
    return unique_list


def track_pretty_print(track):
    try:
        return f'{track["artists"][0]["name"]} - {track["name"]}'
    except Exception:
        return track["name"]


config = {}
with open("config/config.yaml", "r") as c:
    config = yaml.load(c, Loader=yaml.Loader)

playlists = config['playlists']
sync_playlists = config['sync']

scope = "playlist-modify-private playlist-modify-public"
auth_manager = SpotifyOAuth(
    scope=scope,
    redirect_uri="http://localhost:8080",
    client_id=config["client"]["id"],
    client_secret=config["client"]["secret"]
)
sp = spotipy.Spotify(auth_manager=auth_manager)

while True:
    for sync in sync_playlists:
        src_playlist_id = playlists[sync['src']]
        if not src_playlist_id.startswith("http"):
            src_playlist_id = f"spotify:playlist:{playlists[sync['src']]}"
        dst_playlist_id = playlists[sync['dst']]
        if not dst_playlist_id.startswith("http"):
            dst_playlist_id = f"spotify:playlist:{playlists[sync['dst']]}"

        src_playlist_tracks = get_playlist_tracks(src_playlist_id)
        dst_playlist_tracks = get_playlist_tracks(dst_playlist_id)

        tracks_to_add = get_unique_tracks(src_playlist_tracks, dst_playlist_tracks)
        for track_id in tracks_to_add:
            try:
                print(track_pretty_print(sp.track(track_id=track_id)))
                sleep(0.2)
            except Exception:
                print(f"Can't find track_id: {track_id}")
                tracks_to_add.remove(track_id)

        if len(tracks_to_add) > 0:
            offset = 0
            print(f"Adding tracks from {sync['src']} to {sync['dst']}")
            print(tracks_to_add)
            while tracks_to_add[offset:offset + 10]:
                sp.playlist_add_items(
                    playlist_id=dst_playlist_id,
                    items=tracks_to_add[offset:offset + 10]
                )
                offset += 10
                sleep(0.2)
        else:
            print(f"No tracks to add to {sync['dst']}")
        sleep(0.2)
    sleep(int(config["run_every"]) * 60)
