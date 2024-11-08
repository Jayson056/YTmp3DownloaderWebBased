from flask import Flask, render_template, request, send_from_directory, jsonify
import requests
import os
import yt_dlp
import re
import platform

app = Flask(__name__)

# Default download directories
DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

def get_download_directory():
    """Get appropriate download directory based on platform."""
    system = platform.system()
    if system == 'Linux' and 'ANDROID_STORAGE' in os.environ:
        return '/storage/emulated/0/Download'
    elif system == 'Darwin':
        return os.path.join(os.path.expanduser("~"), "Downloads")
    elif system == 'Windows':
        return os.path.join(os.path.expanduser("~"), "Downloads")
    return DOWNLOAD_DIR

def rename_mp4_to_mp3(mp4_filepath):
    """Rename the .mp4 file to .mp3."""
    mp3_filepath = mp4_filepath.replace('.mp4', '.mp3')
    os.rename(mp4_filepath, mp3_filepath)
    return mp3_filepath

def download_file(link, req_format="mp4"):
    """Download YouTube video or file from a link in the requested format."""
    download_dir = get_download_directory()
    filepath = None

    try:
        if re.match(r'^(https?://)?(www\.)?(youtube\.com|youtu\.be|music\.youtube\.com)/.+', link):
            ydl_opts = {
                'format': f'best[ext={req_format}]',
                'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
                'quiet': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=True)
                filename = ydl.prepare_filename(info)
                filepath = os.path.join(download_dir, os.path.basename(filename))
                
                if req_format == "mp3":
                    filepath = rename_mp4_to_mp3(filepath)

        else:
            response = requests.get(link, stream=True)
            response.raise_for_status()
            filename = link.split('/')[-1] or 'downloaded_file'
            if req_format == 'mp4':
                filename += '.mp4'
            filepath = os.path.join(download_dir, filename)

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            if req_format == "mp3" and filepath.endswith('.mp4'):
                filepath = rename_mp4_to_mp3(filepath)

        return filepath

    except Exception as e:
        print(f"Error: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    link = request.form.get('link')
    req_format = request.form.get('format', 'mp4')
    filepath = download_file(link, req_format)

    if filepath:
        filename = os.path.basename(filepath)
        return send_from_directory(directory=get_download_directory(), path=filename, as_attachment=True)
    return jsonify({'error': 'Download failed'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=0000, debug=True)  # Set a valid port number (e.g., 5000)
