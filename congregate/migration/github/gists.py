from congregate.helpers.base_class import BaseClass
from congregate.helpers.processes import start_multi_process_stream
from congregate.migration.github.api.gists import GistsApi
from congregate.helpers.misc_utils import safe_json_response, is_error_message_present


class GistsClient(BaseClass):
    def __init__(self):
        super(GistsClient, self).__init__()
        self.gists_api = GistsApi(self.config.source_host,
                                  self.config.source_token)

    def retreive_public_gists(self):
        """
        List and transform all GitHub gist to GitLab gist metadata
        """
        self.gists_api.get_public_gists()

    def transform_gists(self, gists):
        data = []
        for gist in gists:
            single_gist = safe_json_response(
                self.gists_api.get_single_gist(gist["id"]))
            if not single_gist or is_error_message_present(single_gist):
                self.log.error("Failed to get JSON for gist {} ({})".format(
                    gist["id"], single_gist))
            else:
                data.append(self.transform_gist(single_gist))
        return data

    def transform_gist(self, single_gist):
        # GitHub has no title equivalent
        if single_gist["public"]:
            visibility = "public"
        else:
            visibility = "private"
        return {
            "description": single_gist["description"],
            "visibility": visibility,
        }
