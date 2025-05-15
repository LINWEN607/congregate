import os
import glob
import errno
import requests
import mimetypes
import subprocess
from re import sub
from shutil import copy
from contextlib import contextmanager
from datetime import datetime
from urllib.parse import urlparse
from gitlab_ps_utils.json_utils import read_json_file_into_object


def get_congregate_path():
    app_path = os.getenv("CONGREGATE_PATH")
    if app_path is None:
        app_path = os.getcwd()
    return app_path


def is_dot_com(host):
    return "gitlab.com" in host if host else None


def is_github_dot_com(host):
    return "api.github.com" in host


def rotate_logs():
    """
        Rotate and empty logs
    """
    log_path = f"{get_congregate_path()}/data/logs"
    if os.path.isdir(log_path):
        log = f"{log_path}/congregate.log"
        audit_log = f"{log_path}/audit.log"
        import_json = f"{log_path}/import_failed_relations.json"
        end_time = str(datetime.now()).replace(" ", "_")
        try:
            for file in [log, audit_log, import_json]:
                if os.path.getsize(file) > 0:
                    print(f"Rotating and emptying '{file}'")
                    index = file.find(".")
                    copy(file, file[:index] + f"_{end_time}" + file[index:])
                    open(file, "w").close()
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
    else:
        raise NotADirectoryError(
            "Cannot find data directory. CONGREGATE_PATH not set or you are not running this in the Congregate directory.")


def stitch_json_results(result_type="project", steps=0, order="tail"):
    """
    Stitch together multiple JSON results files into a single file.

        :param result_type: (str) The specific result type file you want to stitch. (Default: project)
        :param steps: (int) How many files back you want to go for the stitching. (Default: 0)
        :return: list containing the newly stitched results
    """
    reverse = order.lower() == "tail"
    steps += 1
    files = glob.glob(
        f"{get_congregate_path()}/data/results/{result_type}_migration_results_*")
    files.sort(key=lambda f: f.split("results_")[
               1].replace(".json", ""), reverse=reverse)
    if steps > len(files):
        steps = len(files)
    files = files[:steps]
    results = []
    for result in files:
        data = read_json_file_into_object(result)
        results += ([r for r in data if r[next(iter(r))]])
    return results

def is_valid_url(url):
    parsed = urlparse(url)
    return all([parsed.scheme, parsed.netloc])

def guess_file_type(filename):
    """
        Guess file type based on file path/url
    """
    guess = mimetypes.guess_type(filename)
    if guess[0] and guess[1]:
        return f"{guess[0].split('/')[0]}/{guess[1]}"
    return guess[0]

# TODO: Move this to gitlab-ps-utils since it's used here and in Evaluate
def to_camel_case(s):
    """
        Shameless copy from https://www.w3resource.com/python-exercises/string/python-data-type-string-exercise-96.php
    """
    s = sub(r"(_|-)+", " ", s).title().replace(" ", "")
    return ''.join([s[0].lower(), s[1:]])

def try_multiple_filename_encodings(base_url, filename):
    """
    Generate a list of possible URL encodings for a filename to try in order.
    Returns list of tuples with (url, description) for each encoding attempt.
    
    Args:
        base_url: Base URL without the filename
        filename: The filename that needs encoding
        
    Returns:
        List of tuples with (encoded_url, encoding_description)
    """
    import urllib.parse
    
    # Create several encoding attempts
    encoding_attempts = [
        # Original filename for simple cases
        (f"{base_url}/{filename}", "original"),
        
        # Simple URL encoding
        (f"{base_url}/{urllib.parse.quote(filename)}", "url_encoded"),
        
        # Encode % characters first to avoid double-encoding
        (f"{base_url}/{filename.replace('%', '%25')}", "percent_encoded"),
        
        # Direct replacement of slashes
        (f"{base_url}/{filename.replace('/', '%2F')}", "slash_encoded"),
        
        # URL decoded version (some APIs want the raw path)
        (f"{base_url}/{urllib.parse.unquote(filename)}", "url_decoded"),
        
        # Another approach for double-encoded URLs
        (f"{base_url}/{filename.replace('%2F', '/')}", "slash_decoded")
    ]
    
    return encoding_attempts

