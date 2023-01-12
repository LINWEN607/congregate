#!/bin/bash

CLONE_URL="$1"
DEST_CLONE_URL="$2"
REPO_NAME="$3"

function usage(){  
    echo "Usage: $0 [SVN Repository] [DEST_CLONE_URL] [REPOSITORY NAME]"  
    echo "Example: $0 svn+ssh://<username>@svn_web git@gitlab.com:namespace or https://gitlab.example.com/namespace SVN_REPO"
    echo "During the script, user needs to input source SSH/HTTPS clone url such as ssh://<username>@<the server name>:<port number>"
    echo "And destination SSH/HTTPS clone url such as git@gitlab.com"
    exit 1  
} 

GIT_SVN_VERSION=$(git svn --version | grep "version" | awk '{print $3}')

if [[ "$GIT_SVN_VERSION" ]]; then
    echo "git svn was installed"
    if [ $# -ne 3 ] ; then
        usage
    else
        if read -r -p "Do we need to generate authors-transform.txt [Y/N] " response && 
            [[ $response =~ ^([yY][eE][sS]|[yY])$ ]]; then
            svn log -q | awk -F '|' '/^r/ {sub("^ ", "", $2); sub(" $", "", $2); print $2" = "$2" <"$2">"}' | sort -u > authors-transform.txt
        fi 
        echo "Please make sure to modify the authors-transform.txt, the format should be flastname = FirstName Lastname <flastname@gitlab.com> "
        
        read -r -p "What is the TRUNK of SVN repository? " TRUNK
        read -r -p "What is the TAG of SVN repository? " TAG
        
        echo "The source repository clone URL: $CLONE_URL --trunk=/$TRUNK --tags=/$TAG $REPO_NAME "
        git svn clone $CLONE_URL --authors-file=authors-transform.txt --trunk=/$TRUNK --tags=/$TAG $REPO_NAME
        cd "${REPO_NAME}"
        
        echo "In $(pwd)"
        for b in $(git for-each-ref --format='%(refname:short)' refs/remotes); do git branch $b refs/remotes/$b && git branch -D -r $b; done
        echo "Listing all the branches coverted from SVN Repository"
        git branch -a

        while read -r -p "Is there any tags need to be converted from SVN? [Y/N] " is_tag && 
            [[ $is_tag =~ ^([yY][eE][sS]|[yY])$ ]]
        do
            read -r -p "What is the tag converted from SVN? " tag_name

            git tag -a -m "Migrating SVN tag" $tag_name origin/tags/$tag_name
            echo "Listing all the tags coverted from SVN Repository Tag folder $REPO_NAME"
            git tag -l
            
        done

        echo "The new repo url: $DEST_CLONE_URL/${REPO_NAME}"
        read -p 'Press [Enter] key to continue...' 
        git remote add origin "$DEST_CLONE_URL/${REPO_NAME}"
        echo "Pushing all the branches from SVN ${REPO_NAME} tag folder to GitLab"
        git push -u origin --all || return 1
        read -p 'Press [Enter] key to continue...'
        if read -r -p "Pushing all the Tags from generic Git repository to GitLab [Y/N] " response && 
            [[ $response =~ ^([yY][eE][sS]|[yY])$ ]]; then
            git push -u origin --tags || return 1
        fi
        echo "Migration Complete!"
    fi
else
    echo "git svn needs to be installed"; exit 1
    
fi
