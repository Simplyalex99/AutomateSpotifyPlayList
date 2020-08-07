import json
import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import requests
import youtube_dl
from credentials import Spotify_user_id  ,Spotify_secret 
class CreatePlayList:
    def __init__(self):
        self.user_id = Spotify_user_id
        self.spotify_token = Spotify_secret
        self.youtube_client = self.get_youtube_client()
        self.all_song_info = {}
    def get_youtube_client(self):
         # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "client_secret.json"

        # Get credentials and create an API client
        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_console()

        # from the Youtube DATA API
        youtube_client = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)

        return youtube_client  
    def get_liked_videos(self):
        request = self.youtube_client.videos().list(
            part="snippet,contentDetails,statistics",
            myRating="like"
        )
        response = request.execute() 
         # collect each video and get important information
        for item in response["items"]:
            video_title = item["snippet"]["title"]
            youtube_url = "https://www.youtube.com/watch?v={}".format(
                item["id"])

            # use youtube_dl to collect the song name & artist name
            video = youtube_dl.YoutubeDL({}).extract_info(
                youtube_url, download=False)
            song_name = video["track"]
            artist = video["artist"]

            if song_name is not None and artist is not None:
                # save all important info and skip any missing song and artist
                self.all_song_info[video_title] = {
                    "youtube_url": youtube_url,
                    "song_name": song_name,
                    "artist": artist,

                    # add the uri, easy to get song to put into playlist
                    "spotify_uri": self.get_spotify_uri(song_name, artist)

                }   
    def create_spotify_playlist(self):
        body = json.dumps(
         "name":"Youtube MusicPlaylist",
         "description":"From Music playlist",
         "public": True


        )
        baseurl = "https://api.spotify.com/v1"
        endPoint = "/users/{self.user_id}/playlists"
        url = baseurl + endPoint
        response = requests.post(
            url,
            data=request.body,
            headers = {
                "Content-Type": "applications/json",
                "Authorization": "Bearer {self.spotify_token}"


            }

        )
        response_json = response.json()
        #playlist id
        return response_json["id"]

        pass
    def get_url(self,song_name,artist):
        baseurl = "https://api.spotify.com/v1"
        endPoint = "/https://api.spotify.com/v1/search?query=track%3A{song_name}+artist%3A{artist}&type=track&offset=0&limit=20"
        url = baseurl+endPoint
        response = requests.get(
            url,
            headers = {
                "Content-Type": "applications/json",
                "Authorization": "Bearer {self.spotify_token}"
            }
        )
        response_json = response.json()
        songs = response_json["tracks"]["items"]
        #only uses first song:
        urlToReturn = songs[0]["uri"]
        return urlToReturn
        
    def add_song_to_playlist(self):
         # populate dictionary with our liked songs
        self.get_liked_videos()

        # collect all of uri
        uris = [info["spotify_uri"]
                for song, info in self.all_song_info.items()]

        # create a new playlist
        playlist_id = self.create_playlist()

        # add all songs into new playlist
        request_data = json.dumps(uris)

        url = "https://api.spotify.com/v1/playlists/{}/tracks".format(
            playlist_id)

        response = requests.post(
            url,
            data=request_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {self.spotify_token}"
            }
        )


        