def download_file_with_encoding_fallback(url_base, filename, output_path, token, logger=None):
    """
    Downloads a file with multiple encoding fallbacks for robust handling of filenames with special characters.
    
    Args:
        url_base: Base URL without the filename
        filename: Filename to download (may contain special characters)
        output_path: Path to save the downloaded file
        token: Authentication token
        logger: Optional logger
        
    Returns:
        tuple: (success, actual_size, successful_encoding_type)
    """    
    log_info = lambda msg: logger.info(msg) if logger else None
    
    download_success = False
    download_headers = {"PRIVATE-TOKEN": token}
    successful_encoding_type = None
    
    # Get encoded URLs to try
    download_urls = try_multiple_filename_encodings(url_base, filename)
    
    # Try downloading with different URL encodings
    for url, encoding_type in download_urls:
        if download_success:
            break
            
        try:
            log_info(f"Attempting download with {encoding_type} encoding")
            
            with requests.get(url, headers=download_headers, stream=True) as response:
                if response.status_code == 200:
                    with open(output_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    
                    download_success = True
                    log_info(f"Download successful using {encoding_type} encoding")
                    successful_encoding_type = encoding_type
                else:
                    log_info(f"Download failed with {encoding_type} encoding: {response.status_code}")
        except Exception as e:
            log_info(f"Error downloading with {encoding_type} encoding: {str(e)}")
    
    actual_size = 0
    if download_success:
        import os
        actual_size = os.path.getsize(output_path)
    
    return (download_success, actual_size, successful_encoding_type)

def upload_file_with_encoding_fallback(url_base, filename, file_path, token, file_size, use_curl=False, logger=None):
    """
    Uploads a file with multiple encoding fallbacks and optional curl support for large files.
    """
    log_info = lambda msg: logger.info(msg) if logger else None
    log_warning = lambda msg: logger.warning(msg) if logger else None
    log_error = lambda msg: logger.error(msg) if logger else None
    
    upload_urls = try_multiple_filename_encodings(url_base, filename)
    upload_success = False
    
    # For larger files (>50MB), start with curl
    if file_size > 50 * 1024 * 1024:
        use_curl = True
    
    # Try the preferred method first (curl or requests based on file size)
    methods_to_try = []
    if use_curl:
        methods_to_try = ["curl", "requests"]
    else:
        methods_to_try = ["requests", "curl"]  # Try requests first, then curl as fallback
    
    for method in methods_to_try:
        if upload_success:
            break
            
        if method == "curl":
            log_info(f"Using curl method for upload of {file_size} bytes")
            
            for url, encoding_type in upload_urls:
                if upload_success:
                    break
                    
                try:
                    log_info(f"Attempting upload with curl using {encoding_type} encoding")
                    
                    # Add more options to curl for better reliability
                    curl_cmd = [
                        "curl", "--fail", "--retry", "3", "--retry-delay", "5",
                        "-X", "PUT",
                        "-H", f"PRIVATE-TOKEN: {token}",
                        "-H", "Content-Type: application/octet-stream",
                        "-H", "Transfer-Encoding: chunked",
                        "--connect-timeout", "60",
                        "--max-time", "3600",  # 1 hour timeout
                        "--upload-file", file_path,
                        url
                    ]
                    
                    # Execute curl command
                    result = subprocess.run(curl_cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        upload_success = True
                        log_info(f"Upload with curl successful using {encoding_type} encoding")
                    else:
                        # Use warning instead of error for individual encoding attempts
                        log_warning(f"Upload with curl failed using {encoding_type} encoding: {result.stderr[:200]}")
                except Exception as e:
                    # Use warning instead of error for individual encoding attempts
                    log_warning(f"Error using curl with {encoding_type} encoding: {str(e)}")
        
        elif method == "requests":
            log_info(f"Using requests method for upload of {file_size} bytes")
            
            # For requests-based upload
            upload_headers = {
                "PRIVATE-TOKEN": token,
                "Content-Type": "application/octet-stream"
            }
            
            for url, encoding_type in upload_urls:
                if upload_success:
                    break
                    
                try:
                    log_info(f"Attempting upload using requests with {encoding_type} encoding")
                    
                    with open(file_path, 'rb') as f:
                        response = requests.put(url, headers=upload_headers, data=f, timeout=3600)
                        
                        if response.status_code == 201:
                            upload_success = True
                            log_info(f"Upload successful using {encoding_type} encoding")
                        else:
                            # Use warning instead of error for individual encoding attempts
                            log_warning(f"Upload failed using {encoding_type} encoding: HTTP {response.status_code} - {response.text[:200] if response.text else 'No response text'}")
                except Exception as e:
                    # Use warning instead of error for individual encoding attempts
                    log_warning(f"Error uploading with {encoding_type} encoding: {str(e)}")
    
    return upload_success

@contextmanager
def temp_directory(prefix="gitlab_temp_"):
    """
    Context manager for creating and cleaning up temporary directories.
    
    Usage:
        with temp_directory() as temp_dir:
            # use temp_dir
    """
    import tempfile
    import shutil
    
    temp_dir = tempfile.mkdtemp(prefix=prefix)
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

class ProjectIdPrefixedLogger:
    """Simple logger wrapper that adds project ID prefixes to log messages"""
    
    def __init__(self, logger, src_id, dest_id):
        self.logger = logger
        self.prefix = f"[Project SRC:{src_id} → DST:{dest_id}]"
    
    def info(self, msg):
        self.logger.info(f"{self.prefix} {msg}")
    
    def warning(self, msg):
        self.logger.warning(f"{self.prefix} {msg}")
    
    def error(self, msg):
        self.logger.error(f"{self.prefix} {msg}")