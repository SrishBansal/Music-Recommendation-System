import gradio as gr
import sqlite3
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import random

# ✅ Load and clean data
df = pd.read_csv("ex.csv", encoding='unicode_escape')
df = df.rename(columns={
    'Song-Name': 'track_name',
    'Singer/Artists': 'artist_name',
    'Genre': 'genre'
})
df = df[['track_name', 'artist_name', 'genre']].dropna().drop_duplicates()
df.reset_index(drop=True, inplace=True)

# ✅ Setup SQLite
conn = sqlite3.connect("music_recommendation.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS playlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    track_name TEXT,
    artist_name TEXT
)
''')
conn.commit()

# ✅ TF-IDF similarity
tfidf = TfidfVectorizer()
tfidf_matrix = tfidf.fit_transform(df['genre'])
cosine_sim = cosine_similarity(tfidf_matrix)

# ✅ Recommend by song (with fresh shuffle each time)
def recommend_by_song(song_title, top_n=5, reset=False):
    if song_title not in df['track_name'].values:
        return "<div style='color:red;'>❌ Song not found.</div>", gr.update(choices=[])

    idx = df[df['track_name'] == song_title].index[0]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:]  # skip itself
    random.shuffle(sim_scores)

    recs = [(df.iloc[i]['track_name'], df.iloc[i]['artist_name']) for i, _ in sim_scores[:top_n]]

    table_html = "<table class='box'><tr><th>Song</th><th>Artist</th></tr>"
    for song, artist in recs:
        table_html += f"<tr><td>{song}</td><td>{artist}</td></tr>"
    table_html += "</table>"

    dropdown_choices = [f"{song} - {artist}" for song, artist in recs]
    return table_html, gr.update(choices=dropdown_choices)

# ✅ Recommend by artist (shuffled)
def recommend_by_artist(artist_name, reset=False):
    songs = df[df['artist_name'].str.contains(artist_name, case=False, na=False)][['track_name', 'artist_name']].sample(frac=1)
    if songs.empty:
        return "<div style='color:red;'>❌ No songs found for this artist.</div>", gr.update(choices=[])

    recs = songs.head(5).values.tolist()
    table_html = "<table class='box'><tr><th>Song</th><th>Artist</th></tr>"
    for song, artist in recs:
        table_html += f"<tr><td>{song}</td><td>{artist}</td></tr>"
    table_html += "</table>"

    dropdown_choices = [f"{song} - {artist}" for song, artist in recs]
    return table_html, gr.update(choices=dropdown_choices)

# ✅ Add song to playlist
def add_to_playlist(song_input):
    if " - " not in song_input:
        return "❗ Use format: Song - Artist"
    track = song_input.split(" - ")[0].strip()
    song = df[df['track_name'] == track]
    if not song.empty:
        artist = song.iloc[0]['artist_name']
        cursor.execute("SELECT * FROM playlist WHERE track_name=? AND artist_name=?", (track, artist))
        if cursor.fetchone():
            return f"⚠️ '{track}' by {artist} is already in the playlist."
        else:
            cursor.execute("INSERT INTO playlist (track_name, artist_name) VALUES (?, ?)", (track, artist))
            conn.commit()
            return f"✅ '{track}' by {artist} added to playlist."
    return "❌ Song not found."

# ✅ View playlist
def view_playlist():
    cursor.execute("SELECT track_name, artist_name FROM playlist")
    rows = cursor.fetchall()
    if not rows:
        return "<div style='color:gray;'>📭 Playlist is empty.</div>"

    table = "<div class='box'><h4>📋 Your Playlist</h4><table><tr><th>Song</th><th>Artist</th></tr>"
    for track, artist in rows:
        table += f"<tr><td>{track}</td><td>{artist}</td></tr>"
    table += "</table></div>"
    return table

# ✅ Custom CSS
custom_css = """
body {
    background: linear-gradient(135deg, #2c3e50, #8e44ad);
    background-size: cover;
    font-family: 'Segoe UI', sans-serif;
    color: #fff;
}
.box {
    background: rgba(255, 255, 255, 0.1);
    padding: 15px;
    border-radius: 12px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.4);
    margin-top: 15px;
    color: #fff;
}
table {
    width: 100%;
    border-collapse: collapse;
    font-size: 16px;
}
th, td {
    padding: 10px;
    border-bottom: 1px solid #ddd;
}
th {
    background-color: #f39c12;
    color: white;
}
"""

# ✅ Gradio App
with gr.Blocks(css=custom_css) as demo:
    gr.Markdown("""
    <div style='text-align:center;'>
    <h1 style='color:#ffeb3b;'>🎵 <u>Music Recommendation System</u> 🎵</h1>
    <p style='font-size:18px;'>Pick a song or artist, discover related tracks, and build your playlist!</p>
    </div>
    """)

    with gr.Row():
        song_input = gr.Dropdown(choices=df['track_name'].unique().tolist(), label="🎧 Pick a Song")
        song_btn = gr.Button("🎼 Get Recommendations")
        refresh_btn = gr.Button("🔁 Refresh Songs")

    song_recs_display = gr.HTML()
    song_recs_dropdown = gr.Dropdown(label="🎯 Select a Recommended Song")
    add_song_btn = gr.Button("➕ Add to Playlist")
    song_status = gr.Textbox(label="Status")

    with gr.Row():
        artist_input = gr.Dropdown(choices=sorted(df['artist_name'].unique()), label="🎤 Select Artist")
        artist_btn = gr.Button("🎶 Show Songs by Artist")
        artist_refresh_btn = gr.Button("🔁 Refresh Artist Recs")

    artist_recs_display = gr.HTML()
    artist_recs_dropdown = gr.Dropdown(label="🎶 Select Artist Song")
    add_artist_btn = gr.Button("➕ Add to Playlist")
    artist_status = gr.Textbox(label="Status")

    playlist_btn = gr.Button("📂 View Playlist")
    playlist_output = gr.HTML()

    song_btn.click(fn=recommend_by_song, inputs=song_input, outputs=[song_recs_display, song_recs_dropdown])
    refresh_btn.click(fn=lambda s: recommend_by_song(s, reset=True), inputs=song_input, outputs=[song_recs_display, song_recs_dropdown])
    add_song_btn.click(fn=add_to_playlist, inputs=song_recs_dropdown, outputs=song_status)

    artist_btn.click(fn=recommend_by_artist, inputs=artist_input, outputs=[artist_recs_display, artist_recs_dropdown])
    artist_refresh_btn.click(fn=lambda a: recommend_by_artist(a, reset=True), inputs=artist_input, outputs=[artist_recs_display, artist_recs_dropdown])
    add_artist_btn.click(fn=add_to_playlist, inputs=artist_recs_dropdown, outputs=artist_status)

    playlist_btn.click(fn=view_playlist, outputs=playlist_output)

demo.launch(share=True)