import logging
from dotenv import load_dotenv
import os
import re
from .download_youtube_video import main as download_video
from .send_video_to_ftp import main as upload_video
from .post_content import rest_post_img, rest_post



load_dotenv('.env')
selchas_url = os.getenv('SELCHAS_REST_URL')
username = os.getenv('SELCHAS_WP_LOGIN')
password = os.getenv('SELCHAS_APP_PSWD')
logger = logging.getLogger('kvedautobot.sch')

def main():
        resp = download_video()['resp']
        remote_filename = os.path.basename(
                upload_video(resp['video_path'])
                )


        post_title = resp['title']
        post_body = resp['description']+f'\n{remote_filename}'
        post_snippet = resp['snippet']
        thumb_path = resp['thumbnail_path']
        media_id, media_link = rest_post_img(thumb_path)

        post = {
                'status'        : 'draft',
                'post_type'     : 'archive',
                'excerpt'       : post_snippet,
                'url'           : selchas_url,
                'title'         : post_title,
                'content'       : post_body,
                'featured_media': media_id
                }

        return resp, rest_post(**post)

if __name__=='__main__':
        os.chdir('../../')
        main()