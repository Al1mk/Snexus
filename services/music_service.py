import os
import logging
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp
import requests
from config.config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
from utils.helpers import sanitize_filename, create_download_dir

logger = logging.getLogger(__name__)

class SpotifyDownloader:
    """Service for downloading music from Spotify"""
    
    def __init__(self):
        self.client_id = SPOTIFY_CLIENT_ID
        self.client_secret = SPOTIFY_CLIENT_SECRET
        self.sp = None
        self.initialize()
    
    def initialize(self):
        """Initialize Spotify client"""
        if self.client_id and self.client_secret:
            try:
                auth_manager = SpotifyClientCredentials(
                    client_id=self.client_id,
                    client_secret=self.client_secret
                )
                self.sp = spotipy.Spotify(auth_manager=auth_manager)
                logger.info("Spotify client initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing Spotify client: {e}")
        else:
            logger.warning("Spotify credentials not provided")
    
    def get_track_info(self, track_url):
        """Get track information from Spotify URL"""
        if not self.sp:
            logger.error("Spotify client not initialized")
            return None
        
        try:
            # Extract track ID from URL
            track_id = track_url.split('/')[-1].split('?')[0]
            
            # Get track info
            track = self.sp.track(track_id)
            
            track_info = {
                'id': track['id'],
                'name': track['name'],
                'artist': ', '.join([artist['name'] for artist in track['artists']]),
                'album': track['album']['name'],
                'duration_ms': track['duration_ms'],
                'release_date': track['album']['release_date'],
                'image_url': track['album']['images'][0]['url'] if track['album']['images'] else None,
                'preview_url': track['preview_url']
            }
            
            return track_info
        except Exception as e:
            logger.error(f"Error getting track info from Spotify: {e}")
            return None
    
    def get_playlist_info(self, playlist_url):
        """Get playlist information from Spotify URL"""
        if not self.sp:
            logger.error("Spotify client not initialized")
            return None
        
        try:
            # Extract playlist ID from URL
            playlist_id = playlist_url.split('/')[-1].split('?')[0]
            
            # Get playlist info
            playlist = self.sp.playlist(playlist_id)
            
            tracks = []
            for item in playlist['tracks']['items']:
                track = item['track']
                if track:
                    tracks.append({
                        'id': track['id'],
                        'name': track['name'],
                        'artist': ', '.join([artist['name'] for artist in track['artists']]),
                        'duration_ms': track['duration_ms'],
                        'preview_url': track['preview_url']
                    })
            
            playlist_info = {
                'id': playlist['id'],
                'name': playlist['name'],
                'description': playlist['description'],
                'owner': playlist['owner']['display_name'],
                'tracks_count': len(tracks),
                'tracks': tracks,
                'image_url': playlist['images'][0]['url'] if playlist['images'] else None
            }
            
            return playlist_info
        except Exception as e:
            logger.error(f"Error getting playlist info from Spotify: {e}")
            return None
    
    def download_track(self, track_info, output_dir):
        """Download track using YouTube as a source"""
        if not track_info:
            logger.error("No track info provided")
            return None
        
        try:
            # Create search query for YouTube
            search_query = f"{track_info['name']} {track_info['artist']}"
            
            # Use yt-dlp to search and download
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': os.path.join(output_dir, sanitize_filename(f"{track_info['artist']} - {track_info['name']}")),
                'quiet': True,
                'noplaylist': True,
                'default_search': 'ytsearch',
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Search for the track on YouTube
                info = ydl.extract_info(f"ytsearch:{search_query}", download=False)
                
                if not info or 'entries' not in info or not info['entries']:
                    logger.error(f"No YouTube results found for {search_query}")
                    return None
                
                # Get the first result
                video = info['entries'][0]
                
                # Download the track
                ydl.download([video['webpage_url']])
                
                # Return the file path
                file_path = f"{ydl_opts['outtmpl']}.mp3"
                
                return file_path
        except Exception as e:
            logger.error(f"Error downloading track from YouTube: {e}")
            return None
    
    def download_playlist(self, playlist_info, output_dir, max_tracks=10):
        """Download playlist tracks using YouTube as a source"""
        if not playlist_info or not playlist_info['tracks']:
            logger.error("No playlist info provided or empty playlist")
            return []
        
        downloaded_tracks = []
        
        # Limit the number of tracks to download
        tracks_to_download = playlist_info['tracks'][:max_tracks]
        
        for track in tracks_to_download:
            try:
                track_info = {
                    'name': track['name'],
                    'artist': track['artist'],
                    'duration_ms': track['duration_ms']
                }
                
                file_path = self.download_track(track_info, output_dir)
                
                if file_path:
                    downloaded_tracks.append({
                        'name': track['name'],
                        'artist': track['artist'],
                        'file_path': file_path
                    })
            except Exception as e:
                logger.error(f"Error downloading track {track['name']}: {e}")
                continue
        
        return downloaded_tracks


