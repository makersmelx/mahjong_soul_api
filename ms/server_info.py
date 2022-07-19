import requests
import logging
import json
import random
import re

URL_BASE = 'https://game.maj-soul.com/1/'
MAX_ATTEMPT_PER_SERVER = 5
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36"
HEADERS = {
    "User-Agent": USER_AGENT,
    "If-Modified-Since": "0",
    "Referer": URL_BASE,
    "sec-ch-ua": '"Chromium";v="100", "Google Chrome";v="100"',
    "sec-ch-ua-platform": "Windows",
}

session = requests.Session()
session.headers = HEADERS


def get_majsoul_resource(path: str):
    url = URL_BASE + path
    for _ in range(MAX_ATTEMPT_PER_SERVER):
        resp = session.get(url)
        if resp.status_code == 200:
            return resp.json()
    logging.error(
        "Just try again. Connection to Majsoul sucks from time to time.")
    exit(1)


def get_game_server_info() -> tuple[str, str, str]:
    '''
    Return a tuple that contains:
        game server endpoint, game version, protobuf version

    Parts below are hard-coded according to mahjong soul api (2022-07-14)
    notify the author if this part throws KeyError
    '''
    majsoul_version, game_server_endpoint, protobuf_version = '', '', ''

    try:
        ws_scheme = 'wss'
        version = get_majsoul_resource("version.json")
        resversion = get_majsoul_resource(
            'resversion{}.json'.format(version['version']))
        config = get_majsoul_resource(
            '{}/config.json'.format(resversion['res']['config.json']['prefix']))
        ip_config = [x for x in config['ip'] if x['name'] == 'player'][0]
        # a list of urls where we can request for game server information
        request_game_server_endpoint_list = ip_config['region_urls']
    except KeyError as e:
        logging.error(e)
        logging.warn("Majsoul api may have changed. Please notify the author.")

    last_error: Exception = None

    for attempt in range(len(request_game_server_endpoint_list) * MAX_ATTEMPT_PER_SERVER):
        logging.info(
            "attempt {}....try fetching majsoul server information".format(attempt))
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
                logging.info("Majsoul is in maintenance")
                return

            game_server_endpoint = random.choice(game_server_info["servers"])

            if 'maj-soul' in game_server_endpoint:
                game_server_endpoint += '/gateway'
            break

        except Exception as e:
            last_error = e
            logging.error(e)
            continue

    # failed to fetch game servers
    if last_error:
        logging.error(e)
        exit(1)

    majsoul_version = "v" + re.sub(r'.[a-z]+$', "", version['version'])
    game_server_endpoint = "{}://{}/".format(ws_scheme, game_server_endpoint)
    protobuf_version = resversion['res']["res/proto/liqi.json"]['prefix']
    logging.info(
        f"Endpoint: {game_server_endpoint}, Version: {majsoul_version}, Protobuf Version: {protobuf_version}")
    return game_server_endpoint, majsoul_version, protobuf_version


def fetch_liqi_json(protobuf_version: str):
    try:
        liqi_json = get_majsoul_resource(
            '{}/res/proto/liqi.json'.format(protobuf_version))
        logging.info("fetch liqi.json succeeds, writing into setup/liqi.json")
        with open("setup/liqi.json", 'w+') as file:
            file.write(json.dumps(liqi_json))
    except Exception as err:
        logging.error(f"fetch liqi.json failed: {err}")
        exit(1)


if __name__ == '__main__':
    _, _, protobuf_version = get_game_server_info()
    fetch_liqi_json(protobuf_version)
