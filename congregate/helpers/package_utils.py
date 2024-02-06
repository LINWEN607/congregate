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
        description = "\n\n".join(s[1:])

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

    return metadata_dict, description
