from congregate.migration.ado.api.projects import ProjectsApi
from congregate.migration.ado.api.repositories import RepositoriesApi
from gitlab_ps_utils.misc_utils import safe_json_response
from gitlab_ps_utils.json_utils import json_pretty

p = ProjectsApi()

response = p.get_project("08909a69-d852-4833-bd82-3c126bfcf71a")

response = p.get_all_projects()

all_items = list(response)
for item in all_items:
    print(json_pretty(item))

# print(json_pretty(response.json()))


# p = RepositoriesApi()

# # response = p.get_all_repositories("08909a69-d852-4833-bd82-3c126bfcf71a")

# # all_items = list(response)
# # for item in all_items:
# #     print(json_pretty(item))

# response = p.get_repository("8649f096-f55a-4966-9a65-adbb648fba6d")

# print(json_pretty(response.json()))

