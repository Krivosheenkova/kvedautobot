import os
import logging 

import argparse
import pathlib
import ftplib
from tqdm import tqdm
from dotenv import load_dotenv
load_dotenv('.env')

logger = logging.getLogger('kvedautobot.sch')
HOST = os.getenv('FTP_HOST')
USER = os.getenv('FTP_USER')
PASSWD = os.getenv('FTP_PASSWD')
REMOTE_DIR = os.getenv('REMOTE_DIR')


def connect_to_server(
    host    : str, 
    user    : str, 
    password: str) -> ftplib.FTP:
    """Get authorized FTP connection object
    Args:
        host (str): FTP host
        user (str): FTP user
        password (str): FTP password
    Returns:
        ftplib.FTP: authorized FTP connection object
    """
    try:
        ftp = ftplib.FTP(host=host, timeout=5)
        ftp.login(user=user, passwd=password)
        ftp.encoding = 'UTF-8'
        logger.info(f'Successfull connect to {host}')
        return ftp
    except Exception as e:
        logger.critical(str(e))
        return False


def upload_file(ftp: ftplib.FTP, localfile: str, remotedir: str) -> str:
    """Upload file to remote ftp server
        Returns False if got wrong paths,
        returns remote path of saved file otherwise
    Args:
        ftp (ftplib.FTP): ftp logged in instance
        localfile (str): path to local file
    Returns:
        str: _description_
    """
    # flag for mark successful uploading
    # change ftp dir
    ftp.cwd(remotedir)
    # progress bar defenition
    filesize = os.stat(localfile).st_size

    tqdm_instance = tqdm(unit='blocks', unit_scale=True, leave=False, miniters=1, desc='Uploading...', total=filesize)
    def progress(sent):
        tqdm_instance.update(len(sent))

    # store data
    remotefile = os.path.basename(localfile)
    if remotefile not in ftp.nlst():
        try:
            with open(localfile, 'rb') as local_file:
                ftp.storbinary(f'STOR {remotefile}',
                                local_file, callback=progress)
                logger.info(f'file {remotefile} was succesfully uploaded.')
                logger.debug('success variable turns to True')

                file_path: str = ftp.pwd() + '/' + remotefile
                ftp.close()
                return file_path

        except Exception as e:
            logger.critical(str(e))
            return False

    elif remotefile in ftp.nlst():
        logger.info(f'file {remotefile} is already uploaded.')
        logger.debug('success variable turns to True')
        return ftp.pwd() + '/' + remotefile
    
    logger.error('Uncaught exception or error')
    return False


def main(file):
    ftp = connect_to_server(HOST, USER, PASSWD)
    saved_remote_path = upload_file(ftp, file, REMOTE_DIR)
    if saved_remote_path != False:
        return saved_remote_path
    logger.error('Uncaught exception or error')
    return False


if __name__ == '__main__':
    # define mp4 file
    video_info_folder = os.path.join('selchas/video_info', os.listdir('selchas/video_info')[0])
    video_path = ''.join([i for i in os.listdir(video_info_folder)
                        if i.split('.')[-1] == 'mp4'])
    file = os.path.join(video_info_folder, video_path)

    # upload defined file
    print(main(file))