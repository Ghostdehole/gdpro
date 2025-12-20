import os
import requests
import logging

logger = logging.getLogger(__name__)

UP_SERVER = os.getenv('UP_SERVER')
UP_TOKEN = os.getenv('UP_TOKEN')
UP_REPO_ID = os.getenv('UP_REPO_ID')
UP_UPLOAD_DIR = os.getenv('UP_UPLOAD_DIR', '/uploads/')

def upload_to_seafile(file_obj, filename: str) -> str | None:

    if not UP_SERVER or not UP_TOKEN or not UP_REPO_ID:
        logger.error("UP_SERVER, UP_TOKEN, or UP_REPO_ID is not set. Please check the environment variables")
        return None
    try:
        upload_url = f"{UP_SERVER}/api/v2.1/repos/{UP_REPO_ID}/upload-link/"
        headers = {"Authorization": f"Token {UP_TOKEN}"}
        resp = requests.get(upload_url, headers=headers)
        resp.raise_for_status()
        upload_link = resp.json().strip('"')

        files = {'file': (filename, file_obj.read(), 'application/octet-stream')}
        data = {'parent_dir': UP_UPLOAD_DIR}
        upload_resp = requests.post(upload_link, files=files, data=data)
        upload_resp.raise_for_status()

        internal_path = f"{UP_UPLOAD_DIR}{filename}"
        logger.info(f"The file has been uploaded to : {internal_path}")
        return internal_path

    except Exception as e:
        logger.error(f"upload failed: {e}")
        return None