class AppleMusicDownloader:
    """Service for downloading music from Apple Music"""
    
    def __init__(self):
        pass
    
    def get_track_info(self, track_url):
        """Get track information from Apple Music URL"""
        try:
            # This is a placeholder as Apple Music doesn't have a public API
            # In a real implementation, you would need to use web scraping or a third-party service
            
            # For now, we'll extract basic info from the URL
            parts = track_url.split('/')
            
            # Try to extract track name from URL
            track_name = parts[-1].replace('-', ' ').title()
            
            # Try to extract artist name
            artist_name = "Unknown Artist"
            if len(parts) > 4:
                artist_name = parts[-2].replace('-', ' ').title()
            
            track_info = {
                'name': track_name,
                'artist': artist_name,
                'url': track_url
            }
            
            return track_info
        except Exception as e:
            logger.error(f"Error getting track info from Apple Music: {e}")
            return None
    
    def download_track(self, track_info, output_dir):
        """Download track using YouTube as a source"""
        if not track_info:
            logger.error("No track info provided")
            return None
        
        try:
            # Create search query for YouTube
            search_query = f"{track_info['name']} {track_info['artist']}"
            
            # Use yt-dlp to search and download
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': os.path.join(output_dir, sanitize_filename(f"{track_info['artist']} - {track_info['name']}")),
                'quiet': True,
                'noplaylist': True,
                'default_search': 'ytsearch',
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Search for the track on YouTube
                info = ydl.extract_info(f"ytsearch:{search_query}", download=False)
                
                if not info or 'entries' not in info or not info['entries']:
                    logger.error(f"No YouTube results found for {search_query}")
                    return None
                
                # Get the first result
                video = info['entries'][0]
                
                # Download the track
                ydl.download([video['webpage_url']])
                
                # Return the file path
                file_path = f"{ydl_opts['outtmpl']}.mp3"
                
                return file_path
        except Exception as e:
            logger.error(f"Error downloading track from YouTube: {e}")
            return None


class SoundCloudDownloader:
    """Service for downloading music from SoundCloud"""
    
    def __init__(self):
        pass
    
    def get_track_info(self, track_url):
        """Get track information from SoundCloud URL"""
        try:
            # Use yt-dlp to get track info
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(track_url, download=False)
                
                if not info:
                    logger.error(f"No info found for SoundCloud URL: {track_url}")
                    return None
                
                track_info = {
                    'id': info.get('id'),
                    'name': info.get('title'),
                    'artist': info.get('uploader'),
                    'duration': info.get('duration'),
                    'thumbnail': info.get('thumbnail'),
                    'url': track_url
                }
                
                return track_info
        except Exception as e:
            logger.error(f"Error getting track info from SoundCloud: {e}")
            return None
    
    def get_playlist_info(self, playlist_url):
        """Get playlist information from SoundCloud URL"""
        try:
            # Use yt-dlp to get playlist info
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'extract_flat': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(playlist_url, download=False)
                
                if not info or 'entries' not in info:
                    logger.error(f"No playlist info found for SoundCloud URL: {playlist_url}")
                    return None
                
                tracks = []
                for entry in info['entries']:
                    tracks.append({
                        'id': entry.get('id'),
                        'name': entry.get('title'),
                        'artist': entry.get('uploader'),
                        'url': entry.get('url')
                    })
                
                playlist_info = {
                    'id': info.get('id'),
                    'name': info.get('title'),
                    'uploader': info.get('uploader'),
                    'tracks_count': len(tracks),
                    'tracks': tracks,
                    'url': playlist_url
                }
                
                return playlist_info
        except Exception as e:
            logger.error(f"Error getting playlist info from SoundCloud: {e}")
            return None
    
    def download_track(self, track_url, output_dir):
        """Download track from SoundCloud"""
        try:
            # Get track info first
            track_info = self.get_track_info(track_url)
            
            if not track_info:
                logger.error(f"Could not get track info for {track_url}")
                return None
            
            # Use yt-dlp to download
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': os.path.join(output_dir, sanitize_filename(f"{track_info['artist']} - {track_info['name']}")),
                'quiet': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([track_url])
                
                # Return the file path
                file_path = f"{ydl_opts['outtmpl']}.mp3"
                
                return file_path
        except Exception as e:
            logger.error(f"Error downloading track from SoundCloud: {e}")
            return None
    
    def download_playlist(self, playlist_url, output_dir, max_tracks=10):
        """Download playlist tracks from SoundCloud"""
        try:
            # Get playlist info first
            playlist_info = self.get_playlist_info(playlist_url)
            
            if not playlist_info or not playlist_info['tracks']:
                logger.error(f"Could not get playlist info for {playlist_url}")
                return []
            
            downloaded_tracks = []
            
            # Limit the number of tracks to download
            tracks_to_download = playlist_info['tracks'][:max_tracks]
            
            for track in tracks_to_download:
                try:
                    file_path = self.download_track(track['url'], output_dir)
                    
                    if file_path:
                        downloaded_tracks.append({
                            'name': track['name'],
                            'artist': track['artist'],
                            'file_path': file_path
                        })
                except Exception as e:
                    logger.error(f"Error downloading track {track['name']}: {e}")
                    continue
            
            return downloaded_tracks
        except Exception as e:
            logger.error(f"Error downloading playlist from SoundCloud: {e}")
            return []


