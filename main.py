import os
import re
import asyncio
import json
import errno
import socket
import time
import psutil
import requests

from enum import Enum
from bhaptics import better_haptic_player as player
from bhaptics.better_haptic_player import BhapticsPosition, connected_positions
from pythonosc import udp_client, osc_server, dispatcher
from tinyoscquery.query import OSCQueryBrowser, OSCQueryClient
from tinyoscquery.queryservice import OSCQueryService, OSCAccess

class Flag(Enum):
    Info = "\033[34m[INFO]\033[0m "
    Debug = "\033[32m[Debug]\033[0m "
    Warn = "\033[33m[Warning]\033[0m "


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
            print("VRC isn't running waiting...")
            while(not OSCQuery.__check_process_is_running()):
                time.sleep(1)

        # find free udp port and set osc_port
        self.__get_free_udp_port()
        # find free tcp port and set http_port
        self.__get_free_tcp_port()

        self.oscQueryService = OSCQueryService("OSC Parameter Increaser", self.http_port, self.osc_port)
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

            print(Flag.Info.value + "getting UDP port has been completed")

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

        while True:
            response = requests.get(f"http://127.0.0.1:{self.vrchat_client_port}/avatar/change")

            if response.status_code == 200:
                json_data = response.json()
                return json_data['VALUE'][0]

            time.sleep(1)

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
    CONFIG_VERSION = 1

    def __init__(self):
        # <NETWORK>
        self.ip_addr: str = "127.0.0.1"
        self.bHaptics_port: int = 5005
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
                self.bHaptics_port = raw["NETWORK"]["bHaptics_port"]

                return 0
        except IOError as e:
            return e.errno
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
            "bHaptics_port": self.bHaptics_port,
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

        for (path, dir, files) in os.walk(oscpath):
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

        return vlaue information: (id, name, parameters)
        :return: (Tuple) avatar config variables
        """
        result = (self.avatar_id, self.avatar_name, self.avatar_prmt)
        return result


class Receiver:
    @staticmethod
    def vest_handler(_addr, *_args):
        """
        (STATIC) This works with dispatcher.

        send feedback to vest when receive contact
        :param _addr: VRC parameter address
        :param _args: VRC parameter value
        :return: NONE
        """

        if "bHapticsOSC_Vest_Back"in _addr:
            num = re.findall(r'\d', _addr)
            idx = int("".join(num)) - 1

            if _args[0]:
                bHaptics_back[idx] = {"index": idx, "intensity": 100}
            else:
                bHaptics_back[idx] = {"index": idx, "intensity": 0}
            print(Flag.Info.value + "Position: VestBack idx: {} Value: {} \033".format(idx, _args[0]))
        elif "bHapticsOSC_Vest_Front" in _addr:
            num = re.findall(r'\d', _addr)
            idx = int("".join(num)) - 1
            idx = (3 - idx % 4) + (idx // 4 * 4)

            if _args[0]:
                bHaptics_front[idx] = {"index": idx, "intensity": 100}
            else:
                bHaptics_front[idx] = {"index": idx, "intensity": 0}
            print(Flag.Info.value + "Position: VestFront idx: {} Value: {} \033".format(idx, _args[0]))

    @staticmethod
    def head_handler(_addr, *_args):
        """
            (STATIC) This works with dispatcher.

            send feedback to head when receive contact
            :param _addr: VRC parameter address
            :param _args: VRC parameter value
            :return: NONE
        """
        num = re.findall(r'\d', _addr)
        idx = int("".join(num)) - 1
        idx = 5 - idx   # reverse index

        if _args[0]:
            bHaptics_head[idx] = {"index": idx, "intensity": 100}
        else:
            bHaptics_head[idx] = {"index": idx, "intensity": 0}
        print(Flag.Info.value + "Position: Head idx: {} Value: {} \033".format(idx, _args[0]))

    @staticmethod
    def arm_handler(_addr, *_args):
        """
            (STATIC) This works with dispatcher.

            send feedback to arms when receive contact
            :param _addr: VRC parameter address
            :param _args: VRC parameter value
            :return: NONE
        """
        num = re.findall(r'\d', _addr)
        idx = int("".join(num)) - 1

        if "bHapticsOSC_Arm_Left" in _addr:
            if _args[0]:
                bHaptics_foreArm_L[idx] = {"index": idx, "intensity": 100}
            else:
                bHaptics_foreArm_L[idx] = {"index": idx, "intensity": 0}
            print(Flag.Info.value + "Position: ForearmL idx: {} Value: {} \033".format(idx, _args[0]))
        elif "bHapticsOSC_Arm_Right" in _addr:
            if _args[0]:
                bHaptics_foreArm_R[idx] = {"index": idx, "intensity": 100}
            else:
                bHaptics_foreArm_R[idx] = {"index": idx, "intensity": 0}
            print(Flag.Info.value + "Position: ForearmR idx: {} Value: {} \033".format(idx, _args[0]))

    @staticmethod
    def hand_handler(_addr, *_args):
        """
            (STATIC) This works with dispatcher.

            send feedback to hands when receive contact
            :param _addr: VRC parameter address
            :param _args: VRC parameter value
            :return: NONE
        """
        num = re.findall(r'\d', _addr)
        idx = int("".join(num)) - 1

        if "bHapticsOSC_Hand_Left" in _addr:
            if _args[0]:
                bHaptics_hand_L[idx] = {"index": idx, "intensity": 100}
            else:
                bHaptics_hand_L[idx] = {"index": idx, "intensity": 0}
            print(Flag.Info.value + "Position: HandL idx: {} Value: {} \033".format(idx, _args[0]))
        elif "bHapticsOSC_Hand_Right" in _addr:
            if _args[0]:
                bHaptics_hand_R[idx] = {"index": idx, "intensity": 100}
            else:
                bHaptics_hand_R[idx] = {"index": idx, "intensity": 0}
            print(Flag.Info.value + "Position: HandR idx: {} Value: {} \033".format(idx, _args[0]))

    @staticmethod
    def foot_handler(_addr, *_args):
        """
            (STATIC) This works with dispatcher.

            send feedback to feet when receive contact
            :param _addr: VRC parameter address
            :param _args: VRC parameter value
            :return: NONE
        """
        num = re.findall(r'\d', _addr)
        idx = int("".join(num)) - 1

        if "bHapticsOSC_Foot_Left" in _addr:
            if _args[0]:
                bHaptics_foot_L[idx] = {"index": idx, "intensity": 100}
            else:
                bHaptics_foot_L[idx] = {"index": idx, "intensity": 0}
            print(Flag.Info.value + "Position: FootL idx: {} Value: {} \033".format(idx, _args[0]))
        elif "bHapticsOSC_Foot_Right" in _addr:
            idx = 2 - idx   # reverse index

            if _args[0]:
                bHaptics_foot_R[idx] = {"index": idx, "intensity": 100}
            else:
                bHaptics_foot_R[idx] = {"index": idx, "intensity": 0}
            print(Flag.Info.value + "Position: HandR idx: {} Value: {} \033".format(idx, _args[0]))

    @staticmethod
    def glove_handler(_addr, *_args):
        """
            (STATIC) This works with dispatcher.

            send feedback to glove when receive contact
            :param _addr: VRC parameter address
            :param _args: VRC parameter value
            :return: NONE
        """
        num = re.findall(r'\d', _addr)
        idx = int("".join(num)) - 1

        if "bHapticsOSC_GloveL" in _addr:
            if _args[0]:
                bHaptics_glove_L[idx] = {"index": idx, "intensity": 100}
            else:
                bHaptics_glove_L[idx] = {"index": idx, "intensity": 0}
            print(Flag.Info.value + "Position: GloveR idx: {} Value: {} \033".format(idx, _args[0]))
        elif "bHapticsOSC_GloveR" in _addr:
            if _args[0]:
                bHaptics_glove_R[idx] = {"index": idx, "intensity": 100}
            else:
                bHaptics_glove_R[idx] = {"index": idx, "intensity": 0}
            print(Flag.Info.value + "Position: GloveR idx: {} Value: {} \033".format(idx, _args[0]))

    @staticmethod
    def reset_handler(_addr, *_args):
        if _args[0]:
            for obj in bHaptics_front:
                obj["intensity"] = 0
            for obj in bHaptics_back:
                obj["intensity"] = 0
            for obj in bHaptics_head:
                obj["intensity"] = 0
            for obj in bHaptics_foreArm_L:
                obj["intensity"] = 0
            for obj in bHaptics_foreArm_R:
                obj["intensity"] = 0
            for obj in bHaptics_hand_L:
                obj["intensity"] = 0
            for obj in bHaptics_hand_R:
                obj["intensity"] = 0
            for obj in bHaptics_foot_L:
                obj["intensity"] = 0
            for obj in bHaptics_foot_R:
                obj["intensity"] = 0
            for obj in bHaptics_glove_L:
                obj["intensity"] = 0
            for obj in bHaptics_glove_R:
                obj["intensity"] = 0

    @staticmethod
    def build_dispatcher():
        """
        (STATIC) build dispatcher for receiver
        """
        d = dispatcher.Dispatcher()

        d.map("/avatar/parameters/bHapticsOSC_reset", Receiver.reset_handler)
        d.map("/avatar/parameters/bHapticsOSC_Head*", Receiver.head_handler)
        d.map("/avatar/parameters/bHapticsOSC_Arm*", Receiver.arm_handler)
        d.map("/avatar/parameters/bHapticsOSC_Hand*", Receiver.arm_handler)
        d.map("/avatar/parameters/bHapticsOSC_Hand*", Receiver.hand_handler)
        d.map("/avatar/parameters/bHapticsOSC_Foot*", Receiver.foot_handler)
        d.map("/avatar/parameters/bHapticsOSC_Glove*",Receiver.glove_handler)
        d.map("/avatar/parameters/bHapticsOSC_Vest*", Receiver.vest_handler)

        return d

    def __init__(self, _dispatcher: dispatcher.Dispatcher, _ip: str = "127.0.0.1", _port: int = 9001):
        self.ip = _ip
        self.port = _port
        self.dispatcher = _dispatcher

        self.server = osc_server.AsyncIOOSCUDPServer(
            (self.ip, self.port),
            self.dispatcher,
            asyncio.get_event_loop()
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

    async def send(self, ctx, prmt: str, path: str = "/avatar/parameters/", PRINT_INFO: bool = True):
        """
        send osc packet
        :param ctx: context to send
        :param prmt: VRC parameter name
        :param path: (Optional) parameter path
        """
        full_path = path + prmt
        self.client.send_message(full_path, ctx)

        if PRINT_INFO:
            print(Flag.Info.value + f"SEND COMPLETE prm: {prmt} - ctx: ({type(ctx)}) {ctx}")


async def loop():
    print(Flag.Info.value + "START SENDING")

    while(True):
        player.submit_dot("backFrame",BhapticsPosition.VestBack.value,bHaptics_back,100)
        player.submit_dot("frontFrame", BhapticsPosition.VestFront.value,bHaptics_front, 100)
        player.submit_dot("headFrame", BhapticsPosition.Head.value,bHaptics_head, 100)
        player.submit_dot("forearmLFrame", BhapticsPosition.ForearmL.value, bHaptics_foreArm_L, 100)
        player.submit_dot("forearmRFrame", BhapticsPosition.ForearmR.value, bHaptics_foreArm_R, 100)
        player.submit_dot("handLFrame", BhapticsPosition.HandL.value, bHaptics_hand_L, 100)
        player.submit_dot("handRFrame", BhapticsPosition.HandR.value, bHaptics_hand_R, 100)
        player.submit_dot("footLFrame", BhapticsPosition.FootL.value, bHaptics_foot_L, 100)
        player.submit_dot("footRFrame", BhapticsPosition.FootR.value, bHaptics_foot_R, 100)
        player.submit_dot("gloveLFrame", BhapticsPosition.GloveL.value, bHaptics_glove_L, 100)
        player.submit_dot("gloveRFrame", BhapticsPosition.GloveR.value, bHaptics_glove_R, 100)
        await asyncio.sleep(0.1)

async def main():
    d = Receiver.build_dispatcher()
    receiver = Receiver(d, config.ip_addr, oscq.get_osc_port())
    transport = await receiver.start()

    await asyncio.gather(loop())

    transport.close()


# Press the green button in the gutter to run the script.

if __name__ == '__main__':
    app_id = "per.Guideung.bHapticsOSCQ"
    app_name = "bHapticsOSCQ"
    oscq = OSCQuery()
    config = Config()

    player.initialize(app_id,app_name)

    bHaptics_front = [{"index": i, "intensity": 0} for i in range(20)]
    bHaptics_back = [{"index": i, "intensity": 0} for i in range(20)]
    bHaptics_head = [{"index": i, "intensity": 0} for i in range(6)]
    bHaptics_foreArm_L = [{"index": i, "intensity": 0} for i in range(6)]
    bHaptics_foreArm_R = [{"index": i, "intensity": 0} for i in range(6)]
    bHaptics_hand_L = [{"index": i, "intensity": 0} for i in range(3)]
    bHaptics_hand_R = [{"index": i, "intensity": 0} for i in range(3)]
    bHaptics_foot_L = [{"index": i, "intensity": 0} for i in range(3)]
    bHaptics_foot_R = [{"index": i, "intensity": 0} for i in range(3)]
    bHaptics_glove_L=[{"index": i, "intensity": 0} for i in range(6)]
    bHaptics_glove_R=[{"index": i, "intensity": 0} for i in range(6)]

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass