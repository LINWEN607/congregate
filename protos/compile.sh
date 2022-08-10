#!/bin/bash

#
# Usage: cd into this directory and then run this script
# 

for PROTOBUF in $(ls *.proto)
do
    SRC="${PROTOBUF%%.*}"
    COMPILE_PATH="../congregate/migration/$SRC"
    echo $SRC
    if [ ! -d $COMPILE_PATH ]; then
        echo "No corresponding file for python files found. Creating now"
        mkdir -p $COMPILE_PATH
    fi
    echo "Compiling $SRC gRPC files"
    poetry run python -m grpc_tools.protoc --proto_path=. --python_out=$COMPILE_PATH --grpc_python_out=$COMPILE_PATH ./$PROTOBUF
    echo "$SRC gRPC files have been generated. Be sure to check the imports of $COMPILE_PATH/$SRC_pb2_grpc.py. The imports will be different between the server and the client usage"
done

