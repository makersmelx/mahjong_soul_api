import random
import re
from sys import stderr
import requests

URL_BASE = 'https://game.maj-soul.com/1/'
MAX_ATTEMPT_PER_SERVER = 2
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36"
HEADERS = {
    "User-Agent": USER_AGENT,
    "If-Modified-Since": "0",
    "Referer": URL_BASE,
    "sec-ch-ua": '"Chromium";v="100", "Google Chrome";v="100"',
    "sec-ch-ua-platform": "Windows",
}


def save_liqi_json(json_string: str):
    with open("setup/liqi.json", 'w+') as file:
        file.write(json_string)

def get_endpoint_and_version():
    # Parts below are hard-coded according to mahjong soul api (2022-07-14)
    # notify the author if this part throws KeyError
    majsoul_version, game_server_endpoint = '', ''

    session = requests.Session()
    session.headers = HEADERS

    def get_majsoul_resource(path: str):
        url = URL_BASE + path
        return session.get(url).json()

    try:
        ws_scheme = 'wss'
        version = get_majsoul_resource("version.json")
        resversion = get_majsoul_resource(
            'resversion{}.json'.format(version['version']))
        liqi_json = resversion['res']["res/proto/liqi.json"]
        protobuf_version = liqi_json['prefix']
        protobuf_schema = get_majsoul_resource(
            '{}/res/proto/liqi.json'.format(protobuf_version))
        config = get_majsoul_resource(
            '{}/config.json'.format(resversion['res']['config.json']['prefix']))
        ip_config = [x for x in config['ip'] if x['name'] == 'player'][0]
        # a list of urls where we can request for game server information
        request_game_server_endpoint_list = ip_config['region_urls']
    except KeyError as e:
        print(e, stderr)
        print("Majsoul api may have changed. Please notify the author.")

    last_error: Exception = None

    for attempt in range(len(request_game_server_endpoint_list) * MAX_ATTEMPT_PER_SERVER):
        request_game_server_endpoint = request_game_server_endpoint_list[
            attempt // MAX_ATTEMPT_PER_SERVER]['url']
        # the final url where we request for game server info
        # javascript float type has 17 digits after the dot.
        request_game_server_endpoint \
            += "?service=ws-gateway&protocol=ws&ssl=true&rv=" \
            + str(random.random())[2:].ljust(17, '0')

        try:
            game_server_info = session.get(request_game_server_endpoint).json()
            # check maintenance
            if 'maintenance' in game_server_info:
                print("Majsoul is in maintenance")
                return

            game_server_endpoint = random.choice(game_server_info["servers"])

            if 'maj-soul' in game_server_endpoint:
                game_server_endpoint += '/gateway'
            break

        except Exception as e:
            last_error = e
            print(e, stderr)
            continue

    # failed to fetch game servers
    if last_error:
        print(e, stderr)
        raise last_error
    majsoul_version = "v" + re.sub(r'.[a-z]+$', "", version['version'])
    game_server_endpoint = "{}://{}/".format(ws_scheme, game_server_endpoint)
    save_liqi_json(liqi_json)
    return game_server_endpoint, majsoul_version


if __name__ == '__main__':
    get_endpoint_and_version()