class MusicDownloadService:
    """Service for downloading music from various platforms"""
    
    def __init__(self):
        self.spotify_downloader = SpotifyDownloader()
        self.apple_music_downloader = AppleMusicDownloader()
        self.soundcloud_downloader = SoundCloudDownloader()
    
    def download_from_url(self, url, user_id, download_dir):
        """Download music from URL"""
        # Create user download directory
        user_download_dir = create_download_dir(download_dir, user_id)
        
        # Determine platform from URL
        if 'spotify.com' in url:
            return self.download_from_spotify(url, user_download_dir)
        elif 'music.apple.com' in url:
            return self.download_from_apple_music(url, user_download_dir)
        elif 'soundcloud.com' in url:
            return self.download_from_soundcloud(url, user_download_dir)
        else:
            logger.error(f"Unsupported music platform: {url}")
            return None
    
    def download_from_spotify(self, url, output_dir):
        """Download music from Spotify"""
        if 'playlist' in url:
            # It's a playlist
            playlist_info = self.spotify_downloader.get_playlist_info(url)
            if playlist_info:
                return {
                    'type': 'playlist',
                    'name': playlist_info['name'],
                    'tracks_count': playlist_info['tracks_count'],
                    'tracks': self.spotify_downloader.download_playlist(playlist_info, output_dir)
                }
        else:
            # It's a track
            track_info = self.spotify_downloader.get_track_info(url)
            if track_info:
                file_path = self.spotify_downloader.download_track(track_info, output_dir)
                if file_path:
                    return {
                        'type': 'track',
                        'name': track_info['name'],
                        'artist': track_info['artist'],
                        'file_path': file_path
                    }
        
        return None
    
    def download_from_apple_music(self, url, output_dir):
        """Download music from Apple Music"""
        track_info = self.apple_music_downloader.get_track_info(url)
        if track_info:
            file_path = self.apple_music_downloader.download_track(track_info, output_dir)
            if file_path:
                return {
                    'type': 'track',
                    'name': track_info['name'],
                    'artist': track_info['artist'],
                    'file_path': file_path
                }
        
        return None
    
    def download_from_soundcloud(self, url, output_dir):
        """Download music from SoundCloud"""
        if '/sets/' in url:
            # It's a playlist
            playlist_info = self.soundcloud_downloader.get_playlist_info(url)
            if playlist_info:
                downloaded_tracks = self.soundcloud_downloader.download_playlist(url, output_dir)
                return {
                    'type': 'playlist',
                    'name': playlist_info['name'],
                    'tracks_count': playlist_info['tracks_count'],
                    'tracks': downloaded_tracks
                }
        else:
            # It's a track
            file_path = self.soundcloud_downloader.download_track(url, output_dir)
            if file_path:
                track_info = self.soundcloud_downloader.get_track_info(url)
                return {
                    'type': 'track',
                    'name': track_info['name'],
                    'artist': track_info['artist'],
                    'file_path': file_path
                }
        
        return None
