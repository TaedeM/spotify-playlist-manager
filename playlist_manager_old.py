# Todo: make dictionary of keys mapped to names and playlists they are in - DONE
# Todo: Fix > 100 playlist size - DONE
# Todo: Fix not all playlists show - DONE
# Todo: Selection what you want to do, 1 or 2, 1 = lookup, 2 = add to playlists - DONE
# Todo: add a song to playlists - DONE
# Todo: after adding a song to a playlist, update the song_index dictionary
 

import sys
import spotipy
from spotipy.oauth2 import SpotifyOAuth


def get_own_playlists(playlists):
    own_playlists = dict()
    index = 1
    for item in playlists['items']:
        if item['owner']['display_name'] == "Taede Meijer":
            own_playlists[item['name']] = item['id']
    result = []
    for key in own_playlists:
        result.append((key, own_playlists[key], index))
        index += 1
    return result


def get_playlists(sp):
    # First line is not enough as it returns 50 playlists max at once
    results = sp.current_user_playlists()
    playlists = results
    while results['next']:
        results = sp.next(results)
        playlists['items'].extend(results['items'])
    return playlists


def get_playlist_tracks(playlist_id, sp):
    # This first line is not enough, as it returns 100 songs max at once
    results = sp.playlist_items(playlist_id)
    tracks = results['items']
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    return tracks


def make_song_index(playlist, song_index, sp):
    temp = dict()
    songs = get_playlist_tracks(playlist, sp)
    for song in songs:
        if song['track']['id'] in song_index:
            # Update the playlists list with new ID
            song_index[song['track']['id']]['playlists'].add(playlist)

        else:
            # add song name to song index
            temp['name'] = song['track']['name']
            artists = []

            # Try except because podcasts dont have an artist tag (some podcasts are songs)
            try:
                for artist in song['track']['artists']:
                    artists.append(artist['name'])
                temp['artist(s)'] = artists
            except KeyError:
                pass
            
            # add the playlist ID the song is in
            temp['playlists'] = {playlist}

            song_index[song['track']['id']] = temp
            temp = dict()

    #print(song_index)
    return song_index


def search_song(song_index, id, playlist_index):
    playlists = []
    songname = song_index[id]['name']
    results = song_index[id]['playlists']
    for result in results:
        playlists.append(playlist_index[result])
    playlists.sort()
    print("Dit nummer zit in je volgende afspeellijsten:", end="\n\n")
    return playlists


def print_results(playlists):
    for playlist in playlists:
        print("\t", playlist)


def selection():
    print("Voer 1 in om een nummer handmatig te checken")
    print("Voer 2 in om het nummer dat je afspeelt te checken")
    print("Voer 3 in om een nummer toe te voegen aan afspeellijsten")



def option1(song_index, playlist_index):
    new_input = input("Enter new song URL: ")
    song_id = new_input[31:53]
    print()
    print(song_index[song_id]['name'], song_index[song_id]['artist(s)'])
    result = search_song(song_index, song_id, playlist_index)
    print_results(result)
    print("\n\t----------------")


def option2(song_index_list, playlist_index, sp):
    try:
        cur_playing = sp.current_user_playing_track()
        result = search_song(song_index_list, cur_playing['item']['id'], playlist_index)
        print_results(result)
    except:
        print("You are not currently playing a song.")

    

def option3(song_index_list, playlist_index, own_playlists, sp):
    print("functieieiieieieieiieieieieieiei")
    new_input = input("Geef de url van het nummer dat je wil toevoegen: ")
    song_id = new_input[31:53]
    print()
    try:
        print(song_index_list[song_id]['name'], song_index_list[song_id]['artist(s)'])
        result = search_song(song_index_list, song_id, playlist_index)
        print_results(result)
    except KeyError:
        print('Dit nummer zit niet in één van je afspeellijsten')
        return -1

    # Print alle afspeellijsten uit met index 
    for playlist in own_playlists:
        if result:
            if playlist[0] in result:
                print(playlist[2], "-", playlist[0], "\t[zit het nummer al in]")
            else:
                print(playlist[2], "-", playlist[0])
        else:
            print(playlist[2], "-", playlist[0])
    
    # Vraag om indexen van afspeellijsten
    to_add = input("Geef de nummers van afspeellijsten: ")

    for playlist in own_playlists:
        if str(playlist[2]) in to_add.split():
            #print(playlist[1], song_id)
            sp.user_playlist_add_tracks("Taede Meijer", playlist[1], [song_id])

            # Update the song_index_list with the new playlist
            song_index_list[song_id]['playlists'].add(playlist[1])
            print("Adding song '%s' to playlist: %s" % (song_index_list[song_id]['name'], playlist[0]))


def main():
    print("Setting up authentication with Spotify", file=sys.stderr)
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="587ff6be26ae46d6ac21f32f9475dff5",
                                                client_secret="b0dee9c93ca04bc5ae4e9c79db8d43d8",
                                                redirect_uri="http://google.com/",
                                                scope="user-read-playback-state playlist-read-private playlist-modify-private playlist-modify-public"))

    song_index_list = dict()
    playlist_index = dict()
    print("Authentication complete", file=sys.stderr, end="\n\n")

    own_playlists = get_own_playlists(get_playlists(sp))

    # Start the processing of the playlists
    for playlist in own_playlists:
        print("Processing playlist:", playlist[0], file=sys.stderr)
        playlist_index[playlist[1]] = playlist[0]
        song_index_list = make_song_index(playlist[1], song_index_list, sp)

    # Look what song the user is currently playing. This will be used as first input
    try:
        cur_playing = sp.current_user_playing_track()
    except:
        pass

    print()
    if cur_playing:
        print("---- RESULTATEN ----", end="\n\n")
        try:
            print("NU AAN HET AFSPELEN:", song_index_list[cur_playing['item']['id']]['name'], "--", ", ".join(song_index_list[cur_playing['item']['id']]['artist(s)']), end="\n\n")
            result = search_song(song_index_list, cur_playing['item']['id'], playlist_index)
            print_results(result)
        except KeyError:
            print("NU AAN HET AFSPELEN:", cur_playing["item"]["name"], "--", cur_playing['item']['album']['artists'][0]['name'])
            print("Dit nummer zit niet in 1 van je afspeellijsten")
    else:
        print("You are not currently playing a track on Spotify")
    print("\n-- selection --")
    selection()
    print("\nSelectie: ", end="")

    for line in sys.stdin:
        line = line.rstrip()
        if line == "1":
            option1(song_index_list, playlist_index)
        if line =="2":
            option2(song_index_list, playlist_index, sp)
        if line == "3":
            option3(song_index_list, playlist_index, own_playlists, sp)

        print()
        selection()

# https://open.spotify.com/track/5hM5arv9KDbCHS0k9uqwjr?si=30b55314cc424508
if __name__ == "__main__":
    main()
