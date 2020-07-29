import mock
import json
import congregate.helpers.bitbucket_client as bbc


def test_get_user_objects_from_user_search_and_user_use_email_for_user_name_false():
    user_search = [
        {
            "username": "should_be_this_user_name",
            "id": "user_id"
        }
    ]
    user = {
        "permission": "PROJECT_ADMIN"
    }
    users_map = {
        "should_be_this": ""
    }
    retval = bbc.get_user_objects_from_user_search_and_user(
        user_search,
        user,
        users_map
    )
    assert retval["user_name"] == "should_be_this_user_name"
    assert retval == {'user_data': {'access_level': 50, 'user_id': 'user_id'}, 'user_id': 'user_id',
                      'user_name': 'should_be_this_user_name',
                      'users_map': {'should_be_this': '', 'should_be_this_user_name': 'user_id'}}


def test_get_user_objects_from_user_search_and_user_use_email_for_user_name_true():
    user_search = [
        {
            "username": "should_be_this_user_name",
            "id": "user_id",
            "email": "should_be_this_email_name@abc.com"
        }
    ]
    user = {
        "permission": "PROJECT_ADMIN"
    }
    users_map = {
        "should_be_this": ""
    }
    retval = bbc.get_user_objects_from_user_search_and_user(
        user_search,
        user,
        users_map,
        True
    )
    assert retval["user_name"] == "should_be_this_email_name"
    assert retval == {'user_data': {'access_level': 50, 'user_id': 'user_id'}, 'user_id': 'user_id',
                      'user_name': 'should_be_this_email_name',
                      'users_map': {'should_be_this': '', 'should_be_this_email_name': 'user_id'}}


class MockHex:
    def __init__(self):
        self.hex = "aaaa"


def mock_uuid():
    return MockHex()


class MockApiReturn:
    def __init__(self, j):
        self.j = j
        pass

    def read(self):
        return self.j

    def json(self):
        return self.j


@mock.patch('congregate.helpers.bitbucket_client.uuid4', side_effect=mock_uuid)
def test_new_user_data_from_user(uuid):
    user = {
        "email": "expected@email.com",
        "name": "name",
        "displayName": "displayname",
        "username": "username"
    }
    newuser = bbc.new_user_data_from_user(user)
    expected = {
        "email": "expected@email.com",
        "skip_confirmation": True,
        "username": "username",
        "name": "displayname",
        "password": MockHex().hex
    }
    assert newuser == expected


"""    
:param api_get: mock patch
:return: Doesn't test anything, yet. Just setting up some framework. Should side-effect and intercept parameters
to inject in to the actual return string
"""
@mock.patch('congregate.helpers.bitbucket_client.api.generate_get_request')
def test_user_search_by_email_or_name(api_get):
    user_return_string = '[{"id": 1,"username": "john_smith","name": "John Smith","state": "active","avatar_url": "http://localhost:3000/uploads/user/avatar/1/cd8.jpeg"}]'
    user_return_dict = json.loads(user_return_string)[0]
    api_get.return_value = MockApiReturn(user_return_string)
    return_value = json.loads(bbc.user_search_by_email_or_name('junk'))
    ret_dict = return_value[0]
    shared_items = {k: ret_dict[k] for k in ret_dict if k in user_return_dict and ret_dict[k] == user_return_dict[k]}
    assert len(shared_items) == len(user_return_dict) == len(ret_dict)


@mock.patch('congregate.helpers.bitbucket_client.api.generate_get_request')
def test_group_search_by_name(api_get):
    groups_return_string = '[{"id": 1,"name": "Foobar Group","path": "foo-bar","description": "An interesting group","visibility": "public","lfs_enabled": true,"avatar_url": "http://localhost:3000/uploads/group/avatar/1/foo.jpg","request_access_enabled": false,"full_name": "Foobar Group","full_path": "foo-bar","file_template_project_id": 1,"parent_id": null}]'
    groups_return_dict = json.loads(groups_return_string)[0]
    api_get.return_value = MockApiReturn(groups_return_string)
    return_value = json.loads(bbc.group_search_by_name('group_name'))
    return_dict = return_value[0]
    shared_items = {k: return_dict[k] for k in return_dict if
                    k in groups_return_dict and return_dict[k] == groups_return_dict[k]}
    assert len(shared_items) == len(return_dict)
