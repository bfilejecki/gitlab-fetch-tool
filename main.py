import logging
import argparse
import time
import sys
import requests
import os
from yaml import safe_load


def main():
    Config.verify_config()
    
    projects_dict = fetch_projects_info()
    clone_repos(projects_dict, True)

    
def fetch_projects_info():
    projects_path = f'{Config.BASE_URL}/projects'
    url_params = {
        "simple": "true",
        "per_page": "100",
        "sort_by": "id",
        "sort": "asc"
    }
    request_headers = {
        "PRIVATE_TOKEN" : Config.API_KEY
    }

    current_page = 1
    next_page = None
    projects_dict = {}
    
    while next_page or current_page == 1:
        response = requests.get(url=projects_path, params=url_params, headers=request_headers)
        body = response.json()

        projects_dict.update({project["path"]: project["http_url_to_repo"] for project in body})

        next_page = response.headers["X-Next-Page"]
        current_page += 1
        url_params["page"] = next_page

    return projects_dict


def clone_repos(projects_dict, dry_run):
    for project_name, project_url in projects_dict.items():
        logger.info(f'Cloning project: {project_name} from url: {project_url}')
        repo_dir = os.path.join(Config.OUTPUT, project_name)
        if os.path.exists(repo_dir):
            logger.warn(f'Destination directory: {repo_dir} exists, skipping {project_name}')
            continue
        else:
            if not dry_run:
                pass
            logger.info(f'Cloned project: {project_name}, created directory: {repo_dir}')
            


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(message)s",
        handlers=[logging.StreamHandler()],
    )

    return logging.getLogger(__name__)


class Config:

    _basedir = os.path.abspath(os.path.dirname(__file__))
    _config_path = os.path.join(_basedir, 'config.yml')

    API_KEY = safe_load(open(_config_path, 'r'))["api-key"]
    OUTPUT = os.path.abspath(safe_load(open(_config_path, 'r'))["output"])
    BASE_URL = safe_load(open(_config_path, 'r'))["base-url"]


    def verify_config():
        if os.path.exists(Config.OUTPUT) and not os.path.isdir(Config.OUTPUT):
            logger.error(f"output path {Config.OUTPUT} is not a directory")
            sys.exit(1)

        if not Config.API_KEY:
            logger.error(f'api-key is required!')
            sys.exit(1)
    
        if not Config.BASE_URL:
            logger.error(f'base-url is required!')
            sys.exit(1)


if __name__ == "__main__":
    logger = configure_logging()
    main()
