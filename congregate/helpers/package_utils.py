import tarfile, json, base64, zipfile
from io import BytesIO
from dacite import from_dict
from gitlab_ps_utils.dict_utils import dig
from congregate import log
from congregate.helpers.utils import guess_file_type
from congregate.migration.gitlab.api.packages import PackagesApi
from congregate.migration.meta.api_models.pypi_package_data import PyPiPackageData
from congregate.migration.meta.api_models.npm_package_data import NpmPackageData
from congregate.migration.meta.api_models.multipart_content import MultiPartContent
from congregate.migration.meta.api_models.pypi_package import PyPiPackage
from congregate.migration.meta.api_models.npm_package import NpmPackage

def extract_pypi_package_metadata(pkg_info):
    """
        Converts data from PKG-INFO file into a dictionary of metadata
        and a string containing the package description
    """
    metadata_dict = {}
    # Split the content at the first occuring doube newline.
    # This marks the separation between the metadata and the description
    if pkg_info and (s := pkg_info.split("\n\n")):
        metadata = s[0]
        # Join the description string back together
        metadata_dict['description'] = "\n\n".join(s[1:])

        for line in metadata.split("\n"):
            # Split the metadata fields to convert into a dictionary
            line_split = line.split(": ")
            k = line_split[0]
            # Grab the second index of the list, 
            # or join together the remaining indeces if multiple colons are present
            if k:
                v = line_split[1] if len(line_split) < 3 else ": ".join(line_split[1:])
                if v:
                    # Update the key to lowercase camelcase
                    metadata_dict[k.replace("-", "_").lower()] = v

    return metadata_dict

def extract_npm_package_metadata(pkg_json):
    """
    Converts the content of a package.json file into a dictionary of metadata.

    Parameters:
    - content: The content of package.json as a string.

    Returns:
    A dictionary of the package metadata. If the content cannot be parsed, returns an empty string.
    """
    try:
        # Parse the JSON content into a Python dictionary
        metadata_dict = json.loads(pkg_json)
        return metadata_dict
    except json.JSONDecodeError as e:
        log.error(f"Error parsing JSON content: {e}")
        return ""

def get_pkg_data(content, filename):
    try:
        with tarfile.open(fileobj=BytesIO(content), mode='r:gz') as tar:
            for member in tar:
                if filename in member.name:
                    return (tar.extractfile(member.name).read()).decode('UTF-8')
    except tarfile.TarError as e:
        log.error(f"Error processing tarball: {e}")
        return ""
        
def generate_pypi_package_payload(package: PyPiPackage, pkg_info) -> PyPiPackageData:
    file_type = guess_file_type(package.file_name)
    return from_dict(data_class=PyPiPackageData, data={
        'content': MultiPartContent(package.file_name, package.content, file_type),
        'md5_digest': package.md5_digest,
        'sha256_digest': package.sha256_digest,
        **pkg_info
    })

def extract_pypi_wheel_metadata(file_content):
    try:
        with zipfile.ZipFile(BytesIO(file_content)) as z:
            for name in z.namelist():
                if name.endswith('.dist-info/METADATA'):
                    with z.open(name) as metadata_file:
                        pkg_info_content = metadata_file.read().decode('utf-8')
                        return extract_pypi_package_metadata(pkg_info_content)
    except zipfile.BadZipFile:
        log.error("The provided file is not a valid .whl (zip) file.")
    return {}

def generate_npm_package_payload(package: NpmPackage, pkg_json) -> NpmPackageData:
    file_type = guess_file_type(package.file_name)
    package_payload = from_dict(data_class=NpmPackageData, data={
        'content': MultiPartContent(package.file_name, package.content, file_type),
        'md5_digest': package.md5_digest,
        **pkg_json
    })
    return package_payload

def generate_npm_json_data(package_metadata_bytes, package_data, tarball_name, tarball_content, version, custom_tarball_url):
    # Base64 encode the tarball content
    encoded_content = base64.b64encode(tarball_content).decode('utf-8')

    # Decode the byte string to get the metadata as a dictionary
    package_metadata = json.loads(package_metadata_bytes.decode('utf-8'))

    # Build the JSON structure to put in the PUT request
    package_json_dict = {
        "_attachments": {
            tarball_name: {
                "content_type": "application/octet-stream",
                "data": encoded_content,
                "length": len(encoded_content)
            }
        },
        "_id": package_data.name,
        "description": package_data.description,
        "dist-tags": {"latest": version},
        "name": package_data.name,
        "readme": package_data.description,
        "versions": { version: dig(package_metadata, 'versions', version) }
    }

    # Update tarball URL
    package_json_dict["versions"][version]['dist']['tarball'] = custom_tarball_url

    package_json = json.dumps(package_json_dict)

    return package_json

