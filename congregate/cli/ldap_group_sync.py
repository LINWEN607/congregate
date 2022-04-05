import json
from csv import reader

from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.api.base_api import GitLabApiWrapper
from gitlab_ps_utils.misc_utils import safe_json_response

class LdapGroupSync(BaseClass):
    """
    Based on https://docs.gitlab.com/ee/api/groups.html#add-ldap-group-link-with-cn-or-filter
    """

    def __init__(self):
        super().__init__()
        self.ldap_dict = {}
        self.ldap_results = []
        self.gl_wrapper = GitLabApiWrapper()

    def load_pdv(self, file_path):
        """
        Load a pipe-delimited file of group_id,ldap_cn_or_filter to use with the LDAP group sync settings API

        """
        with open(file_path) as ldap_group_mapping_file:
            csv_reader = reader(ldap_group_mapping_file, delimiter='|')
            for row in csv_reader:
                group_id = str(row[0].strip())
                cn = str(row[1].strip())
                if self.ldap_dict.get(group_id, None) is None:
                    self.ldap_dict[group_id] = cn
                else:
                    self.log.warning(
                        "group_id %s duplicated in file" % (group_id))

    def synchronize_groups(self, dry_run=True):
        gitlab_token = self.config.destination_token
        gitlab_host = self.config.destination_host
        for link in self.ldap_dict:
            gitlab_api = "groups/{group_id}/ldap_group_links".format(
                group_id=link)
            gitlab_post_data = {
                "provider": f"{self.config.ldap_group_link_provider}",
                "cn": f"{self.ldap_dict[link]}",
                "group_access": self.config.ldap_group_link_group_access
            }
            gitlab_post_description = "Linking {group_id} with {cn}".format(
                group_id=link, cn=self.ldap_dict[link])
            self.log.info(gitlab_post_description)
            if not dry_run:
                response = self.gl_wrapper.api.generate_post_request(
                    host=gitlab_host,
                    token=gitlab_token,
                    api=gitlab_api,
                    data=json.dumps(gitlab_post_data),
                    description=gitlab_post_description
                )
                response_json = safe_json_response(response)
                self.ldap_results.append(response_json) if response_json else self.ldap_results.append(
                    {
                        "description": f"{gitlab_post_description}",
                        "message": "Error. None returned for JSON result", 
                        "error": response.text if response else "Response was None"
                    })
            # TODO: Decide how error handling or output might work
