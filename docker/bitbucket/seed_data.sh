#!/bin/bash

create_project_repo () {
    projectkey=$1
    repopath=$2
    reponame=$3
    git clone $repopath
    cd $reponame
    curl -X POST --user $auth:$password \
        -H "X-Atlassian-Token: no-check" \
        -H "Content-Type: application/json" \
        "http://localhost:7990/rest/api/1.0/projects/$projectkey/repos" \
        --data-binary @- << EOF
        {
            "name": "$reponame",
            "is_private": "true"
        }
EOF
    git remote remove origin
    git remote add origin http://$auth:$password@localhost:7990/scm/$projectkey/$reponame.git
    git push -u origin --all
    git push -u origin --tags
    cd ..
}

create_user () {
    username=$1
    curl -X POST --user $auth:$password \
         -H "X-Atlassian-Token: no-check" \
         "http://localhost:7990/rest/api/1.0/admin/users?name=$username&password=password&displayName=$username&emailAddress=$username@example.com"
}

create_project () {
    groupkey=$1
    groupname=$2
    curl -X POST --user $auth:$password \
        -H "X-Atlassian-Token: no-check" \
        -H "Content-Type: application/json" \
        "http://localhost:7990/rest/api/1.0/projects" \
        --data-binary @- << EOF
        {
            "name": "$groupname",
            "key": "$groupkey",
            "description": "test"
        }
EOF
}

add_users_to_group () {
    group=$1
    users=$2
    curl --user $auth:$password \
         http://localhost:7990/rest/api/1.0/admin/groups/ \
         --data $(group_user_data)
}

group_user_data () {
  cat <<EOF
    { 
        "group": "$group",
        "users": $(to_json_array "$users") 
    }
EOF
}

to_json_array () {
    X=($@)
    for f in "${X[@]}"; do 
        printf '%s' "$f" | jq -R -s .; 
    done | jq -s .
}

auth=admin
password=$BITBUCKET_PASSWORD
users=(user1 user2 user3 user4 user5)

echo "Restarting Bitbucket server"
    /opt/atlassian/bitbucket/bin/stop-bitbucket.sh
    /opt/atlassian/bitbucket/bin/start-bitbucket.sh


if [ ! -d "/opt/test-repos" ]; then
    echo "Seeding data"

    for user in ${users[@]}; do
        echo "Creating user $user"
        create_user "$user"
    done

    cd /opt
    mkdir -p test-repos
    cd test-repos

    repos=(
        "https://github.com/pypa/pip.git"
        "https://gitlab.com/pages/plain-html.git"
        "https://github.com/nodejs/node.git"
        "https://gitlab.com/gitlab-org/project-templates/spring.git",
        "https://gitlab.com/gitlab-org/project-templates/react.git",
        "https://gitlab.com/gitlab-org/project-templates/android.git"
    )

    create_project "TGP" "test-group"

    for repo in ${repos[@]}; do
        echo "Creating new repository from $repo"
        reponame=$(echo $repo | awk -F/ '{ print $NF}' | awk -F. '{ print $1 }')
        create_project_repo "TGP" "$repo" "$reponame"
    done
fi

