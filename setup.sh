#!/bin/sh
WORK_DIR=$(pwd)
PYTHON="python3"
# Test if python3 is installed
python3 --help > /dev/null &> /dev/null
if [ $? == 0 ]
then
    PYTHON="python3"
else
    PYTHON="python"
fi

echo "Fetching protobuf descriptor \"liqi.json\"..."
poetry run "${PYTHON}" ms/majsoul_server_information.py || exit 1
cd setup
echo "Compiling protobuf python code..."
poetry run "${PYTHON}" generate_proto_file.py || exit 1
protoc --python_out=./ protocol.proto || exit 1
chmod +x ms-plugin.py
export PATH="ms-plugin.py:$PATH"
protoc --custom_out=../ms --plugin=protoc-gen-custom=ms-plugin.py ./protocol.proto || exit 1
mv protocol_pb2.py ../ms
echo "Done"