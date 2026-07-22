import concurrent.futures
import os
import subprocess
import urllib

from torchvision.datasets.utils import download_url


def download_check(model_url: str, model_dir: str, model_name: str, is_overwrite: bool = False):
    model_path = os.path.join(model_dir, model_name)
    # remove model before overwrite
    if is_overwrite and os.path.exists(model_path):
        os.remove(model_path)
    if os.path.exists(model_path):
        print(f'Model {model_url} has been downloaded!')
        return False
    return True


def download_model_url(model_url: str, model_dir: str, model_name: str | None = None, is_overwrite: bool = False):
    try:
        if model_name is None:
            model_name = os.path.basename(model_url)
        if not download_check(model_url, model_dir, model_name, is_overwrite):
            return
        # get model file size
        response = urllib.request.urlopen(model_url)
        model_size = response.headers.get('Content-Length')
        if model_size is None:
            raise Exception('Invalid model url with empty file size!')
        download_url(model_url, model_dir)
        local_model_size = os.path.getsize(os.path.join(model_dir, model_name))
        # determine whether the model download is complete
        if float(model_size) == local_model_size:
            print(f'Download model {model_url} successfully!')
        else:
            raise Exception('Model download is not complete!')
    except Exception as e:
        print(f'Failed to download model {model_url} with error {e}!')
        raise e


def download_model_hdfs(hdfs_path: str, model_dir: str, model_name: str | None = None, is_overwrite: bool = False):
    try:
        if model_name is None:
            model_name = os.path.basename(hdfs_path)
        if not download_check(hdfs_path, model_dir, model_name, is_overwrite):
            return
        result = subprocess.run(['hdfs', 'dfs', '-get', hdfs_path, model_dir], capture_output=True, text=True,
                                check=True)
        # determine whether the model download is complete
        if result.returncode == 0:
            print(f'Download model {hdfs_path} successfully!')
        else:
            raise Exception(result.stderr)
    except FileNotFoundError as e:
        raise Exception('The current environment missing hdfs command!') from e
    except (subprocess.CalledProcessError, Exception) as e:
        print(f'Failed to download model {hdfs_path} with error {e}!')
        raise e


def download_model_hdfs_batch(hdfs_paths: list[str], model_dir: str, is_overwrite: bool = False):
    for hdfs_path in hdfs_paths:
        model_name = os.path.basename(hdfs_path)
        download_model_hdfs(hdfs_path, model_dir, model_name, is_overwrite)


def download_model_url_batch(model_urls: list[str], model_dir: str, is_overwrite: bool = False):
    with concurrent.futures.ThreadPoolExecutor(5) as pool:
        for url_path in model_urls:
            model_name = os.path.basename(url_path)
            pool.submit(download_model_url, url_path, model_dir, model_name, is_overwrite)
