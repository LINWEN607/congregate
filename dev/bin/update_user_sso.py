"""
Usage:
    For instances when a user is migrated/created and do not contain the proper saml identity provider
    mapped. This script can be used to update a list of users by providing a csv file using the
    following format:
        "UserEmail","Extern_UID"
        "John.Smith@example.com","extern-uid-from-customer-sso-provider"
        "Jane.Doe@example.com","extern-uid-from-customer-sso-provider"
    Eventual goal is to maybe intergrate into Congregate proper, currently storing within Congregate
    so that the code is not lost in case it is needed in the future.
"""
from urllib.error import HTTPError
from xmlrpc.client import ResponseError
import requests
import csv

headers = {
    'PRIVATE-TOKEN': 'GL Admin PAT',
}

# Default to GitLab.com api url.
api_url = "https://gitlab.com/api/v4"


def getUserId(useremail):
    # API call get user id
    user_url = f'{api_url}/users?search={useremail}'

    try:
        # lookup user by user email
        response = requests.get(user_url, headers=headers)
        response.raise_for_status()
        jsonResponse = response.json()
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
    except Exception as err:
        print(f'Other error occurred: {err}')

    ids_found = len([ele for ele in jsonResponse if isinstance(ele, dict)])
    if ids_found == 1:
        if jsonResponse[0].get("identities"):
            for idents in jsonResponse[0]['identities']:
                if idents['provider'] == "group_saml":
                    print(f"[SKIPPING] User {useremail} already contains group_saml extern_uid.")
                    return None
        user_id = jsonResponse[0]['id']
    elif ids_found == 0:
        print(f"[SKIPPING] No users found in lookup for {useremail}.\n{response.content}")
        return None
    else:
        print(f"Multiple users found in lookup for {useremail}.\n{response.content}")
        print("Please input user id manually.")
        user_id = input("Enter User ID: ")
    return user_id


def updateUserExternUid(user_email, extern_uid, group_id):
    if user_id := getUserId(user_email):
        update_user_url = f'{api_url}/users/{user_id}'
        data = {
            'extern_uid': extern_uid,
            'provider': 'group_saml',
            'group_id_for_saml': group_id
        }

        # Sanity check
        print(f"Updating [{user_id}] - {user_email}:")
        user_data = requests.get(f'{api_url}/users/{user_id}', headers=headers)
        user_content = user_data.json()
        print(user_content)
        if user_content.get("email"):
            if user_content['email'].lower() == user_email.lower():
                print("Emails exact match, skipping manual confirmation.")
                proceed = 'y'
            else:
                proceed = str(input("Proceed with changes? [y/n]: ") or 'n').lower()

        if proceed in ['y', 'yes']:
            response = requests.put(update_user_url, headers=headers, data=data)
            if response.ok:
                print("User %s Updated" % user_email)
            else:
                print(f"User update failed. Status code {response.status_code}\n{response.content}")
        else:
            print("User not updated.")
    else:
        return None


def main():
    with open('test.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            updateUserExternUid(row["UserEmail"], row["Extern_UID"], '12345678')


if __name__ == "__main__":
    main()
