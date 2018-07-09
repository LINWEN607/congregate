#!/bin/bash

config=$(cat data/config.json | jq '.config')
host=$(echo $config | jq -r '.child_instance_host')
token=$(echo $config | jq -r '.child_instance_token')

users=$(curl -s --request GET --header "PRIVATE-TOKEN: $token" $host/api/v4/users | jq 'del(.[] | select(.id == 1))')
jsonArray=$(jq -n '[]')
for ((i=0;i<`echo $users | jq '. | length'`;i++));
do
    cleanup=$(echo $users | jq ".[$i] | del(.web_url, .last_sign_in_at, .last_activity_at, .current_sign_in_at, .can_create_project, .two_factor_enabled, .avatar_url, .created_at, .confirmed_at, .last_activity_on, .id, .state)")
    cleanup=$(echo $cleanup | jq ". + {reset_password: true}")
    jsonArray=$(echo $jsonArray | jq --argjson i "$cleanup" '. += [$i]')
done

echo $jsonArray | jq . > data/users.json

if [ "$1" = "status" ]; then
    num=$(echo $jsonArray | jq '. | length')
    echo "Retrieved $num users. Check users.json to see all retrieved groups"
fi