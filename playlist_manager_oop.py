# TODO: aantal nummers in een afspeellijst laten zien

import sys
import spotipy
from spotipy.oauth2 import SpotifyOAuth

class PlaylistManager(object):
    def process(self):
        print("Setting up authentication with Spotify", file=sys.stderr)
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="587ff6be26ae46d6ac21f32f9475dff5",
                                                client_secret="b0dee9c93ca04bc5ae4e9c79db8d43d8",
                                                redirect_uri="http://google.com/",
                                                scope="user-read-playback-state playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public"))
        self.playlists = self.get_playlists()
        self.own_playlists = self.get_own_playlists()

        self.playlist_index = dict()
        self.song_index_list = dict()

        # Processing of the playlists
        for playlist in self.own_playlists:
            if playlist[0] != "Introkamp '22":
                print("Processing playlist:", playlist[0], file=sys.stderr)
                self.playlist_index[playlist[1]] = playlist[0]
                self.make_song_index_list(playlist[1])

        self.listener()


    def listener(self):
        print("Voer 1 in om je huidige nummer te checken.")
        print("Voer 2 in om je huidige nummer aan afspeellijst(en) toe te voegen.")
        for line in sys.stdin:
            if line.rstrip() == "1":
                self.check_current_for_playlists()
            elif line.rstrip() == "2":
                self.add_current_to_playlists()
            else:
                print("unknown character")
            print("Voer 1 in om je huidige nummer te checken.")
            print("Voer 2 in om je huidige nummer aan afspeellijst(en) toe te voegen.")

            
    def get_playlists(self):
        # Returns all playlists the user follows
        results = self.sp.current_user_playlists()

        playlists = results
        while results['next']:
            results = self.sp.next(results)
            playlists['items'].extend(results['items'])
        return playlists    


    def get_own_playlists(self):
        # Return owned/collaborative playlists from full list of playlists
        own_playlists = dict()
        index = 1
        for item in self.playlists['items']:
            print(item['collaborative'])
            if item['owner']['display_name'] == "Taede Meijer" or item['collaborative'] == True: # volgens mij doet item['collaborative'] het niet, later naar kijken
                own_playlists[item['name']] = item['id']

        result = []
        for key in own_playlists:
            result.append((key, own_playlists[key], index))
            index += 1
        return result    


    def get_playlist_tracks(self, playlist_id):
        # First line is not enough, as it returns 100 songs max at once
        results = self.sp.playlist_items(playlist_id)

        tracks = results['items']
        while results['next']:
            results = self.sp.next(results)
            tracks.extend(results['items'])
        return tracks


    def make_song_index_list(self, playlist):
        # Build a dictionary of songs with the playlists they're in
        temp = dict()
        songs = self.get_playlist_tracks(playlist)
        for song in songs:
            if song['track']['id'] in self.song_index_list:
                # Update the song index with new ID of new playlist
                self.song_index_list[song['track']['id']]['playlists'].add(playlist)

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

                self.song_index_list[song['track']['id']] = temp
                #print(self.song_index_list)
                temp = dict()
    

    def add_current_to_playlists(self):
        try:
            cur_playing = self.sp.current_user_playing_track()
            print(cur_playing["item"]["name"], "--", cur_playing['item']['album']['artists'][0]['name'])
            in_playlists = self.search_song(cur_playing['item']['id'])
            self.print_results(in_playlists)
        except TypeError:
            print("You are not currently playing any song.")
            in_playlists = []
        except KeyError:
            print("This song is not in any of your playlists.")
            in_playlists = []
        self.add_song(in_playlists, cur_playing)


    def check_current_for_playlists(self):
        try:
            cur_playing = self.sp.current_user_playing_track()
            print(cur_playing["item"]["name"], "--", cur_playing['item']['album']['artists'][0]['name'])
            result = self.search_song(cur_playing['item']['id'])
            if result:
                self.print_results(result)
        except TypeError:
            print("You are not currently playing any song.")
        except KeyError:
            print("This song is not in any of your playlists.")


    def add_song(self, in_playlists, song_to_add):
        # Print alle afspeellijsten uit met index er bij
        for playlist in self.own_playlists:
            if in_playlists:
                if playlist[0] in in_playlists:
                    print(playlist[2], "-", playlist[0], "\t[zit het nummer al in]")
                else:
                    print(playlist[2], "-", playlist[0])
            else:
                print(playlist[2], "-", playlist[0])
        
        # Vraag om indexen van afspeellijsten waar het nummer aan toegevoegd moet worden
        to_add = input("Geef de nummers van afspeellijsten, gebruik '-1' voor exit: ")
        if '-1' in to_add:
            print("Exiting...")
            return -1

        for playlist in self.own_playlists:
            if str(playlist[2]) in to_add.split():
                #print(playlist[1], song_id)
                self.sp.user_playlist_add_tracks("Taede Meijer", playlist[1], [song_to_add['item']['id']])

                # Update the song_index_list with the new playlist
                # Crashes if song not in song_index_list !!
                try:
                    self.song_index_list[song_to_add['item']['id']]['playlists'].add(playlist[1])
                    print("Adding song '%s' to playlist: %s" % (self.song_index_list[song_to_add['item']['id']]['name'], playlist[0]))
                except KeyError:
                    self.song_index_list[song_to_add['item']['id']] = dict()
                    self.song_index_list[song_to_add['item']['id']]['playlists'] = {playlist[1]}
                    # name = ''
                    # artists = []
                    # print("Dit nummer stond niet eerst in 1 van de afspeellijsten(!)", file=sys.stderr)
                    print("Adding song '%s' to playlist: %s" % (self.song_index_list[song_to_add['item']['id']]['name'], playlist[0]))


    def search_song(self, id):
        in_playlists = []
        try:
            results = self.song_index_list[id]['playlists']
        except KeyError:
            print("Dit nummer staat niet in 1 van je afspeellijsten")
            return None
        for result in results:
            in_playlists.append(self.playlist_index[result])
        in_playlists.sort()
        print("Dit nummer zit in je volgende afspeellijsten:", end="\n\n")
        return in_playlists


    def print_results(self, playlists):
        for playlist in playlists:
            print("\t", playlist)

if __name__ == "__main__":
    s = PlaylistManager()
    s.process()
