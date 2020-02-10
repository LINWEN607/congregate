#!/bin/bash

spin_up_instance () {
    pipenv run aws ec2 run-instances \
        --image-id $AMI_ID \
        --count 1 \
        --instance-type t2.large \
        --key-name $KEY_NAME \
        --security-group-ids $SECURITY_GROUP
}

get_instance_ip () {
    pipenv run aws ec2 describe-instances --instance-ids $INSTANCE_ID | jq '.Reservations[0].Instances[0].NetworkInterfaces[0].Association.PublicIp' | tr -d '\n' | sed -e 's/^"//' -e 's/"$//' 
}

echo "Spinning up instance"
INSTANCE_ID=$(spin_up_instance | jq '.Instances[0].InstanceId' | tr -d '\n' | sed -e 's/^"//' -e 's/"$//')

echo $INSTANCE_ID > instance_id

echo $(get_instance_ip)

while [ $(get_instance_ip) == "null" ]; do
    echo "Waiting for instance to start"
    sleep 5
done

printf "$(get_instance_ip)" > source_ip
