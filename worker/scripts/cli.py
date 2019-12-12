#!/usr/bin/python3

import os
import re
import sys
import time
from web3.auto import w3 as auto_w3

import requests
import click
import progressbar
import six
from PyInquirer import (Token, ValidationError, Validator, print_json, prompt,
                        style_from_dict)

from pyfiglet import figlet_format

from enigma_docker_common.config import Config
from enigma_docker_common import storage

colorama = None

try:
    from termcolor import colored
except ImportError:
    colored = None


env_defaults = {'K8S': '/root/p2p/config/k8s_config.json',
                'TESTNET': '/root/p2p/config/testnet_config.json',
                'MAINNET': '/root/p2p/config/mainnet_config.json',
                'COMPOSE': '/root/p2p/config/compose_config.json'}

try:
    config = Config(config_file=env_defaults[os.getenv('ENIGMA_ENV', 'COMPOSE')])
except (ValueError, IOError):
    exit(1)


staking_address = ''
conf = storage.LocalStorage(directory=config["STAKE_KEY_PATH"], flags='+')


def do_action(action: str):
    resp = requests.get(f'http://localhost:23456/mgmt/{action}')
    if resp.status_code == 200:
        log('YAY great success!', 'green')
    else:
        log('AWW it failed :(', 'red')


def get_status():
    filename = f'{config["ETH_KEY_PATH"]}{config["STATUS_FILENAME"]}'
    with open(filename, 'r') as f:
        status = f.read()
        return status


def get_staking_key():
    filename = f'{config["STAKE_KEY_PATH"]}{config["STAKE_KEY_NAME"]}'
    with open(filename, 'r') as f:
        staking_address = f.read()
        return staking_address


def get_eth_address():
    filename = f'{config["ETH_KEY_PATH"]}{config["ETHEREUM_ADDR_FILENAME"]}'
    with open(filename, 'r') as f:
        eth_address = f.read()
        return eth_address


style = style_from_dict({
    Token.QuestionMark: '#fac731 bold',
    Token.Answer: '#4688f1 bold',
    Token.Instruction: '',  # default
    Token.Separator: '#cc5454',
    Token.Selected: '#0abf5b',  # default
    Token.Pointer: '#673ab7 bold',
    Token.Question: '',
})

commands = ['help', 'exit', 'register', 'login', 'logout']


def getContentType(answer, conttype):
    return answer.get("content_type").lower() == conttype.lower()


def log(string, color, font="slant", figlet=False):
    if colored:
        if not figlet:
            six.print_(colored(string, color))
        else:
            six.print_(colored(figlet_format(
                string, font=font), color))
    else:
        six.print_(string)


class EmptyValidator(Validator):
    def validate(self, value):
        if len(value.text):
            return True
        else:
            raise ValidationError(
                message="You can't leave this blank",
                cursor_position=len(value.text))


class CommandValidator(Validator):
    def validate(self, value):
        if len(value.text):
            if value.text in commands:
                return True

        raise ValidationError(message=f"Invalid command. Choose one of: {commands}")


class FilePathValidator(Validator):
    def validate(self, value):
        if len(value.text):
            if os.path.isfile(value.text):
                return True
            else:
                raise ValidationError(
                    message="File not found",
                    cursor_position=len(value.text))
        else:
            raise ValidationError(
                message="You can't leave this blank",
                cursor_position=len(value.text))


class EthereumAddressValidator(Validator):
    def validate(self, value):
        if len(value.text):
            if not auto_w3.isAddress(value.text):
                raise ValidationError(
                    message="Value is not a valid Etheruem address!")
        else:
            raise ValidationError(
                message="You can't leave this blank",
                cursor_position=len(value.text))


def ask_staking_key():
    questions = [
        {
            'type': 'input',
            'name': 'staking_address',
            'message': 'Enter staking address',
            'validate': EthereumAddressValidator,
        },
    ]
    answers = prompt(questions, style=style)
    return answers


def display_help():
    log('HELPU', 'green')


@click.command()
def main():
    """
    Simple CLI for sending emails using SendGrid
    """
    log("Enigma Secret Node", color="blue", figlet=True)
    log("Welcome to Enigma Secret Node CLI", "green")
    try:
        api_key = conf["staking_address"]
    except FileNotFoundError:
        api_key = ask_staking_key()['staking_address']

    log(f"Staking address is: {api_key}", "green")
    log(f"Are you sure?", "green")
    conf["staking_address"] = api_key
    log(f"Starting up...", "green")

    bar = progressbar.ProgressBar(max_value=progressbar.UnknownLength, enable_colors=True)
    while get_status() != "DOWN":
        time.sleep(0.1)
        bar.update()

    log(f"Generating Node Ethereum address...", "green")
    while True:
        try:
            eth_address = get_eth_address()
            break
        except FileNotFoundError:
            time.sleep(0.1)
            bar.update()

    bar.finish('\nDone!')
    if not eth_address:
        log(f"Failed to load Ethereum address for this node. Try... restarting?", "red")

    log(f"Ethereum address for this node is: {eth_address}", "green")

    while get_status() == 'ETH_LOW':
        log(f"Your current balance is less than the amount required to start (0.1 ETH)", "green")
        log(f"Please transfer more ETH to the node address to continue startup and click any key to continue", "green")
        input("Press Enter to continue...")

    while True:
        cmd = prompt({
            'type': 'input',
            'name': 'content',
            'message': 'Enter command:',
            'validate': CommandValidator,
        })
        if cmd == {}:
            log('Exiting... Goodbye!', 'red')
            break
        if cmd['content'] == 'help':
            display_help()
        elif cmd['content'] == 'exit':
            break
        else:
            do_action(cmd['content'])


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        log('Exiting... Goodbye!', 'red')