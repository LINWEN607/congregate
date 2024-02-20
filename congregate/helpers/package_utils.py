import tarfile, json
from io import BytesIO
from dacite import from_dict
from congregate import log
from congregate.helpers.utils import guess_file_type
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
            v = line_split[1] if len(line_split) < 3 else ": ".join(line_split[1:]) 
            if k and v:
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

def get_pypi_pkg_info(content):
    try:
        with tarfile.open(fileobj=BytesIO(content), mode='r:gz') as tar:
            for member in tar:
                if 'PKG-INFO' in member.name:
                    return (tar.extractfile(member.name).read()).decode('UTF-8')
    except tarfile.TarError as e:
        log.error(f"Error processing tarball: {e}")
        return ""
    
def get_npm_pkg_json(content):
    """
    Extracts the package.json file from a .tgz file and returns its content as a string.

    Parameters:
    - content: The path to the .tgz file.

    Returns:
    The content of package.json as a string. If package.json is not found or an error occurs, returns an empty String.
    """    
    try:
        with tarfile.open(fileobj=BytesIO(content), mode='r:gz') as tgz:
            for member in tgz:
                if 'package.json' in member.name:
                    return (tgz.extractfile(member.name).read()).decode('UTF-8')
    except Exception as e:
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

def generate_npm_package_payload(package: NpmPackage, pkg_json) -> NpmPackageData:
    file_type = guess_file_type(package.file_name)
    package_payload = from_dict(data_class=NpmPackageData, data={
        'content': MultiPartContent(package.file_name, package.content, file_type),
        'md5_digest': package.md5_digest,
        **pkg_json
    })
    return package_payload
