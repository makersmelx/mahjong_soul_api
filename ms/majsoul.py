import asyncio
import configparser
from enum import IntEnum
import hashlib
import hmac
import logging
from typing import Optional
import uuid
from ms.server_info import get_game_server_info
from ms.rpc import Lobby
from ms.base import MSRPCChannel
import ms.protocol_pb2 as pb


MS_HOST = "https://game.maj-soul.com"
DEFAULT_CONFIG_PATH = "./majsoul_bot.ini"


class MajsoulGameMode(IntEnum):
    # 4-player South
    Throne_4p_South = 216
    Jade_4p_South = 212
    Gold_4p_South = 209

    # 4-player East
    Throne_4p_East = 215
    Jade_4p_East = 211
    Gold_4p_East = 208

    # 3-player South
    Throne_3p_South = 226
    Jade_3p_South = 224
    Gold_3p_South = 222

    # 3-player East
    Throne_3p_East = 225
    Jade_3p_East = 223
    Gold_3p_East = 221

    # todo: implement __str__


class Majsoul:
    lobby: Lobby
    channel: MSRPCChannel
    access_token: Optional[str]
    config: configparser.ConfigParser

    # async constructor
    # stackoverflow: https://stackoverflow.com/a/45364670
    async def __new__(cls, *a, **kw):
        instance = super().__new__(cls)
        await instance.__init__(*a, **kw)
        return instance

    async def __init__(self, config_path=DEFAULT_CONFIG_PATH):
        self.initialize_config(config_path)
        await self.establish_connection()

    async def fetch_live_game_list(self, mode: MajsoulGameMode):
        logging.info("fetching game live list...")
        request = pb.ReqGameLiveList()
        request.filter_id = int(mode)
        response = await self.lobby.fetch_game_live_list(request)
        return response

    # Since destructor cannot be an async task, use event_loop to wait for clean up
    # stackoverflow: https://stackoverflow.com/a/67577364
    def __del__(self):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.clean_up())
            else:
                loop.run_until_complete(self.clean_up())
        except Exception as err:
            logging.warn(f"Clean up fails")
            pass
    '''
    Clean up for the destructor
    '''
    async def clean_up(self):
        await self.channel.close()

    async def establish_connection(self) -> None:
        endpoint, version, _ = get_game_server_info()
        logging.info(f"Chosen endpoint: {endpoint}")
        self.channel = MSRPCChannel(endpoint)
        self.lobby = Lobby(self.channel)
        try:
            await self.channel.connect(MS_HOST)
            logging.info("Connection was established")
        except Exception as err:
            logging.error("Connection failed: {}".format(err))
            exit(1)

        # login
        logging.info("Login with username and password...")
        account_config = self.config['ACCOUNT']
        username, password, secret_key = account_config[
            "username"], account_config['password'], account_config['SecretKey']
        request = pb.ReqLogin()
        request.account = username
        request.password = hmac.new(secret_key.encode(
            'UTF-8'), password.encode(), hashlib.sha256).hexdigest()
        request.device.is_browser = True
        request.random_key = str(uuid.uuid1())
        request.gen_access_token = True
        request.client_version_string = f"web-{version}"
        request.currency_platforms.append(2)

        response = await self.lobby.login(request)
        self.access_token = response.access_token
        if not self.access_token:
            logging.error(f"Login failed. Response: {response}")
            exit(1)
        logging.info("Login succeeds.")

    def initialize_config(self, config_path: str) -> None:
        config_path = config_path or DEFAULT_CONFIG_PATH
        self.config = configparser.ConfigParser()
        self.config.read(config_path)

        # todo: add schema check
