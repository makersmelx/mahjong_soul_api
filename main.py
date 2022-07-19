import asyncio
import json
import logging

from optparse import OptionParser
from urllib import response
from ms.majsoul import Majsoul, MajsoulGameMode
import ms.protocol_pb2 as pb
from google.protobuf.json_format import MessageToJson

MS_HOST = "https://game.maj-soul.com"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


async def main():
    """
    Login to the CN server with username and password and get latest 30 game logs.
    """
    parser = OptionParser()
    parser.add_option("-l", "--log", type="string",
                      help="Your log UUID for load.")
    parser.add_option("-c", "--config", type="string",
                      help="Path to the config file to use")

    opts, _ = parser.parse_args()
    log_uuid = opts.log
    config = opts.config

    majsoul = await Majsoul(config)

    if not log_uuid:
        game_logs = await load_game_logs(majsoul.lobby)
        logging.info("Found {} records".format(len(game_logs)))
    else:
        game_log = await load_and_process_game_log(majsoul.lobby, log_uuid)
        logging.info("game {} result : \n{}".format(
            game_log.head.uuid, game_log.head.result))


async def load_game_logs(lobby):
    logging.info("Loading game logs")

    records = []
    current = 1
    step = 30
    req = pb.ReqGameRecordList()
    req.start = current
    req.count = step
    res = await lobby.fetch_game_record_list(req)
    records.extend([r.uuid for r in res.record_list])

    return records


async def load_and_process_game_log(lobby, uuid):
    logging.info("Loading game log")

    req = pb.ReqGameRecord()
    req.game_uuid = uuid
    req.client_version_string = 'web-0.9.333'
    res = await lobby.fetch_game_record(req)

    record_wrapper = pb.Wrapper()
    record_wrapper.ParseFromString(res.data)

    game_details = pb.GameDetailRecords()
    game_details.ParseFromString(record_wrapper.data)

    game_records_count = len(game_details.records)
    logging.info("Found {} game records".format(game_records_count))

    round_record_wrapper = pb.Wrapper()
    is_show_new_round_record = False
    is_show_discard_tile = False
    is_show_deal_tile = False

    for i in range(0, game_records_count):
        round_record_wrapper.ParseFromString(game_details.records[i])

        if round_record_wrapper.name == ".lq.RecordNewRound" and not is_show_new_round_record:
            logging.info("Found record type = {}".format(
                round_record_wrapper.name))
            round_data = pb.RecordNewRound()
            round_data.ParseFromString(round_record_wrapper.data)
            print_data_as_json(round_data, "RecordNewRound")
            is_show_new_round_record = True

        if round_record_wrapper.name == ".lq.RecordDiscardTile" and not is_show_discard_tile:
            logging.info("Found record type = {}".format(
                round_record_wrapper.name))
            discard_tile = pb.RecordDiscardTile()
            discard_tile.ParseFromString(round_record_wrapper.data)
            print_data_as_json(discard_tile, "RecordDiscardTile")
            is_show_discard_tile = True

        if round_record_wrapper.name == ".lq.RecordDealTile" and not is_show_deal_tile:
            logging.info("Found record type = {}".format(
                round_record_wrapper.name))
            deal_tile = pb.RecordDealTile()
            deal_tile.ParseFromString(round_record_wrapper.data)
            print_data_as_json(deal_tile, "RecordDealTile")
            is_show_deal_tile = True

    return res


def print_data_as_json(data, type):
    json = MessageToJson(data)
    logging.info("{} json {}".format(type, json))


if __name__ == "__main__":
    asyncio.run(main())
