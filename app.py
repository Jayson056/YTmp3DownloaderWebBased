from flask import Flask, render_template, request, Response, redirect, url_for, send_from_directory
import yt_dlp
import re
import os
import tempfile

app = Flask(__name__)

# Directory to store cookies and ensure `uploads` exists
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Path for cookies file, auto-generated or provided
COOKIES_PATH = os.path.join(UPLOAD_FOLDER, 'cookies.txt')

def download_file(link, format='mp3', cookies_path=None):
    """Download YouTube video/audio and yield data in chunks from a temporary file."""
    try:
        print("Starting download process...")

        # Check if the link is a valid YouTube URL
        if re.match(r'^(https?://)?(www\.)?(youtube\.com|youtu\.be|music\.youtube\.com)/.+', link):
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]' if format == 'mp3' else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
                'quiet': True,
                'cookiefile': cookies_path,  # Use auto-generated cookies.txt path
                'outtmpl': tempfile.mktemp(suffix=f".{format}")  # Temporary file path
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print("Extracting info and downloading...")
                
                # Attempt extraction to verify cookies
                try:
                    info = ydl.extract_info(link, download=False)
                    print("Cookies are valid. Video info extracted.")
                except yt_dlp.utils.DownloadError as e:
                    print("Cookies failed verification:", e)
                    return "Cookies are invalid. Please check.", 400

                # Download the video/audio
                info = ydl.extract_info(link)
                filename = ydl.prepare_filename(info)
                print("Download complete:", filename)

                def generate(file_path):
                    with open(file_path, 'rb') as f:
                        while chunk := f.read(8192):
                            yield chunk
                    os.remove(file_path)  # Clean up after streaming

                mimetype = 'audio/mpeg' if format == 'mp3' else 'video/mp4'
                return Response(generate(filename),
                                mimetype=mimetype,
                                headers={'Content-Disposition': f'attachment; filename="{info["title"]}.{format}"'})

        else:
            print("Unsupported link:", link)
            return "Unsupported Link", 400

    except Exception as e:
        print(f"Error during download: {e}")
        return "Download failed", 400

@app.route('/')
def convert_to_mp3():
    return render_template('ConvertToMp3.html')

@app.route('/convert-to-mp4')
def convert_to_mp4():
    return render_template('ConvertToMp4.html')

# Serve the favicon to avoid 404 errors in browser requests
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/download', methods=['POST'])
def download_mp3():
    link = request.form.get('link')
    return download_file(link, format='mp3', cookies_path=COOKIES_PATH)

@app.route('/download-mp4', methods=['POST'])
def download_mp4():
    link = request.form.get('link')
    return download_file(link, format='mp4', cookies_path=COOKIES_PATH)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
