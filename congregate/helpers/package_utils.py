import tarfile
from io import BytesIO
from dacite import from_dict
from congregate.helpers.utils import guess_file_type
from congregate.migration.meta.api_models.pypi_package_data import PyPiPackageData
from congregate.migration.meta.api_models.multipart_content import MultiPartContent

def extract_pypi_package_metadata(pkg_info):
    """
        Converts data from PKG-INFO file into a dictionary of metadata
        and a string containing the package description
    """
    metadata_dict = {}
    description = ""
    # Split the content at the first occuring doube newline.
    # This marks the separation between the metadata and the description
    if s := pkg_info.split("\n\n"):
        metadata = s[0]
        # Join the description string back together
        metadata_dict['description'] = "\n\n".join(s[1:])

        for line in metadata.split("\n"):
            # Split the metadata fields to convert into a dictionary
            line_split = line.split(": ")
            k = line_split[0]
            # Grab the second index of the list, 
            # or join together the remaining indeces if multiple colons are present
            v = line_split[1] if len(line_split) < 1 else ": ".join(line_split[1:]) 
            if k and v:
                # Update the key to lowercase camelcase
                metadata_dict[k.replace("-", "_").lower()] = v

    return metadata_dict

def get_pypi_pkg_info(content):
    with tarfile.open(fileobj=BytesIO(content), mode='r:gz') as tar:
        for member in tar:
            if 'PKG-INFO' in member.name:
                return tar.extractfile(member.name).read()
        
def generate_pypi_package_payload(file_name, file_content, package_name, version) -> PyPiPackageData:
    file_type = guess_file_type(file_name)
    if 'tar.gz' in file_name:
        pkg_info = get_pypi_pkg_info(file_content)
        metadata = extract_pypi_package_metadata(pkg_info)
        return from_dict(data_class=PyPiPackageData, data={
            'content': MultiPartContent(file_name, BytesIO(file_content), file_type),
            **metadata
        })
    return PyPiPackageData(
            content=(file_name, file_content, file_type),
            name=package_name,
            version=version
        )