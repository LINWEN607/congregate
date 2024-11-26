# Custom importer interface

This folder contains several dataclasses that represent the majority of the data needed for importing data to GitLab.
It is based off our file-based export/import functionality and essentially allows us to use that mechanism for any source instance
not currently supported directly in GitLab.

## Usage

*Note: We are going to assume the listing and staging functions for this source type has already been developed.*

### Extract data from the source instance

Extend the existing API wrappers used for listing and staging data to cover any additional specific data points from the source.

Common examples would be:
- Merge/Pull request
- Issues/tickets

### Transform the data to match the GitLab data structures

In the existing `congregate/migration/<source-type>` folder where you have been working out of for this source type,
create an `export.py` file that extends the `ExportBuilder` class. This is where we will house any data transformations.

The three main components of a project export you will likely need to map out are:

- Project Members: This is required for the project import to successfully import
- Mege Requests: This is optional, but a main reason to use this interface since the built-in GitLab APIs aren't as comprehensive as a project import
- Issues: This is optional as well since the GitLab APIs have close to parity with the project export dataclasses, 
but you have more flexibility and some additional fields/timestamps to work with if you map it out here

For each data type you need to map out, create a function handling that process that will return the specific dataclass needed for the project export.

For example, a function to map PR data to MR data could look like the following:

```python
def build_merge_requests(self):
    merge_requests = []
    for pr in self.pull_requests_api.get_all_pull_requests(project_id=self.project_id, repository_id=self.repository_id):
        # Convert Azure DevOps PR to GitLab MR format
        pr_id = pr['pullRequestId']
        merge_request_commits = self.build_mr_diff_commits(pr_id)
        start_sha = merge_request_commits[-1].sha
        target_sha = dig(pr, 'lastMergeSourceCommit', 'commitId')
        merge_request_diffs = self.build_mr_diff_files(start_sha, target_sha)
        merge_requests.append(MergeRequests(
            author=Author(name=dig(pr, 'createdBy', 'displayName')),
            iid=pr_id,
            source_branch=pr['sourceRefName'].replace("refs/heads/", ""),
            target_branch=pr['targetRefName'].replace("refs/heads/", ""),
            source_branch_sha=dig(pr, 'lastMergeSourceCommit', 'commitId') if self.pull_request_status(pr) == 'opened' else None,
            target_branch_sha=dig(pr, 'lastMergeTargetCommit', 'commitId'),
            merge_commit_sha=dig(pr, 'lastMergeCommit', 'commitId'),
            squash_commit_sha=dig(pr, 'lastMergeCommit', 'commitId') if pr.get('mergeStrategy') == 'squash' else None,
            title=pr['title'],
            description=pr['description'],
            state=self.pull_request_status(pr),
            draft=pr['isDraft'],
            created_at=pr['creationDate'],
            updated_at=pr.get('lastMergeSourceUpdateTime'),
            source_project_id=1,
            target_project_id=1,
            merge_request_diff=MergeRequestDiff(
                state='collected' if len(merge_request_diffs) > 0 else 'empty',
                created_at=pr['creationDate'],
                updated_at=pr.get('lastMergeSourceUpdateTime', pr['creationDate']),
                head_commit_sha=dig(pr, 'lastMergeSourceCommit', 'commitId') if self.pull_request_status(pr) == 'opened' else None,
                base_commit_sha=dig(pr, 'lastMergeTargetCommit', 'commitId'),
                start_commit_sha=dig(pr, 'lastMergeSourceCommit', 'commitId') if self.pull_request_status(pr) == 'opened' else None,
                commits_count=len(merge_request_commits),
                real_size=str(len(merge_request_diffs)),
                files_count=len(merge_request_diffs),
                sorted=True,
                diff_type='regular',
                merge_request_diff_commits=merge_request_commits,
                merge_request_diff_files=merge_request_diffs
            ),
            notes=self.build_mr_notes(pr_id),
            author_id=self.get_new_member_id(pr['createdBy'])
        ))
    return merge_requests
```

This function iterates over a source instance's Pull Request APIs and maps the data into a list of `MergeRequest` dataclass objects.
This example also calls sub functions to build out the Merge Request Commits and Merge Request Diffs, but the concept is the same: iterate over the necessary source API and map to a dataclass

You will need to create multiple mapping functions and this is where the bulk of your development time will be spent.

Once you have created the specific data type mapping functions, create a function in your extended `ExportBuilder` class called `build_<source-type>_data.py` to build out the entire export tree. It should look something like:

```python
# <source-type> in this example is Azure DevOps

def build_ado_data(self):
    merge_requests = self.build_merge_requests()
    issues = self.build_issues()
    return ProjectExport(
        project_members=self.build_project_members(),
        merge_requests=merge_requests,
        issues=issues
    )
```

### Load the data into a project export

Once all the data has been mapped using the dataclasses in the extend ExportBuilder, you will need to generate the export. 

The bare minimum for building an export and NOT using the rest of the Congregate workflow is the following:

```python
# CustomExportBuilder is the example name of the extended ExportBuilder

ce = CustomExportBuilder(example_project) # where example_project is a listed project object
tree = ce.build_custom_source_data() # this is the function you would write to build out the tree data
ce.build_export(tree, ce.project_metadata) # builds out the contents of the archive
ce.create_export_tar_gz() # Creates the actual archive
ce.delete_cloned_repo() # Clean up task to delete the cloned repo
```
