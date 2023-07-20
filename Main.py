#!/scripts/pyvenv/audi_conv/bin/python3
import pytube.exceptions
from pytube import YouTube, Playlist
import moviepy.editor as mp
import os
import requests
from bs4 import BeautifulSoup
import music_tag
from PIL import Image


def get_title(page_url:str):
    response = requests.get(page_url)
    name = BeautifulSoup(response.text, 'html.parser')
    title = name.find('title').text
    new_title = title.replace(' - YouTube', '')
    return new_title


def sanitize_file_name(file_name:str):
    invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|', "'", '.', ';']
    for char in invalid_chars:
        file_name = file_name.replace(char, ' ')
    return file_name

class Error404(Exception):
    pass

def download_image(url:str, file_path:str):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        with open(file_path, 'wb') as file:
            file.write(response.content)
    else:
        raise Error404

def make_thumbnail(image_path:str , result_path:str):
    original_image = Image.open(image_path)
    width, height = original_image.size
    original_aspect_ratio = width / height
    target_aspect_ratio_16_9 = 16 / 9
    target_aspect_ratio_1_1 = 1.0
    if original_aspect_ratio < target_aspect_ratio_16_9:
        new_height = int(width / target_aspect_ratio_16_9)
        y_offset = (height - new_height) // 2
        original_image = original_image.crop((0, y_offset, width, y_offset + new_height))
        width, height = original_image.size
    if width / height > target_aspect_ratio_1_1:
        new_width = int(height * target_aspect_ratio_1_1)
        x_offset = (width - new_width) // 2
        original_image = original_image.crop((x_offset, 0, x_offset + new_width, height))
    original_image.save(result_path)

def get_thumbnail(video_id:str,file_path:str):
    image_url = 'https://i.ytimg.com/vi/' + video_id

    try:
        download_image(url=image_url + '/maxresdefault.jpg',file_path=file_path)
    except Error404:
        try:
            download_image(url=image_url + '/sddefault.jpg',file_path=file_path)
        except Error404:
            try:
                download_image(url=image_url + '/hqdefault.jpg',file_path=file_path)
            except Error404:
                raise Error404
    make_thumbnail(image_path=file_path , result_path=file_path)

def add_tag(file:str,youtube_object:YouTube,origin_file:str,song_title:str):
    author = get_title(page_url=youtube_object.channel_url)
    publish_date = youtube_object.publish_date
    image_file = origin_file + '.jpg'
    tag_editor = music_tag.load_file(file)
    tag_editor['title'] = song_title
    tag_editor['artist'] = author
    get_thumbnail(video_id=youtube_object.video_id,file_path=image_file)
    image = open(image_file,'rb').read()
    tag_editor['artwork'] = image
    tag_editor.save()
    os.remove(image_file)

def _download(video_url:str,playlist_dir:str='Song',singular:bool='True'):
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
            while True:
                login = input('Would you like to login in order to download the video? (y/n) :')
                if login == 'y':
                    yt = YouTube(video_url, use_oauth=True, allow_oauth_cache=True)
                    break
                elif login == 'n':
                    print('Skipping...')
                    break
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
            current = '1'
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
            if singular:
                length = 1
            return f"Audio downloaded ({current}/{length}) : {video_file}"

def download_audio(input_url:str,filedir:str='./'):
    try:
        os.mkdir(filedir)
    except FileExistsError:
        pass
    if "playlist" in input_url:
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
                    output = _download(video_url=video_url,playlist_dir=playlist_dir,singular=False)
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
            return _download(video_url=input_url,playlist_dir=playlist_dir,singular=True)


if __name__ == '__main__':
    url = input("Enter the YouTube video or playlist URL: ")
    output = download_audio(input_url=url,filedir='./songs')
    print(output)
