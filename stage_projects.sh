#!/bin/bash

## Checking for cached project file
if [ ! -f project_json.json ]; then
    ./list_projects > /dev/null
fi

projects=$(cat data/project_json.json)

if [ "$1" = "all" ] || [ "$1" = "." ]; then
    staging=$(jq -n '[]')
    for ((i=0;i<`echo $projects | jq '. | length'`;i++));
    do
        id=$(echo $projects | jq -r ".[$i] .id")
        name=$(echo $projects | jq -r ".[$i] .name")
        namespace=$(echo $projects | jq -r ".[$i] .path_with_namespace" | cut -d/ -f 1)
        staging=$(echo $staging | jq --arg name "$name" --arg id "$id" --arg namespace "$namespace" '. += [{"id": $id, "name": $name, "namespace": $namespace}]')
    done
else
    staging=$(jq -n '[]')
    for project in $@
    do
        if  [ "$project" -eq "$project" ] 2> /dev/null; then
            project=$(echo $projects | jq --argjson i "$project" '.[] | select(.id == $i)')
        else
            project=$(echo $projects | jq --arg i "$project" '.[] | select(.name == $i)')
        fi
        id=$(echo $project | jq -r ".id")
        name=$(echo $project | jq -r ".name")
        namespace=$(echo $project | jq -r ".path_with_namespace" | cut -d/ -f 1)
        staging=$(echo $staging | jq --arg name "$name" --arg id "$id" --arg namespace "$namespace" '. += [{"id": $id, "name": $name, "namespace": $namespace}]')
    done
fi

if [[ ! -z $staging ]]; then
    echo $staging | jq . > data/stage.json
fi