import os
import asyncio
import json
import errno
import socket
import time
import psutil
import requests
import sys

from log import Flag
from pythonosc import udp_client, osc_server, dispatcher
from tinyoscquery.query import OSCQueryBrowser, OSCQueryClient
from tinyoscquery.queryservice import OSCQueryService, OSCAccess
from bhaptics.better_haptic_player import BhapticsPosition, connected_positions
from haptics_player import HapticsPlayer
from haptics_handler import HapticsHandler

DEFAULT_DURATION = 100
INTENSITY = 100

class OSCQuery:
    @staticmethod
    def __check_process_is_running():
        """
        (PRIVATE STATIC)return true if vrc is running
        :return: (Bool) result
        """
        for proc in psutil.process_iter():
            ps_name = os.path.splitext(proc.name())[0]

            if ps_name == 'VRChat':
                return True

        return False

    def __init__(self):
        self.http_port: int = 0
        self.osc_port: int = 0
        self.vrchat_client_port = None

        if not OSCQuery.__check_process_is_running():
            print(Flag.Warn.value + "VRC isn't running waiting...")
            try:
                while not OSCQuery.__check_process_is_running():
                    time.sleep(1)
            except KeyboardInterrupt:
                sys.exit(0)

        # find free udp port and set osc_port
        self.__get_free_udp_port()
        # find free tcp port and set http_port
        self.__get_free_tcp_port()

        self.oscQueryService = OSCQueryService("bHapticsOSCQ", self.http_port, self.osc_port)
        self.oscQueryService.advertise_endpoint("/avatar/parameters/MuteSelf", False, OSCAccess.WRITEONLY_VALUE)

        self.browser = OSCQueryBrowser()
        # wait for discovery
        time.sleep(2)

        while self.vrchat_client_port is None:
            for service_info in self.browser.get_discovered_oscquery():
                client = OSCQueryClient(service_info)

                if 'VRChat-Client' in client.service_info.name:
                    self.vrchat_client_port = client.service_info.port
                    print(Flag.Info.value + f"VRChat port found: {self.vrchat_client_port}")

                time.sleep(1)

    def __get_free_udp_port(self):
        """
        (PRIVATE) set udp port
        :return: NONE
        """

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            udp_socket.bind(('localhost', 0))
            port = udp_socket.getsockname()[1]

            self.osc_port = port

            print(Flag.Info.value + "getting OSC port has been completed")

    def __get_free_tcp_port(self):
        """
        (PRIVATE) set tcp port
        :return: NONE
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
            tcp_socket.bind(('localhost', 0))
            tcp_socket.listen(1)
            port = tcp_socket.getsockname()[1]

            self.http_port = port
            print(Flag.Info.value + "getting TCP port has been completed")

    # <method that returns class variable>
    def get_osc_port(self) -> int:
        """
        get UDP port number for osc
        :return: (Int) port number for osc
        """
        return self.osc_port

    def get_http_port(self) -> int:
        """
        get TCP port number for http connection
        :return: (Int) port number for http connection
        """
        return self.http_port

    def get_current_avatar(self) -> str:
        """
        get current avatar id
        :return: (String) Avatar ID
        """

        try:
            while True:
                response = requests.get(f"http://127.0.0.1:{self.vrchat_client_port}/avatar/change", timeout=5)

                if response.status_code == 200:
                    json_data = response.json()
                    return json_data['VALUE'][0]

                time.sleep(1)
        except requests.exceptions.RequestException as e:
            print(Flag.Warn.value + f"Error while fetching avatar: {e}")
            return "Unknown"
        except Exception as e:
            print(Flag.Warn.value + f"Unexpected error: {e}")
            return "Unknown"

    def get_avatar_prmt(self) -> dict:
        """
        get current avatar's parameters
        :return: (Dictionary) parameters
        """
        response = requests.get(f"http://127.0.0.1:{self.vrchat_client_port}/avatar/parameters")

        if response.status_code == 200:
            prmt = response.json()
            return prmt
    # </method that returns class variable>


class Config:
    CONFIG_VERSION = 2

    def __init__(self):
        # <NETWORK>
        self.ip_addr: str = "127.0.0.1"
        # </NETWORK>

        if self.load() == errno.ENOENT:
            print(Flag.Info.value + "there's no config file. now create new one.")
            self.save()

    def load(self, _file: str = "./config.json") -> int:
        """
        load config file
        :param _file: [optional] (String) file path that have setting value (json format)
        :return: (Int) errno more information see this page https://docs.python.org/3/library/errno.html
        """
        try:
            with open(_file, 'r', encoding='utf-8') as f:
                raw = json.load(f)

                self.ip_addr = raw["NETWORK"]["ip"]

                if self.CONFIG_VERSION != raw["CONFIG_VERSION"]:
                    print(Flag.Info.value + "Config file version is not match. Now create new one. \033")
                    self.save()

                return 0
        except IOError as e:
            return e.errno
        except KeyError:
            print(Flag.Warn.value + "Config file is not correct format. Now create new one. \033")
            self.save()
        except Exception as e:
            raise e

    def save(self, _file: str = "./config.json") -> int:
        """
        create or update config file
        :param _file: [optional] (String) file path that config file saved
        :return: (Int) errno, You can get more information from this page https://docs.python.org/3/library/errno.html
        """

        try:
            with open(_file, "w", encoding='utf-8') as f:
                f.write(self.tojson())
                print(Flag.Info.value + '**CONFIG DATA SAVE COMPLETE**')
                return 0
        except IOError as e:
            return e.errno
        except Exception as e:
            print(e)
            raise e

    def tojson(self) -> str:
        """
        convert config class to json
        :return: (String) convert class variable to json format string
        """

        d_net = {
            "ip": self.ip_addr,
        }

        result = {
            "CONFIG_VERSION": self.CONFIG_VERSION,
            "NETWORK": d_net,
        }

        return json.dumps(result, sort_keys=False, indent=4)

    def todict(self):
        s_json: str = self.tojson()
        return json.loads(s_json)


class AvatarConfig:
    def __init__(self):
        self.avatar_id = oscq.get_current_avatar()
        self.avatar_name = self.__get_avatar_name()
        self.avatar_prmt = oscq.get_avatar_prmt()

    def __get_avatar_name(self) -> str:
        """
        (PRIVATE) get avatar name
        :return: (String) avatar name
        """
        oscpath = os.path.expandvars(r'%localappdata%low/VRChat/VRChat/OSC/')

        for (path, _dir, files) in os.walk(oscpath):
            for filename in files:
                ext = os.path.splitext(filename)
                if ext[0] == self.avatar_id:
                    avatar_file = os.path.join(path, filename)
                    with open(avatar_file, 'r', encoding='utf-8-sig') as f:
                        raw = json.load(f)
                        avatar_name = raw['name']
                        return avatar_name

    def update(self, _avatar_id: str):
        """
        update avatarConfig
        :param _avatar_id: (String) changed avatar id
        :return: None
        """
        self.avatar_id = _avatar_id
        self.avatar_name = self.__get_avatar_name()
        self.avatar_prmt = oscq.get_avatar_prmt()

    def get(self) -> tuple:
        """
        get avatar information

        return value information: (id, name, parameters)
        :return: (Tuple) avatar config variables
        """
        result = (self.avatar_id, self.avatar_name, self.avatar_prmt)
        return result


class Receiver:
    @staticmethod
    def build_dispatcher():
        """
        (STATIC) build dispatcher for receiver

        :return: dispatcher object
        """
        d = dispatcher.Dispatcher()

        handler = HapticsHandler(haptics_player)

        d.map("/avatar/change", handler.avi_changed_handler)
        d.map("/avatar/parameters/bHapticsOSC_reset", handler.reset_handler)

        d.map("/avatar/parameters/bHapticsOSC_Head*", handler.head_handler)
        d.map("/avatar/parameters/bHapticsOSC_Arm*", handler.arm_handler)
        d.map("/avatar/parameters/bHapticsOSC_Hand*", handler.hand_handler)
        d.map("/avatar/parameters/bHapticsOSC_Foot*", handler.foot_handler)
        d.map("/avatar/parameters/bHapticsOSC_Glove*",handler.glove_handler)
        d.map("/avatar/parameters/bHapticsOSC_Vest*", handler.vest_handler)

        # <V1 Parameters>
        d.map("/avatar/parameters/bOSC_v1_Vest*", handler.v1_vest_handler)
        d.map("/avatar/parameters/bOSC_v1_Head*", handler.v1_head_handler)
        d.map("/avatar/parameters/bOSC_v1_Forearm*", handler.v1_arm_handler)
        #</V1 Parameters>

        return d

    def __init__(self, _dispatcher: dispatcher.Dispatcher, _ip: str = "127.0.0.1", _port: int = 9001):
        self.ip = _ip
        self.port = _port
        self.dispatcher = _dispatcher

        self.server = osc_server.AsyncIOOSCUDPServer(
            (self.ip, self.port),
            self.dispatcher,
            asyncio.get_running_loop()
        )

        self.transport = None
        self.protocol = None

        print(Flag.Info.value + "server has been created ({}:{})".format(self.ip, self.port))

    async def start(self):
        """
        run receiver
        :return: transport
        """
        self.transport, self.protocol = await self.server.create_serve_endpoint()

        return self.transport


class Sender:
    def __init__(self, _ip: str = "127.0.0.1", _port: int = 9000):
        """
        Create instance that Send OSC packet to server.
        :param _ip: (String) server ip address that send OSC packet
        :param _port: (Int) server ip port that send OSC packet
        """
        self.client = udp_client.SimpleUDPClient(_ip, _port)
        print(Flag.Info.value + f"Client has been created ({_ip}:{_port})")

    def update(self, _ip: str, _port: int):
        """
        Update client destination
        :param _ip: (String) server ip address that send OSC packet
        :param _port: (Int) server ip port that send OSC packet
        :return:
        """
        self.client = udp_client.SimpleUDPClient(_ip, _port)
        print(Flag.Info.value + f"Client has been updated ({_ip}:{_port})")

    async def send(self, ctx, prmt: str, path: str = "/avatar/parameters/", print_info: bool = True):
        """
        send osc packet
        :param ctx: context to send
        :param prmt: VRC parameter name
        :param path: (Optional) parameter path
        :param print_info (Optional) print info or not
        """
        full_path = path + prmt
        self.client.send_message(full_path, ctx)

        if print_info:
            print(Flag.Info.value + f"SEND COMPLETE prm: {prmt} - ctx: ({type(ctx)}) {ctx}")


async def loop():
    print(Flag.Info.value + "START SENDING")

    while True:
        for pos in BhapticsPosition:
            haptics_player.sumit_dot(pos)

        await asyncio.sleep(0.1)

async def main():
    d = Receiver.build_dispatcher()
    receiver = Receiver(d, config.ip_addr, oscq.get_osc_port())
    transport = await receiver.start()

    await asyncio.gather(loop())

    transport.close()

if __name__ == '__main__':
    app_id = "per.Guideung.bHapticsOSCQ"
    app_name = "bHapticsOSCQ"
    show_log: bool = True

    config = Config()

    haptics_player = HapticsPlayer(app_id, app_name)
    oscq = OSCQuery()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)