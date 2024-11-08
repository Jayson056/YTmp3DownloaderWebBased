from flask import Flask, render_template, request, Response, redirect, url_for
import yt_dlp
import re
import os
import tempfile

app = Flask(__name__)

# Folder to store uploaded cookies
UPLOAD_FOLDER = 'uploads'
COOKIES_FILE = os.path.join(UPLOAD_FOLDER, 'cookies.txt')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def download_file(link, format='mp3'):
    """Download YouTube video/audio and yield data in chunks from a temporary file, using uploaded cookies if available."""
    try:
        print("Starting download process...")

        # Verify link is a YouTube URL
        if re.match(r'^(https?://)?(www\.)?(youtube\.com|youtu\.be|music\.youtube\.com)/.+', link):
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]' if format == 'mp3' else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
                'quiet': True,
                'cookiefile': COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,  # Use cookies if available
                'outtmpl': tempfile.mktemp(suffix=f".{format}")  # Temporary file path
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print("Extracting info and downloading...")

                # Attempt to download using cookies
                try:
                    info = ydl.extract_info(link, download=False)
                    print("Cookies verified. Video info extracted successfully.")
                except yt_dlp.utils.DownloadError as e:
                    print("Cookies not valid or download failed:", e)
                    return "Cookies verification failed. Please check your cookies file.", 400

                # Download if extraction is successful
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
    app.run(host='0.0.0.0', port=0000, debug=True)