#!/bin/bash
set -e
CLONE_URL="$1"
REPO_NAME="${CLONE_URL##*/}"
PUSH_BRANCHES='refs/remotes/old-origin/*:refs/heads/*'

function usage(){  
    echo "Usage: $0 [original repo with group name]"  
    echo "Example: $0 git@gitlab.com:namespace/abc.git"
    echo "During the script, user needs to input source SSH/HTTPS clone url such as ssh://<username>@<the server name>:29418"
    echo "And destination SSH/HTTPS clone url such as git@gitlabexample.com"
    exit 1  
} 

if [ $# -ne 1 -a -z "$CLONE_URL" ] ; then
    usage
else
    echo "The source repository clone URL: $CLONE_URL"
    git clone "$CLONE_URL"
    cd "${REPO_NAME/\.git/}"
    echo "In $(pwd)"
    
    read -p "Enter Destination Server URL, not including the reponame i.e. for SSH: git@gitlabexample.com:groupname or HTTPS: https://gitlabexample.com/groupname"
    if [ -z "$DEST_CLONE_URL" ] 
        then 
    echo 'Destination URL is required.  Exiting...' 
        exit 0 
fi 
    
    echo "The new repo url: $DEST_CLONE_URL/${REPO_NAME}"
    read -p 'Press [Enter] key to continue...'
    git remote rename origin old-origin 
    git remote add origin "$DEST_CLONE_URL/${REPO_NAME}"
    
    echo "Pushing all the branches from generic Git repository to GitLab including LFS"
    git push origin $PUSH_BRANCHES || return 1
    read -p 'Press [Enter] key to continue...'
    
    echo "Pushing all the Tags from generic Git repository to GitLab including LFS"
    git push -u origin --tags || return 1
    echo "Migration Complete!"
fi


