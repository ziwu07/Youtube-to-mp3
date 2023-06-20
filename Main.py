#!/scripts/pyvenv/audi_conv/bin/python3
import sys

import pytube.exceptions
from pytube import YouTube, Playlist
import moviepy.editor as mp
import os
import requests
from bs4 import BeautifulSoup


def get_title(page_url):
    response = requests.get(page_url)
    name = BeautifulSoup(response.text, 'html.parser')
    title = name.find('title').text
    new_title = title.replace(' - YouTube', '')
    return new_title


def sanitize_file_name(file_name):
    # Remove characters that are not allowed in file names
    invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|', "'", '.', ';']
    for char in invalid_chars:
        file_name = file_name.replace(char, ' ')
    try:
        file_name.encode('utf-8').decode('utf-8')
        return file_name
    except UnicodeDecodeError:
        return file_name.encode('latin1').decode('utf-8')


def download_audio(input_url='',filedir='./'):
    os.chdir(filedir)
    if "playlist" in input_url:
        # Download all videos in the playlist
        try:
            playlist = Playlist(input_url)
            playlist_title = sanitize_file_name(get_title(input_url))
        except Exception as e:
            print(f'error: invalid url {e}')
        else:
            videos = playlist.video_urls

            playlist_dir = sanitize_file_name(playlist_title)
            os.makedirs(playlist_dir, exist_ok=True)
            try:
                length = playlist.length
            except KeyError as e:
                print(f'error: the playlist is most likely private {e}')
            else:
                max_length = len(str(length))

                playlist_file = os.path.join(playlist_dir, f"# {playlist_title}.m3u")
                f = open(playlist_file, "w", encoding='utf-8')

                for i, video_url in enumerate(videos):
                    yt = YouTube(video_url, use_oauth=False, allow_oauth_cache=True)
                    try:
                        yt.check_availability()
                    except Exception as e:
                        print(f'unavailable {e}')
                    else:
                        try:
                            video = yt.streams.get_audio_only(subtype='webm')
                        except pytube.exceptions.AgeRestrictedError or pytube.exceptions.VideoPrivate as e:
                            print(f'Video is age restricted or private {e}')
                            while login != 'y' or login != 'n' or login is None:
                                login = input('Would you like to login inorder to download the video? (y/n) :')
                                if login == 'y':
                                    yt = YouTube(video_url, use_oauth=True, allow_oauth_cache=True)
                                elif login == 'n':
                                    print('Skipping...')
                                else:
                                    print('Please enter "y" or "n"')
                            try:
                                video = yt.streams.get_audio_only(subtype='webm')
                            except Exception as e:
                                print(e)
                        current = str(i + 1).zfill(max_length)
                        video_file = current + ' - ' + sanitize_file_name(get_title(video_url))
                        try:
                            video.download(output_path=playlist_dir, filename=video_file)
                        except Exception as e:
                            print(f'!!!!!error: {e}')
                            exits(e)
                        origin_file = os.path.join(playlist_dir, video_file)
                        mp3_file = os.path.join(playlist_dir, video_file + ".mp3")
                        clip = mp.AudioFileClip(origin_file)
                        clip.write_audiofile(mp3_file, codec='mp3', bitrate="320k", verbose=False, logger=None)
                        clip.close()
                        os.remove(origin_file)
                        f.write(video_file + ".mp3" + "\n")
                        print(f"Audio downloaded ({current}/{length}) : {video_file}")

                f.close()
                print(f"Playlist downloaded: {playlist_title}")
                print(f"Playlist file created: {playlist_file}")

    else:
        video_url = input_url
        playlist_dir = 'Songs'
        os.makedirs(playlist_dir, exist_ok=True)
        try:
            yt = YouTube(video_url, use_oauth=False, allow_oauth_cache=True)
        except pytube.exceptions.RegexMatchError as e:
            print(f'error: invalid url {e}')
        else:
            try:
                yt.check_availability()
            except Exception as e:
                print(f'unavailable {e}')
            else:
                try:
                    video = yt.streams.get_audio_only(subtype='webm')
                except pytube.exceptions.AgeRestrictedError or pytube.exceptions.VideoPrivate as e:
                    print(f'Video is age restricted or private {e}')
                    while login != 'y' or login != 'n' or login is None:
                        login = input('Would you like to login inorder to download the video? (y/n) :')
                        if login == 'y':
                            yt = YouTube(video_url, use_oauth=True, allow_oauth_cache=True)
                        elif login == 'n':
                            print('Skipping...')
                        else:
                            print('Please enter "y" or "n"')
                    try:
                        video = yt.streams.get_audio_only(subtype='webm')
                    except Exception as e:
                        print(e)
                        exits(e)
                video_file = sanitize_file_name(get_title(video_url))
                try:
                    video.download(output_path=playlist_dir, filename=video_file)
                except Exception as e:
                    print(f'!!!!!error: {e}')
                origin_file = os.path.join(playlist_dir, video_file)
                mp3_file = os.path.join(playlist_dir, video_file + ".mp3")
                clip = mp.AudioFileClip(origin_file)
                clip.write_audiofile(mp3_file, codec='mp3', bitrate="320k", verbose=False, logger=None)
                clip.close()
                os.remove(origin_file)
                print(f"Audio downloaded (1/1) : {video_file}")


def exits(e):
    sys.exit(e)


if __name__ == '__main__':
    url = input("Enter the YouTube video or playlist URL: ")
    download_audio(input_url=url,filedir='../songs')
