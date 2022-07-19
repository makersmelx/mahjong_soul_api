The idea of repository based on https://github.com/chaserhkj/PyMajSoul/

Python wrappers for Majsoul allow you to interact with their servers from Python scripts.

## For User
Before you start, you should
- know the exact key for password encryption
- keep in mind not to share or post it to public
- **It is a severe security issue.**

1. Install [`poetry`](https://python-poetry.org/)
2. Install python packages from by running
~~~shell
poetry install
~~~
3. copy `examples/majsoul_bot.ini.example` into the root directory. Rename to `majsoul_bot.ini`. Edit the file with your own information.
4. `poetry run python main.py`
5. You can use your own config by adding `-c` or `--config` flag. like `poetry run python main.py -c /path/to/your/config`. Anyway, the file must be in `ini` format.

This example is working only with **Python3.7+**.

Also, you need to have an account from CN server to run this example, because only accounts from CN server has the ability to login with login and password.

If you want to login to EN or JP servers you need to write your code to authenticate via email code or social network. Protobuf wrapper from this repository contains all needed API objects for that.

## For Developer

### Documents for reference
1. Code behind [https://amae-koromo.sapk.ch/](https://amae-koromo.sapk.ch/): [SAPikachu/amae-koromo-scripts](https://github.com/SAPikachu/amae-koromo-scripts/blob/master/logGames.js)
2. Api and protocol reference in Chinese: [takayama-lily/mjsoul](https://github.com/takayama-lily/mjsoul)
### Requirements

1. Install [`poetry`](https://python-poetry.org/) using package manager
2. Install python packages from by running
~~~shell
poetry install
~~~
1. Install protobuf compiler [`protoc`](https://grpc.io/docs/protoc-installation/)

### How to update protocol files to the new version
It was tested on Ubuntu.

1. At the root directory
~~~shell
chmod +x ./setup.sh
./setup.sh
~~~


### How to update protocol files for manager API to the new version

1. Prepare new `liqi_admin.json` file from MS tournament manager panel
1. `python ms_tournament/generate_proto_file.py`
1. `protoc --python_out=. protocol_admin.proto`
1. `chmod +x ms-admin-plugin.py`
1. `sudo cp ms-admin-plugin.py /usr/bin/ms-admin-plugin.py`
1. `protoc --custom_out=. --plugin=protoc-gen-custom=ms-admin-plugin.py ./protocol_admin.proto`
