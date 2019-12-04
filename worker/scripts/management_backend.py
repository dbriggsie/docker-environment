import logging
import json
import os
import subprocess
import time
from pathlib import Path
import web3
from flask import Flask, request
from flask_cors import CORS
from flask_restplus import Api, Resource
from flask_restplus import abort


from enigma_docker_common.config import Config
from enigma_docker_common.logger import get_logger
logger = get_logger('worker.management_backend')

logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)
logging.getLogger("werkzeug").setLevel(logging.ERROR)

env_defaults = {'K8S': '/root/p2p/config/k8s_config.json',
                'TESTNET': '/root/p2p/config/testnet_config.json',
                'MAINNET': '/root/p2p/config/mainnet_config.json',
                'COMPOSE': '/root/p2p/config/compose_config.json'}

try:
    config = Config(config_file=env_defaults[os.getenv('ENIGMA_ENV', 'COMPOSE')])
except (ValueError, IOError):
    exit(1)

NODE_URL = config["ETH_NODE_ADDRESS"]
provider = web3.HTTPProvider(NODE_URL)
w3 = web3.Web3(provider)

application = Flask(__name__)
CORS(application)

api = Api(app=application, version='1.0')
ns = api.namespace('ethereum', description='Contract operations')
worker = api.namespace('worker', description='Contract operations')
status = ''
eth_address = ''


def get_eth_address():
    global eth_address
    if eth_address:
        return eth_address
    filename = f'{config["ETH_KEY_PATH"]}{config["ETHEREUM_ADDR_FILENAME"]}'
    with open(filename, 'r') as f:
        eth_address = f.read()
        return eth_address


def get_status():
    global status
    filename = f'{config["ETH_KEY_PATH"]}{config["STATUS_FILENAME"]}'
    with open(filename, 'r') as f:
        status = f.read()
        return status


def stop_worker():
    subprocess.call(["supervisorctl", "stop", "p2p"])


def register_workaround():
    subprocess.call(["supervisorctl", "signal", "SIGURG", "p2p"])


def logout_worker():
    subprocess.call(["supervisorctl", "signal", "SIGUSR2", "p2p"])


def login_worker():
    subprocess.call(["supervisorctl", "signal", "SIGUSR1", "p2p"])


def deposit():
    subprocess.call(["supervisorctl", "signal", "SIGSYS", "p2p"])


def withdraw():
    subprocess.call(["supervisorctl", "signal", "64", "p2p"])


def start_worker():
    subprocess.call(["supervisorctl", "start", "p2p"])


@ns.route("/address")
class GetAddress(Resource):
    """ returns a list of tracked addresses for a chain/network. If parameters are empty, will return
    all addresses """
    @ns.param('name', 'Key management address filename -- by default right now can only be principal-sign-addr.txt', 'query')
    def get(self):
        try:
            return get_eth_address()
        except FileNotFoundError as e:
            logger.error(f'Ethereum address not created yet')
            return 'N/A'
        except json.JSONDecodeError as e:
            logger.error(f'Error decoding config file. Is it valid JSON? {e}')
            return abort(500)


@ns.route("/balance")
class GetBalance(Resource):
    """ returns balance for current ethereum account """
    def get(self):
        try:
            account = w3.toChecksumAddress(get_eth_address())
        except FileNotFoundError:
            logger.error(f'Ethereum address not created yet')
            return 'N/A'
        val = w3.fromWei(w3.eth.getBalance(account), 'ether')
        return str(val)


@worker.route("/status")
class GetStatus(Resource):
    """ returns a list of tracked addresses for a chain/network. If parameters are empty, will return
    all addresses """
    def get(self):
        return get_status()


@worker.route("/stop")
class StopWorker(Resource):
    """ Stop the worker (actually just stops the p2p) """
    def post(self):
        return stop_worker()


@worker.route("/start")
class StartWorker(Resource):
    """ Start the worker (actually just starts the p2p) """
    def post(self):
        return start_worker()


@worker.route("/register")
class StartWorker(Resource):
    """ Start the worker (actually just starts the p2p) """
    def post(self):
        return register_workaround()


@worker.route("/login")
class LoginWorker(Resource):
    """ Start the worker (actually just starts the p2p) """
    def post(self):
        return login_worker()


@worker.route("/deposit")
class DepositWorker(Resource):
    """ Start the worker (actually just starts the p2p) """
    def post(self):
        return deposit()


@worker.route("/logout")
class LogoutWorker(Resource):
    """ Start the worker (actually just starts the p2p) """
    def post(self):
        return logout_worker()


@worker.route("/withdraw")
class LogoutWorker(Resource):
    """ Start the worker (actually just starts the p2p) """
    def post(self):
        return withdraw()


def run(port):
    logger.debug("using port:"+str(port))
    application.run(host='0.0.0.0', port=9876, debug=True)


if __name__ == '__main__':
    run(9876)
