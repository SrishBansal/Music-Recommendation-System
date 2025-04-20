import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import time
import random
import os

# Use environment variables for credentials (more secure)
client_id = os.environ.get('SPOTIFY_CLIENT_ID', 'e924aec6a43e4b2482eddcd9d2a54d2a')
client_secret = os.environ.get('SPOTIFY_CLIENT_SECRET', 'f2ef1a5c234b40dc98bf277e2411aea6')

# Configure better error handling and logging
def setup_spotify_client(retries=3):
    for attempt in range(retries):
        try:
            auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
            sp = spotipy.Spotify(auth_manager=auth_manager, requests_timeout=15)
            # Test the connection with a simple request
            sp.search(q='test', limit=1)
            print("✅ Successfully connected to Spotify API")
            return sp
        except Exception as e:
            print(f"Connection attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                wait_time = 2 ** attempt + random.uniform(1, 3)
                print(f"Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
            else:
                print("❌ Failed to connect to Spotify API after multiple attempts")
                raise

# Improved search function with better query construction
def fetch_track_info_with_retry(sp, track_name, artist_name, retries=3, initial_delay=1):
    # Try different query formats and increase the number of search results returned
    queries = [
        f"track:{track_name} artist:{artist_name}",  # Most specific format
        f"{track_name} {artist_name}",                # Simple format (fallback)
        f"track:{track_name}",                        # Try with just track name
        f"artist:{artist_name}"                       # Try with just artist name
    ]
    
    for query in queries:
        attempt = 0
        while attempt < retries:
            try:
                print(f"Searching with query: {query}")
                results = sp.search(q=query, type='track', limit=5)  # Increase to return 5 results
                items = results['tracks']['items']
                if items:
                    for track in items:
                        if track['preview_url']:  # Ensure the track has a preview URL
                            return track['preview_url'], track['external_urls']['spotify'], track['name'], track['artists'][0]['name']
                    print(f"No preview found for any track in the results")
                    break  # Move on to next query or track
                else:
                    print(f"No results found for query: {query}")
                    break  # Try next query format
            except spotipy.exceptions.SpotifyException as e:
                if e.http_status == 429:  # Rate limiting
                    retry_after = int(e.headers.get('Retry-After', 1)) if hasattr(e, 'headers') else initial_delay
                    print(f"Rate limited. Waiting for {retry_after} seconds...")
                    time.sleep(retry_after + random.uniform(0, 1))
                else:
                    print(f"Spotify API error: {e}")
                    attempt += 1
                    wait_time = initial_delay * (2 ** attempt) + random.uniform(0, 1)
                    print(f"Retrying in {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
            except Exception as e:
                print(f"Unexpected error: {e}")
                attempt += 1
                wait_time = initial_delay * (2 ** attempt) + random.uniform(0, 1)
                print(f"Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
    
    return None, None, None, None

def main():
    try:
        # Initialize Spotify client
        sp = setup_spotify_client()
        
        # Load the CSV with proper error handling
        try:
            df = pd.read_csv("ex.csv", encoding='unicode_escape')
            print(f"✅ Loaded CSV with {len(df)} rows")
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            return
        
        # Rename columns if needed
        if 'Song-Name' in df.columns:
            df = df.rename(columns={
                'Song-Name': 'track_name',
                'Singer/Artists': 'artist_name',
                'Genre': 'genre'
            })
        
        # Add columns for preview and full Spotify URL
        df['preview_url'] = None
        df['spotify_track_url'] = None
        df['matched_track_name'] = None
        df['matched_artist_name'] = None
        
        # Process in smaller batches to avoid rate limiting
        batch_size = 10
        total_rows = len(df)
        
        for start_idx in range(0, total_rows, batch_size):
            end_idx = min(start_idx + batch_size, total_rows)
            print(f"\nProcessing batch {start_idx//batch_size + 1}: rows {start_idx+1} to {end_idx}")
            
            for i in range(start_idx, end_idx):
                row = df.iloc[i]
                track_name = row['track_name']
                artist_name = row['artist_name']
                
                print(f"[{i+1}/{total_rows}] Searching for: {track_name} by {artist_name}")
                preview_url, spotify_url, matched_track, matched_artist = fetch_track_info_with_retry(
                    sp, track_name, artist_name
                )
                
                df.at[i, 'preview_url'] = preview_url
                df.at[i, 'spotify_track_url'] = spotify_url
                df.at[i, 'matched_track_name'] = matched_track
                df.at[i, 'matched_artist_name'] = matched_artist
                
                status = "✅" if preview_url else "❌"
                print(f"[{i+1}/{total_rows}] {status} {track_name} - {artist_name}")
                
                # Save progress periodically
                if (i + 1) % 20 == 0 or i == total_rows - 1:
                    df.to_csv("ex_with_previews_progress.csv", index=False)
                    print(f"💾 Progress saved at row {i+1}")
                
                # Respect rate limits with a small delay between requests
                time.sleep(0.8 + random.uniform(0, 0.4))
            
            # Longer pause between batches
            if end_idx < total_rows:
                wait_time = 5 + random.uniform(1, 3)
                print(f"Pausing between batches for {wait_time:.2f} seconds...")
                time.sleep(wait_time)
        
        # Save final result
        df.to_csv("ex_with_previews.csv", index=False)
        print("\n✅ Process completed successfully!")
        print(f"Preview & track URLs saved to ex_with_previews.csv")
        print(f"Success rate: {df['preview_url'].notna().sum()}/{total_rows} tracks found ({df['preview_url'].notna().mean()*100:.1f}%)")
        
    except Exception as e:
        print(f"❌ Program error: {e}")

if __name__ == "__main__":
    main()
