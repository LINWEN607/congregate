from congregate.migration.user_authorization.classes.instances import Gitlab_Instance
from congregate.migration.user_authorization.classes.instances import Bitbucket_Instance
from congregate.migration.user_authorization.classes.repo import Repo
from congregate.migration.user_authorization.classes.user import User
from congregate.migration.user_authorization.classes.level import Level
from congregate.migration.user_authorization.classes.user_and_repo_operations import User_And_Repo_Operations
from congregate.helpers import conf
import logging

config = conf.Config()


def user_is_authorized(migration_type, **kwargs):
    """
    Function that checks whether a user is authorized to perform migration for a Bitbucket repository or project.

    :param migration_type: Repository or Project
    :type migration_type: str
    :keyword https_clone_url: Bitbucket https clone url of the repo. If migration_type is "Project", this can be
    the https clone url of any repository in the project.
    :keyword repo_name: Name of the repo
    :keyword first_name: First name of the user to check authorization for
    :keyword last_name: Last name of the user to check authorization for
    :keyword email: Email address of the user to check authorization for
    :keyword build_user_id: User ID to of the user to check authorization for
    :keyword bb_username: Username of an admin service account for the Bitbucket instance
    :keyword bb_password: Password of an admin service account for the Bitbucket instance

    :return: A boolean representing whether the user is authorized to migrate the given project or repo
    """
    assert migration_type != None
    assert migration_type.lower() == 'repository' or migration_type.lower() == 'project'
    bb_api_url_base = '%s/rest/api/1.0' % config.external_source_url
    gitlab_api_url_base = "%s/api/v4/" % config.destination_host
    bitbucket_instance = Bitbucket_Instance(bb_api_url_base, config.external_user_name, config.external_user_password)
    gitlab_instance = Gitlab_Instance(gitlab_api_url_base)
    repo = Repo(
        https_clone_url=kwargs['https_clone_url'],
        repo_name=kwargs['repo_name'],
        bitbucket_instance=bitbucket_instance,
        gitlab_instance=gitlab_instance
    )
    user = User(
        first_name=kwargs['first_name'],
        last_name=kwargs['last_name'],
        email=kwargs['email'],
        build_user_id=kwargs['build_user_id']
    )
    ops = User_And_Repo_Operations(repo, user)
    repo_level = Level("bitbucket_repo")
    project_level = Level("bitbucket_project")
    bb_repo_permission = ops.get_bitbucket_user_permission_at_level(level=repo_level)
    bb_project_permission = ops.get_bitbucket_user_permission_at_level(level=project_level)
    if bb_repo_permission is not None:
        is_repo_admin = True if bb_repo_permission.lower() == 'repo_admin' else False
    else:
        is_repo_admin = False
    if bb_project_permission is not None:
        is_project_admin = True if bb_project_permission.lower() == 'project_admin' else False
    else:
        is_project_admin = False

    if migration_type.lower() == 'repository':
        logging.info('Repository admin status: %s' % is_repo_admin)
        logging.info('Project admin status: %s' % is_project_admin)
        if is_repo_admin or is_project_admin:
            return True
        else:
            return False
    elif migration_type.lower() == 'project':
        logging.info('Project admin status: %s' % is_project_admin)
        if is_project_admin:
            return True
        else:
            return False


def user_authorization_main(migration_type, **kwargs):
    """
    Function that runs the full user authorization process for a migration, including all logging.
    If the user is not authorized for migration, it will raise an error.

    :param migration_type: Repository or Project
    :type migration_type: str
    :keyword https_clone_url: Bitbucket https clone url of the repo. If migration_type is "Project", this can be
    the https clone url of any repository in the project.
    :keyword repo_name: Name of the repo
    :keyword first_name: First name of the user to check authorization for
    :keyword last_name: Last name of the user to check authorization for
    :keyword email: Email address of the user to check authorization for
    :keyword build_user_id: build_user_id of the user to check authorization for
    :keyword bb_username: Username of an admin service account for the Bitbucket instance
    :keyword bb_password: Password of an admin service account for the Bitbucket instance

    :return: A boolean representing whether the user is authorized to migrate the given project or repo
    """
    logging.info('\nName: %s %s' % (kwargs['first_name'], kwargs['last_name']))
    allow_migration = user_is_authorized(migration_type, **kwargs)
    logging.info('Allow migration: %s' % allow_migration)
    if not allow_migration:
        if migration_type.lower() == 'repository':
            raise RuntimeError("Admin status could not be confirmed for the executor. Please confirm that you are a repository admin or project admin and try again.")
        elif migration_type.lower() == 'project':
            raise RuntimeError(
                "Admin status could not be confirmed for the executor. Please confirm that you are an admin of this project and try again.")