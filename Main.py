#!/scripts/pyvenv/audi_conv/bin/python3
import pytube.exceptions
from pytube import YouTube, Playlist
import moviepy.editor as mp
import os
import requests
from bs4 import BeautifulSoup
import music_tag
from urllib.parse import urlparse, urlunparse
from datetime import datetime


def get_title(page_url:str):
    response = requests.get(page_url)
    name = BeautifulSoup(response.text, 'html.parser')
    title = name.find('title').text
    new_title = title.replace(' - YouTube', '')
    return new_title


def sanitize_file_name(file_name:str):
    # Remove characters that are not allowed in file names
    invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|', "'", '.', ';']
    for char in invalid_chars:
        file_name = file_name.replace(char, ' ')
    return file_name

def download_thumbnail(thumbnail_url:str,file_path:str='./thumbnail.jpg'):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    
    response = requests.get(thumbnail_url, headers=headers)
    if response.status_code == 200:
        with open(file_path, 'wb') as file:
            file.write(response.content)
    else:
        print("Failed to download thumbnail.")

def add_tag(file:str,youtube_object:YouTube,origin_file:str,song_title:str):
    author = youtube_object.author
    publish_date = youtube_object.publish_date
    initial_thumbnail_url = youtube_object.thumbnail_url
    bad_url = urlparse(initial_thumbnail_url)
    bad_url = bad_url._replace(query=None)
    thumbnail_url = urlunparse(bad_url)
    image_file = origin_file + '.jpg'
    download_thumbnail(thumbnail_url=thumbnail_url,file_path=image_file)
    tag_editor = music_tag.load_file(file)
    tag_editor['title'] = song_title
    tag_editor['artist'] = author
    tag_editor['year'] = publish_date.year

def download(video_url:str,playlist_dir:str='Song',singular:bool='True'):
    yt = YouTube(video_url, use_oauth=False, allow_oauth_cache=True)
    try:
        yt.check_availability()
    except Exception as e:
        return f'unavailable {e}'
    else:
        try:
            video = yt.streams.get_audio_only(subtype='webm')
        except pytube.exceptions.AgeRestrictedError or pytube.exceptions.VideoPrivate as e:
            print(f'Video is age restricted or private')
            while login != 'y' or login != 'n' or login is None:
                login = input('Would you like to login in order to download the video? (y/n) :')
                if login == 'y':
                    yt = YouTube(video_url, use_oauth=True, allow_oauth_cache=True)
                elif login == 'n':
                    print('Skipping...')
                else:
                    print('Please enter "y" or "n"')
            try:
                video = yt.streams.get_audio_only(subtype='webm')
            except Exception as e:
                return e
        if singular is False:
            global max_length
            global which
            current = str(which + 1).zfill(max_length)
        else:
            current = 1
        name = sanitize_file_name(file_name=get_title(page_url=video_url))
        video_file = current + ' - ' + name
        try:
            video.download(output_path=playlist_dir, filename=video_file)
        except Exception as e:
            return f'error: {e}'
        else:
            origin_file = os.path.join(playlist_dir, video_file)
            mp3_file = os.path.join(playlist_dir, video_file + ".mp3")
            clip = mp.AudioFileClip(origin_file)
            clip.write_audiofile(mp3_file, codec='mp3', bitrate="320k", verbose=False, logger=None)
            clip.close()
            os.remove(origin_file)
            add_tag(file=mp3_file , youtube_object=yt,origin_file=origin_file,song_title=name)
            if singular is False:
                global f
                f.write(video_file + ".mp3" + "\n")
            global length
            return f"Audio downloaded ({current}/{length}) : {video_file}"

def download_audio(input_url:str,filedir:str='./'):
    os.chdir(filedir)
    if "playlist" in input_url:
        # Download all videos in the playlist
        try:
            playlist = Playlist(input_url)
            playlist_title = sanitize_file_name(file_name=get_title(page_url=input_url))
        except Exception as e:
            return f'error: invalid url {e}'
        else:
            videos = playlist.video_urls

            playlist_dir = sanitize_file_name(file_name=playlist_title)
            os.makedirs(playlist_dir, exist_ok=True)
            try:
                global length
                length = playlist.length
            except KeyError as e:
                return f'error: the playlist is most likely private, make it unlisted and try again {e}'
            else:
                global max_length
                max_length = len(str(length))

                playlist_file = os.path.join(playlist_dir, f"# {playlist_title}.m3u")
                global f
                f = open(playlist_file, "w", encoding='utf-8')

                global which
                for which, video_url in enumerate(videos):
                    output = download(video_url=video_url,playlist_dir=playlist_dir,singular=False)
                    print(output)
                
                f.close()
                return f"Playlist downloaded: {playlist_title}"

    else:
        playlist_dir = 'Songs'
        os.makedirs(playlist_dir, exist_ok=True)
        try:
            yt = YouTube(input_url, use_oauth=False, allow_oauth_cache=True)
        except pytube.exceptions.RegexMatchError as e:
            return f'error: invalid url {e}'
        else:
            return download(video_url=input_url,playlist_dir=playlist_dir,singular=True)


if __name__ == '__main__':
    url = input("Enter the YouTube video or playlist URL: ")
    output = download_audio(input_url=url,filedir='./songs')
    print(output)
