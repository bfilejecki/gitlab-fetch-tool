import logging
import argparse
import time
import sys
import requests
import os
from git import Repo, GitError
from yaml import safe_load


def main():
    Config.verify_config()
    
    projects_dict = fetch_projects_info()
    # projects_dict = {key: value for (key,value) in projects_dict.items() if key == "infra"}
    start = time.perf_counter()
    clone_repos(projects_dict)
    end = time.perf_counter()
    logger.debug(f"Finished cloning, took: {(end - start):.3f} seconds")


def fetch_projects_info():
    projects_path = f'{Config.BASE_URL}/projects'
    url_params = {
        "simple": "true",
        "archived": "false",
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

        fetched_projects = {project["path_with_namespace"]: project["http_url_to_repo"] for project in body}
        logger.debug(f"Fetched projects: {fetched_projects}")
        projects_dict.update(fetched_projects)

        next_page = response.headers["X-Next-Page"]
        current_page += 1
        url_params["page"] = next_page

    logger.info(f"Found {len(projects_dict)} projects.")
    return projects_dict


def clone_repos(projects_dict):
    cloned_projects = []
    skipped_projects = []
    i = 0
    for project_name, project_url in projects_dict.items():
        i+=1
        logger.debug(f'Cloning project: {project_name} from url: {project_url}')
        logger.info(f'Current progress: {i}/{len(projects_dict)}')
        repo_dir = os.path.join(Config.OUTPUT, project_name)
        if os.path.exists(repo_dir):
            logger.warning(f'Destination directory: {repo_dir} exists, skipping {project_name}')
            skipped_projects.append(project_name)
            continue
        else:
            try:
                repo = Repo.clone_from(url=project_url, to_path=repo_dir)
            except GitError:
                logger.error("Something went wrong while cloning the repo, skipping")
                skipped_projects.append(project_name)
                continue
            except Exception:
                logger.error("Something went terribly wrong, program will terminate soon")
                sys.exit(1)
            cloned_projects.append(project_name)
            logger.info(f'Cloned project: {project_name}, created directory: {repo_dir}')
    
    logger.info(f"Cloned {len(cloned_projects)} projects and skipped {len(skipped_projects)}")
    logger.debug(f"Cloned projects: {cloned_projects}")
    logger.debug(f"Skipped projects: {skipped_projects}")


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
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
