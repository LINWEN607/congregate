#!/bin/bash

config=$(cat config.json | jq '.config')
host=$(echo $config | jq -r '.child_instance_host')
token=$(echo $config | jq -r '.child_instance_token')

groups=$(curl -s --request GET --header "PRIVATE-TOKEN: $token" $host/api/v4/groups | jq . ) 

jsonArray=$(jq -n '[]')
for ((i=0;i<`echo $groups | jq '. | length'`;i++));
do
    cleanup=$(echo $groups | jq ".[$i] | del(.web_url, .full_name, .full_path, .ldap_cn, .ldap_access, .id)")
    jsonArray=$(echo $jsonArray | jq --argjson i "$cleanup" '. += [$i]')
done

echo $jsonArray | jq . > groups.json

if [ "$1" = "status" ]; then
    num=$(echo $jsonArray | jq '.[] | length')
    echo "Retrieved $num groups. Check groups.json to see all retrieved groups"
fi
