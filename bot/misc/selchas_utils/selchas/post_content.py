import os
import base64
import requests
import json
from dotenv import load_dotenv
import logging
from http.client import responses
# from wordpress_xmlrpc import Client
# from wordpress_xmlrpc.methods import posts

load_dotenv('.env')
selchas_url = os.getenv('SELCHAS_REST_URL')
username = os.getenv('SELCHAS_WP_LOGIN')
password = os.getenv('SELCHAS_APP_PSWD')
logger = logging.getLogger('kvedautobot.sch')


def rest_post_img(img_path: str) -> tuple:
    url = 'https://сельский-час.рф/wp-json/wp/v2/media'

    data = open(f'{img_path}', 'rb').read()
    fileName = os.path.basename(img_path)
    wp_connection = username + ':' + password
    token = base64.b64encode(wp_connection.encode())
    response = requests.post(url=url,
                        data=data,
                        headers={ 
                            'Content-Type': 'image/jpg',
                            'Content-Disposition' : 'attachment; filename=%s'% fileName,
                            'Authorization': 'Basic ' + token.decode('utf-8')})
    
    resp_json = response.json()
    img_id: str = resp_json.get('id')
    link: str = resp_json.get('guid').get("rendered")
    logger.info('Loaded image to the server %s::%s' % (img_id, link))
    return (img_id, link)


def rest_post(
    url           : str,
    post_type     : str,
    title         : str,
    content       : str,
    excerpt       : str,
    featured_media: str,
    status        : str  = 'draft',
    categories    : str  = None,
    tags                 = None,
    # meta          : dict = None !!!!add video_filename
    ) -> tuple:
    
    wp_connection = username + ':' + password
    token = base64.b64encode(wp_connection.encode())
    logger.debug(f'Got token {token[:10]}...')
    headers = {'Authorization': 'Basic ' + token.decode('utf-8')}
    logger.debug(f'Initialized headers; keys={headers.keys()}')
    post = {
        'title'         : title,
        'status'        : status,
        'content'       : content,
        'excerpt'       : excerpt,
        'categories'    : categories,
        'tags'          : tags,
        'featured_media': str(featured_media),
        # 'meta'          : meta
    }
    wp_request = requests.post(
                            url + '/' + post_type, 
                            headers=headers, 
                            json=post
                            )  
    status_code = wp_request.status_code  
    status_explain = responses[wp_request.status_code]   
    if status_code != 201:
        logger.critical('got STATUS_CODE', 
                status_code, 
            ':', 
                status_explain)
        return False, False
    logger.debug(status_explain)
    post_link = json.loads(wp_request.content)['link']
    post_id = json.loads(wp_request.content)['id']
    logger.info('Your post is published on {}.'.format(post_link))
    return post_id, post_link   