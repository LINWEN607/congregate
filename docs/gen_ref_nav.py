"""Generate the code reference pages and navigation."""

import re
from pathlib import Path

import mkdocs_gen_files

def link_rep_readme():
    with open("README.md", "r") as f:
        data = f.read()

    data = data.replace('./', '../')
    data = data.replace('../docs/', '../')
    data = data.replace('.md', '/')

    return data

nav = mkdocs_gen_files.Nav()

for path in sorted(Path("congregate").glob("**/*.py")):
    if '__init__' not in str(path):
        module_path = path.relative_to("./").with_suffix("")
        doc_path = path.relative_to("./").with_suffix(".md")
        full_doc_path = Path("reference", doc_path)

        parts = list(module_path.parts)
        parts[-1] = f"{parts[-1]}.py"
        nav[parts] = doc_path

        with mkdocs_gen_files.open(full_doc_path, "w") as fd:
            ident = ".".join(module_path.parts)
            print("::: " + ident, file=fd)
        
        mkdocs_gen_files.set_edit_path(full_doc_path, path)

with mkdocs_gen_files.open("project_readme.md", "w") as new_readme:
    new_readme.write(link_rep_readme())

with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())