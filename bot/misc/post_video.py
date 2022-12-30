from bot.misc.selchas_utils.selchas.main import main
from bot.misc.util import html_link

def post_video():
    video_info, (post_id, post_link) = main()
    # logger.info(f'Download_status: {video_info["status"]}')
    # logger.info(f'Got post_id: {post_id}')
    title = video_info['title']
    message = f"Video {title} succesfully posted.\n{html_link('Link to the post', post_link)}"
    return message

