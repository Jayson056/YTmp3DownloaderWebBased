from flask import Flask, render_template, request, Response
import yt_dlp
import os
import tempfile
import re

app = Flask(__name__)

# Folder to store uploaded cookies
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def download_file(link, format='mp3', cookies_path=None):
    """Download YouTube video/audio using yt-dlp and stream the file."""
    try:
        print("Starting download process...")

        # Check if the link is a valid YouTube URL
        if re.match(r'^(https?://)?(www\.)?(youtube\.com|youtu\.be|music\.youtube\.com)/.+', link):
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]' if format == 'mp3' else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
                'cookiefile': cookies_path,  # Path to uploaded cookies file
                'quiet': False,  # Set to False for debugging
                'verbose': True,
                'outtmpl': tempfile.mktemp(suffix=f".{format}")  # Temporary file path
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print("Checking if cookies are valid...")

                try:
                    # Attempt to fetch video information without downloading to test cookies
                    info = ydl.extract_info(link, download=False)
                    print("Cookies appear to be working; proceeding with download...")
                except yt_dlp.utils.DownloadError as e:
                    print("Cookies failed or require update:", e)
                    return "Cookies are invalid or verification failed. Please update cookies.", 400

                # Continue with download if cookies are verified
                info = ydl.extract_info(link)
                filename = ydl.prepare_filename(info)
                print("Download complete:", filename)

                # Stream the file back to the client
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
            print("Invalid or unsupported link format:", link)
            return "Unsupported link format", 400

    except Exception as e:
        print(f"Unexpected error during download: {e}")
        return "Download failed due to an error.", 400

@app.route('/')
def index():
    return render_template('ConvertToMp3.html')

@app.route('/upload-cookies', methods=['POST'])
def upload_cookies_file():
    """Endpoint to handle cookies file upload."""
    file = request.files.get('cookies')
    if file:
        cookies_path = os.path.join(app.config['UPLOAD_FOLDER'], 'cookies.txt')
        file.save(cookies_path)
        print("Cookies uploaded and saved.")
        return "Cookies uploaded successfully", 200
    else:
        return "No cookies file uploaded", 400

@app.route('/download', methods=['POST'])
def download_mp3():
    """Endpoint to download MP3 using cookies."""
    link = request.form.get('link')
    cookies_path = os.path.join(app.config['UPLOAD_FOLDER'], 'cookies.txt')

    if not os.path.exists(cookies_path):
        return "Cookies file is missing. Please upload it first.", 400

    return download_file(link, format='mp3', cookies_path=cookies_path)

@app.route('/download-mp4', methods=['POST'])
def download_mp4():
    """Endpoint to download MP4 using cookies."""
    link = request.form.get('link')
    cookies_path = os.path.join(app.config['UPLOAD_FOLDER'], 'cookies.txt')

    if not os.path.exists(cookies_path):
        return "Cookies file is missing. Please upload it first.", 400

    return download_file(link, format='mp4', cookies_path=cookies_path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)