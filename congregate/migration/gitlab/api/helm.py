from copy import deepcopy as copy
from urllib.parse import quote_plus
from congregate.migration.gitlab.api.base_api import GitLabApiWrapper
from congregate.migration.meta.api_models.helm_package_data import HelmPackageData
import requests

class HelmPackagesApi(GitLabApiWrapper):
    
    def transfer_helm_package(self, src_host, dst_host, src_token, dst_token, src_pid, dst_pid, helm_export_user, helm_import_user, file_name):
        """
        Transfer a Helm Package from Source to Destination

        Gitlab API Doc: https://docs.gitlab.com/ee/user/packages/helm_repository/#publish-a-package

            :param src_host: (str) Gitlab source host url
            :param dst_host: (str) Gitlab destination host url
            :param src_token: (str) Source PAT
            :param dst_token: (str) Destintion PAT
            :param src_pid (int) Gitlab source project ID
            :param dst_pid (int) Gitlab destination project ID
            :param helm_export_user (str) Username of token owner on the source instance
            :param helm_import_user (str) Username of token owner on the destination instance
            :param file_name (str) Package filename
        """

        src_url = f"{src_host}/api/v4/projects/{src_pid}/packages/helm/stable/charts/{file_name}"
        dst_url = f"{dst_host}/api/v4/projects/{dst_pid}/packages/helm/api/stable/charts"

        download_response = requests.get(src_url, auth=(helm_export_user, src_token), stream=True)
        if download_response.status_code == 200:
            download_response.decode_content = False
            files = {
                'chart': (file_name, download_response.raw, download_response.headers['Content-Type'])   
            }
            return requests.post(dst_url, auth=(helm_import_user, dst_token), files=files)
        else:
            error_msg = f'{"error": "Unable to download {file_name}"}'
            bytes_error = error_msg.encode('utf-8')
            download_response._content = bytes_error
            return download_response
