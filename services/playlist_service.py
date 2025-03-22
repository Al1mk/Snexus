import os
import logging
from models.models import Playlist, Song
from utils.helpers import sanitize_filename

logger = logging.getLogger(__name__)

class PlaylistService:
    """Service for managing playlists"""
    
    def __init__(self, db):
        self.db = db
        self.playlist_model = Playlist(db)
        self.song_model = Song(db)
    
    def create_playlist(self, user_id, name, description=None):
        """Create a new playlist"""
        try:
            playlist_id = self.playlist_model.create_playlist(
                user_id=user_id,
                name=name,
                description=description
            )
            
            if playlist_id:
                return {
                    'id': playlist_id,
                    'name': name,
                    'description': description,
                    'user_id': user_id,
                    'songs_count': 0
                }
            
            return None
        except Exception as e:
            logger.error(f"Error creating playlist: {e}")
            return None
    
    def get_user_playlists(self, user_id):
        """Get all playlists for a user"""
        try:
            playlists = self.playlist_model.get_user_playlists(user_id)
            
            # Get song count for each playlist
            for playlist in playlists:
                songs = self.playlist_model.get_playlist_songs(playlist['id'])
                playlist['songs_count'] = len(songs)
            
            return playlists
        except Exception as e:
            logger.error(f"Error getting user playlists: {e}")
            return []
    
    def get_playlist(self, playlist_id):
        """Get playlist by ID"""
        try:
            playlist = self.playlist_model.get_playlist(playlist_id)
            
            if playlist:
                # Get songs in playlist
                songs = self.playlist_model.get_playlist_songs(playlist_id)
                playlist['songs'] = songs
                playlist['songs_count'] = len(songs)
            
            return playlist
        except Exception as e:
            logger.error(f"Error getting playlist: {e}")
            return None
    
    def add_song_to_playlist(self, playlist_id, song_id):
        """Add a song to a playlist"""
        try:
            # Check if song exists
            song = self.song_model.get_song(song_id)
            if not song:
                logger.error(f"Song not found: {song_id}")
                return False
            
            # Check if playlist exists
            playlist = self.playlist_model.get_playlist(playlist_id)
            if not playlist:
                logger.error(f"Playlist not found: {playlist_id}")
                return False
            
            # Check if song is already in playlist
            if self.playlist_model.is_song_in_playlist(playlist_id, song_id):
                logger.warning(f"Song {song_id} already in playlist {playlist_id}")
                return True
            
            # Add song to playlist
            return self.playlist_model.add_song_to_playlist(playlist_id, song_id)
        except Exception as e:
            logger.error(f"Error adding song to playlist: {e}")
            return False
    
    def remove_song_from_playlist(self, playlist_id, song_id):
        """Remove a song from a playlist"""
        try:
            # Check if song is in playlist
            if not self.playlist_model.is_song_in_playlist(playlist_id, song_id):
                logger.warning(f"Song {song_id} not in playlist {playlist_id}")
                return False
            
            # Remove song from playlist
            return self.playlist_model.remove_song_from_playlist(playlist_id, song_id)
        except Exception as e:
            logger.error(f"Error removing song from playlist: {e}")
            return False
    
    def delete_playlist(self, playlist_id, user_id):
        """Delete a playlist"""
        try:
            # Check if playlist exists and belongs to user
            playlist = self.playlist_model.get_playlist(playlist_id)
            if not playlist:
                logger.error(f"Playlist not found: {playlist_id}")
                return False
            
            if playlist['user_id'] != user_id:
                logger.error(f"Playlist {playlist_id} does not belong to user {user_id}")
                return False
            
            # Delete playlist
            return self.playlist_model.delete_playlist(playlist_id)
        except Exception as e:
            logger.error(f"Error deleting playlist: {e}")
            return False
    
    def create_playlist_from_songs(self, user_id, name, song_ids, description=None):
        """Create a new playlist with multiple songs"""
        try:
            # Create playlist
            playlist_id = self.playlist_model.create_playlist(
                user_id=user_id,
                name=name,
                description=description
            )
            
            if not playlist_id:
                logger.error("Failed to create playlist")
                return None
            
            # Add songs to playlist
            for song_id in song_ids:
                self.playlist_model.add_song_to_playlist(playlist_id, song_id)
            
            # Get created playlist
            playlist = self.playlist_model.get_playlist(playlist_id)
            if playlist:
                # Get songs in playlist
                songs = self.playlist_model.get_playlist_songs(playlist_id)
                playlist['songs'] = songs
                playlist['songs_count'] = len(songs)
            
            return playlist
        except Exception as e:
            logger.error(f"Error creating playlist from songs: {e}")
            return None
    
    def get_playlist_share_text(self, playlist_id):
        """Generate text for sharing a playlist"""
        try:
            playlist = self.get_playlist(playlist_id)
            
            if not playlist:
                logger.error(f"Playlist not found: {playlist_id}")
                return None
            
            # Generate share text
            share_text = f"🎵 *پلی‌لیست: {playlist['name']}*\n\n"
            
            if playlist['description']:
                share_text += f"{playlist['description']}\n\n"
            
            share_text += f"🔢 تعداد آهنگ‌ها: {playlist['songs_count']}\n\n"
            
            # Add songs
            if playlist['songs']:
                share_text += "📋 *لیست آهنگ‌ها:*\n"
                for i, song in enumerate(playlist['songs'], 1):
                    share_text += f"{i}. {song['title']} - {song['artist']}\n"
            
            share_text += "\n🤖 اشتراک‌گذاری شده توسط ربات Snexus"
            
            return share_text
        except Exception as e:
            logger.error(f"Error generating playlist share text: {e}")
            return None
    
    def export_playlist_as_file(self, playlist_id, output_dir):
        """Export playlist as a text file"""
        try:
            playlist = self.get_playlist(playlist_id)
            
            if not playlist:
                logger.error(f"Playlist not found: {playlist_id}")
                return None
            
            # Create file path
            file_name = f"{sanitize_filename(playlist['name'])}_playlist.txt"
            file_path = os.path.join(output_dir, file_name)
            
            # Generate content
            content = f"پلی‌لیست: {playlist['name']}\n"
            content += f"تاریخ ایجاد: {playlist['created_at']}\n"
            
            if playlist['description']:
                content += f"توضیحات: {playlist['description']}\n"
            
            content += f"تعداد آهنگ‌ها: {playlist['songs_count']}\n\n"
            
            # Add songs
            if playlist['songs']:
                content += "لیست آهنگ‌ها:\n"
                for i, song in enumerate(playlist['songs'], 1):
                    content += f"{i}. {song['title']} - {song['artist']}\n"
            
            content += "\nاشتراک‌گذاری شده توسط ربات Snexus"
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return file_path
        except Exception as e:
            logger.error(f"Error exporting playlist as file: {e}")
            return None
