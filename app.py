from flask import Flask, render_template, request, Response, redirect, url_for
import yt_dlp
import re
import os
import platform
import tempfile
from threading import Lock

app = Flask(__name__)

# Folder to store uploaded cookies
UPLOAD_FOLDER = 'uploads'
COOKIES_FILE = os.path.join(UPLOAD_FOLDER, 'cookies.txt')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Default download directories for different platforms
DOWNLOAD_DIR_PC = os.path.join(os.path.expanduser("~"), "Downloads")  # Default for PC (Windows/Linux)
DOWNLOAD_DIR_MAC = os.path.join(os.path.expanduser("~"), "Downloads")  # Default for Mac
DOWNLOAD_DIR_ANDROID = '/storage/emulated/0/Download'  # Default for Android
DOWNLOAD_DIR_IOS = '/var/mobile/Media/Downloads'  # Placeholder for iOS

# Lock to prevent concurrent downloads
download_lock = Lock()

def get_download_directory():
    """Identify the device type and return the appropriate download directory."""
    system = platform.system()
    if system == 'Linux' and 'ANDROID_STORAGE' in os.environ:
        return DOWNLOAD_DIR_ANDROID
    elif system == 'Darwin':
        return DOWNLOAD_DIR_MAC
    elif system == 'Windows':
        return DOWNLOAD_DIR_PC
    else:
        return DOWNLOAD_DIR_PC  # Default for other platforms like Linux desktops

def download_file(link, format):
    """Download YouTube video/audio and yield data in chunks."""
    if format not in ['mp3', 'mp4']:
        return "Invalid format. Only MP3 or MP4 formats are allowed.", 400

    try:
        print("Starting download process...")
        DOWNLOAD_DIR = get_download_directory()
        print(f"Download directory: {DOWNLOAD_DIR}")

        # Verify link is a YouTube URL
        if re.match(r'^(https?://)?(www\.)?(youtube\.com|youtu\.be|music\.youtube\.com)/.+', link):
            with download_lock:  # Lock to ensure no concurrent downloads
                ydl_opts = {
                    'format': 'bestaudio[ext=m4a]' if format == 'mp3' else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
                    'quiet': True,
                    'cookiefile': COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
                    'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s')  # Save to detected directory
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    print("Extracting info and downloading...")
                    info = ydl.extract_info(link)
                    filename = ydl.prepare_filename(info)
                    print("Download complete:", filename)

                    def generate(file_path):
                        with open(file_path, 'rb') as f:
                            while chunk := f.read(8192):
                                yield chunk

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

@app.route('/upload')
def upload_cookies():
    return render_template('UploadCookies.html')

@app.route('/upload-cookies', methods=['POST'])
def upload_cookies_file():
    """Handles the upload of the cookies.txt file only, storing it in the uploads directory."""
    file = request.files.get('cookies')
    if file and file.filename.endswith('.txt'):
        file.save(COOKIES_FILE)
        print(f"Cookies file uploaded to: {COOKIES_FILE}")
        return redirect(url_for('convert_to_mp3'))  # Redirect to main page or specified page
    return "Invalid file or no file uploaded. Please upload a valid cookies.txt file.", 400

@app.route('/download', methods=['POST'])
def download_mp3():
    link = request.form.get('link')
    return download_file(link, format='mp3')

@app.route('/download-mp4', methods=['POST'])
def download_mp4():
    link = request.form.get('link')
    return download_file(link, format='mp4')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
