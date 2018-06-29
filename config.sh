#!/bin/bash

#
# Bash script to generate configuration JSON for congregate
#

echo "##Configuring congregate"

echo "1. Host of parent instance (destination instance)"
read parent_instance_host
config=$(jq -n --arg i "$parent_instance_host" '{"parent_instance_host": $i}')

echo "2. Access token to use for parent instance"
read parent_instance_token
config=$(echo $config | jq --arg i "$parent_instance_token" '. + {parent_instance_token: $i}')

echo "3. Host of child instance (destination instance)"
read child_instance_host
config=$(echo $config | jq --arg i "$child_instance_host" '. + {child_instance_host: $i}')

echo "4. Access token to use for child instance"
read child_instance_token
config=$(echo $config | jq --arg i "$child_instance_token" '. + {child_instance_token: $i}')

echo "5. Staging location type for exported projects? (default: filesystem)"
read location
if [ -z $location ]; then
    config=$(echo $config | jq '. + {location: "filesystem"}')
    location="filesystem"
else
    config=$(echo $config | jq --arg i "$location" '. + {location: $i}')
fi

if [ "$location" == "filesystem" ]; then
    echo "6. Absolute path for exported projects? (default: $(pwd))"
    read path
    if [ -z $path ]; then
        config=$(echo $config | jq '. + {path: "./"}')
    else
        config=$(echo $config | jq --arg i "$path" '. + {path: $i}')
    fi
elif [ "$location" == "aws" ] || [ "$location" == "AWS" ]; then
    asdf="asdf"
    #generate pre-signed url here
fi

config=$(jq -n --argjson i "$config" '{config: $i}')
echo $config | jq . > config.json

echo "Congregate has been successfully configured"