def generate_custom_npm_tarball_url(host, pid, package_name, file_name):
    return f"{host}/api/v4/projects/{pid}/packages/npm/{package_name}/-/{file_name}"
    
def compare_packages(
    src_id, 
    dest_id, 
    package_name, 
    package_version, 
    src_host, 
    dest_host, 
    src_token, 
    dest_token, 
    PackagesApi,
    logger=None
):
    """
    Compares a package between source and destination GitLab instances
    to determine if they match exactly.
    
    Args:
        src_id: Source project ID
        dest_id: Destination project ID
        package_name: Package name
        package_version: Package version
        src_host: Source GitLab instance URL
        dest_host: Destination GitLab instance URL
        src_token: Source GitLab token
        dest_token: Destination GitLab token
        packages_api: Instance of PackagesApi
        logger: Optional logger
        
    Returns:
        dict: Comparison result with keys:
            - match (bool): True if packages match, False otherwise
            - reason (str): Reason for match/mismatch
            - details (str): Additional details (for mismatches)
    """
    prefix = f"[Project SRC:{src_id} → DST:{dest_id}]"
    log_info = lambda msg: logger.info(f"{prefix} {msg}") if logger else None
    log_warning = lambda msg: logger.warning(f"{prefix} {msg}") if logger else None

    packages_api = PackagesApi()
    
    # Get source packages
    src_packages = list(packages_api.get_project_packages(src_host, src_token, src_id))
    src_pkg = next((p for p in src_packages if p.get('name') == package_name and p.get('version') == package_version), None)
    
    if not src_pkg:
        log_info(f"Package {package_name} v{package_version} not found in source")
        return {
            "match": False,
            "reason": "source_not_found",
            "details": "Package not found in source project"
        }
        
    # Get destination packages
    dest_packages = list(packages_api.get_project_packages(dest_host, dest_token, dest_id))
    dest_pkg = next((p for p in dest_packages if p.get('name') == package_name and p.get('version') == package_version), None)
    
    if not dest_pkg:
        log_info(f"Package {package_name} v{package_version} not found in destination")
        return {
            "match": False,
            "reason": "dest_not_found",
            "details": "Package not found in destination project"
        }
        
    # Get file lists
    src_files = list(packages_api.get_package_files(src_host, src_token, src_id, src_pkg['id']))
    dest_files = list(packages_api.get_package_files(dest_host, dest_token, dest_id, dest_pkg['id']))
    
    # Compare file counts - Warning condition when destination has more files than source
    if len(dest_files) > len(src_files):
        log_warning(f"Destination has more files ({len(dest_files)}) than source ({len(src_files)}) for package {package_name} v{package_version}")
        log_warning(f"This may indicate duplicate uploads or incomplete prior migrations")
        log_warning(f"Consider manually deleting the package in the destination and retrying the migration")
        
        return {
            "match": False,
            "reason": "dest_has_more_files",
            "details": f"Destination has more files ({len(dest_files)}) than source ({len(src_files)}). Consider manual deletion."
        }
    
    # Compare file counts - standard mismatch
    if len(src_files) != len(dest_files):
        log_info(f"File count mismatch: source={len(src_files)}, dest={len(dest_files)}")
        return {
            "match": False,
            "reason": "file_count_mismatch",
            "details": f"File count mismatch - source: {len(src_files)}, destination: {len(dest_files)}"
        }
        
    # Compare individual files
    for src_file in src_files:
        dest_file = next((f for f in dest_files if f['file_name'] == src_file['file_name']), None)
        
        if not dest_file:
            log_info(f"File '{src_file['file_name']}' missing in destination")
            return {
                "match": False,
                "reason": "missing_file",
                "details": f"File '{src_file['file_name']}' exists in source but not in destination"
            }
            
        # Compare file size
        if src_file.get('size', 0) != dest_file.get('size', 0):
            log_info(f"Size mismatch for file '{src_file['file_name']}'")
            return {
                "match": False,
                "reason": "size_mismatch",
                "details": f"Size mismatch for '{src_file['file_name']}' - source: {src_file.get('size', 0)}, dest: {dest_file.get('size', 0)}"
            }
            
        # Compare checksums if available (trying multiple digest types)
        for digest_type in ['file_sha256', 'file_md5', 'file_sha1']:
            if digest_type in src_file and digest_type in dest_file:
                if src_file[digest_type] != dest_file[digest_type]:
                    log_info(f"{digest_type} mismatch for file '{src_file['file_name']}'")
                    return {
                        "match": False,
                        "reason": "checksum_mismatch",
                        "details": f"{digest_type} mismatch for '{src_file['file_name']}'"
                    }
    
    # If we get here, everything matches
    log_info(f"Package {package_name} v{package_version} matches exactly between source and destination")
    return {
        "match": True,
        "reason": "exact_match",
        "details": "All files match exactly"
    }