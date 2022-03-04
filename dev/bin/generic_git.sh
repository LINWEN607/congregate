#!/usr/bin/bash

repo_name="$1"
target_group="$2"

push_branches='refs/remotes/old-origin/*:refs/heads/*'

function usage(){  
    echo "Usage: $0 [original repo with group name] [target group_name] "  
    echo "Example: $0 abc.git <test> "
    echo "During the script, user need to input source SSH clone url such as ssh://<username>@<the server name>:29418"
    echo "And destination SSH clone url such as git@gitlab.com"
    exit 1  
 } 

if [ $# -ne 2 ] ; then
    usage
else
    echo "What is the clone URL from source instance?"
    echo "For example, for Gerrit migration:  ssh://<username>@<the server name>:29418"
    read source_clone_url
    echo "The source repository clone URL: $source_clone_url/${repo_name##*/}"
    git clone "$source_clone_url/$repo_name" 
    cd ${repo_name##*/}
    echo "where am I"
    pwd
    echo "What is the clone URL for destination instance?"
    echo "For example, for GitLab: git@gitlab.com"
    read dest_clone_url
    echo "The new repo url: $dest_clone_url:$target_group/${repo_name}"
    read -p 'Press [Enter] key to continue...'
    git remote rename origin old-origin 
    git remote add origin "git@gitlab.com:$target_group/${repo_name}"
    echo "Pushing all the branches from Gerrit to GitLab including LFS"
    git push origin $push_branches
    read -p 'Press [Enter] key to continue...'
    echo "Pushing all the rags from Gerrit to GitLab including LFS"
    git push -u origin --tags
    echo "Migration Completes!"
fi


