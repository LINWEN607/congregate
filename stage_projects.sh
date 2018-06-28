#!/bin/bash

## Checking for cached project file
if [ ! -f project_json.json ]; then
    ./list_projects > /dev/null
fi

projects=$(cat project_json.json)

if [ "$1" = "all" ] || [ "$1" = "." ]; then
    staging=$(jq -n '[]')
    for ((i=0;i<`echo $projects | jq '. | length'`;i++));
    do
        id=$(echo $projects | jq -r ".[$i] .id")
        name=$(echo $projects | jq -r ".[$i] .name")
        staging=$(echo $staging | jq --arg name "$name" --arg id "$id" '. += [{"id": $id, "name": $name}]')
    done
else
    staging=$(jq -n '[]')
    for project in $@
    do
        project=$(echo $projects | jq --argjson i "$project" '.[] | select(.id == $i)')
        id=$(echo $project | jq -r ".id")
        name=$(echo $project | jq -r ".name")
        staging=$(echo $staging | jq --arg name "$name" --arg id "$id" '. += [{"id": $id, "name": $name}]')
    done
fi

if [[ ! -z $staging ]]; then
    echo $staging | jq . > stage.json
fi