#!/usr/bin/bash

repo_url="$1"
repo_folder="$2"
target_group="$3"

push_branches='refs/remotes/old-origin/*:refs/heads/*'

function usage(){  
    echo "Usage: $0 [original repo url] [repository folder] [target group_name] "  
    exit 1  
 } 

if [ $# -ne 3 ] ; then
    usage
else
    filename=$1
    echo "1. The repo name: ${repo_url##*/}"
    git clone "ssh://admin@$name" $repo_folder
    cd $repo_folder
    echo "2. the new repo url: $target_group/${repo_url##*/}"
    echo "where am I"
    pwd
    read -p 'Press [Enter] key to continue...'
    git remote rename origin old-origin 
    git remote add origin $target_group/${name##*/}
    echo "Pushing all the branches from Gerrit to GitLab including LFS"
    git push origin $push_branches
    read -p 'Press [Enter] key to continue...'
    echo "Pushing all the rags from Gerrit to GitLab including LFS"
    git push -u origin --tags
    echo "Migration Completes!"
fi


