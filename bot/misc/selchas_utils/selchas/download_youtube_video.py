import os
import logging
from pprint import pp
import json
import requests
from dotenv import load_dotenv
from pytube import YouTube
from pytube import Channel
from pytube.cli import on_progress
from pathvalidate import sanitize_filename
from http.client import IncompleteRead
from time import sleep

load_dotenv('.env')
CHANNEL_URL = os.getenv('CHANNEL_URL')

logger = logging.getLogger('kvedautobot.sch')


def get_channel(url) -> Channel:
    try:
        c = Channel(url)
        sleep(7)
        videos = c.videos
    except IncompleteRead as e:
        c_part = e.partial.decode('utf-8')
        print(c_part)
    assert len(videos) != 0, 'No videos found on channel'
    return c

def get_last_video_title_and_url(channel: Channel) -> tuple:
    """Возвращает строку с названием и ссылкой на последнее видео"""
    # Get last youtube object of video
    # videos = channel.videos[0:1] 
    # for video in videos:
    #     title = video.title
    #     url = video.watch_url
    # return title, url
    limit =1
    url = f"https://www.googleapis.com/youtube/v3/search?key=AIzaSyC8089Tr-0pN9SFaiFlbAyqlEpHm2nSqgQ&channelId=UCkzdSoNgljm7Ub3nLe0xJmw&part=snippet,id&order=date"
    url += "&maxResults=" + str(limit)
    r = requests.get(url)
    resp = json.loads(r.text)['items'][0]
    title = resp['snippet']['title']
    id = resp['id']['videoId']
    video_url = youtube_link(id)
    return title, video_url


def youtube_link(id):
    return f'https://www.youtube.com/watch?v={id}'

def download_video(url: str, path_to_save='selchas/video_info/'):
    """Download video from youtube by url.
    Args:
        url (str): url to video
        path_to_save (str, optional): Defaults to 'selchas/video_info/'.
    Returns:
        dict: dict(video_info got from api)
    """
    yt = YouTube(url=url, on_progress_callback=on_progress)
    title = yt.title
    description = yt.description
    desc_snippet = snippet(description)
    thumbnail_url = yt.thumbnail_url

    path_to_save = os.path.join(path_to_save, sanitize_filename(title))
    path_exists = is_info_exists(path_to_save)
    if path_exists != False:
        video_filepath, thumbnail_filepath = path_exists
        logger.warning(f'Video is already downloaded in: {path_to_save[:30]}...')
        return {'resp': 
            {'status':'video is already downloaded',
             'video_path': video_filepath,
             'title': title,
             'description': description,
             'snippet': desc_snippet,
             'thumbnail_path': thumbnail_filepath
             }
            }
    saved_video_path = yt\
        .streams\
        .filter(progressive=True, 
                file_extension='mp4')\
        .get_highest_resolution()\
        .download(output_path=path_to_save, 
                  max_retries=3)
    logger.info('Video saved to %s...' % (saved_video_path[:30]))

    thumbnail_filepath = save_image_from_url(thumbnail_url, path_to_save)
    logger.info('Thumbnail saved to %s' % (thumbnail_filepath))
    return {'resp':
        {'status': 'success',
        'url': url,
        'title': title,
        'thumbnail_path': thumbnail_filepath,
        'description': description,
        'snippet': desc_snippet,
        'video_name': os.path.basename(saved_video_path),
        'video_path': saved_video_path}
    }


def is_info_exists(video_name):
    """Returns path if video already exists"""
    if os.path.isdir(video_name):
        mp4 = [i for i in os.listdir(video_name) if i.__contains__('.mp4')]
        jpg = [i for i in os.listdir(video_name) if i.__contains__('.jpg')]
        if len(mp4) == 1 and len(jpg) == 1:
            return os.path.join(video_name, ''.join(mp4)),\
                   os.path.join(video_name, ''.join(jpg))
    return False


def snippet(text):
    return text[:text.find('. ', text.find('. ')+30)+1]


def save_image_from_url(pic_url: str, path_to_save: str) -> str:
    """Returns saved image path"""
    pic_url = try_get_better_image(pic_url)
    filename = pic_url.split('/')[-1]
    with open(os.path.join(path_to_save, filename), 'wb') as f:
        response = requests.get(pic_url, stream=True)
        if not response.ok:
            print(response)
        for block in response.iter_content(1024):
            if not block:
                break
            f.write(block)
    return os.path.join(path_to_save, filename)


def try_get_better_image(image_url):
    file = image_url.split('/')[-1]
    new_image_url = image_url.replace(file, 'maxresdefault.jpg')
    if new_image_url == image_url:
        return image_url
    resp = requests.get(new_image_url)
    if resp.status_code == 200:
        return new_image_url


def main():
    # channel = get_channel(CHANNEL_URL)
    last_video_title, last_video_url = get_last_video_title_and_url(None)
    response = download_video(last_video_url)
    pp(response)
    return response

if __name__ == '__main__':
    r = main()
    print(r)