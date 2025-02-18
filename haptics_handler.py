from enum import Enum
from bhaptics.better_haptic_player import BhapticsPosition
from log import Flag

INTENSITY = 100

PARAMETER_ADDRESS = {

}

class HapticsHandler:
    def __init__(self, haptics_player, show_log=False):
        self.haptics_player = haptics_player
        self.show_log = show_log


    def vest_handler(self, _addr, *_args):
        """
        (STATIC) This works with dispatcher.

        send feedback to vest when receive contact
        :param _addr: VRC parameter address
        :param _args: VRC parameter value
        :return: NONE
        """
        num = _addr.split("_")[-1]
        idx = int("".join(num)) - 1

        if "bHapticsOSC_Vest_Back" in _addr:
            self.haptics_player.set(BhapticsPosition.VestBack, idx, _args[0])

            if self.show_log:
                print(Flag.Info.value + "Position: VestBack idx: {} Value: {}".format(idx, _args[0]))
        elif "bHapticsOSC_Vest_Front" in _addr:
            idx = (3 - idx % 4) + (idx // 4 * 4)

            self.haptics_player.set(BhapticsPosition.VestFront, idx, _args[0])

            if self.show_log:
                print(Flag.Info.value + "Position: VestFront idx: {} Value: {}".format(idx, _args[0]))

    def v1_vest_handler(self, _addr, *_args):
        """
        (STATIC)(Legacy) This works with dispatcher.

        send feedback to vest when receive contact
        :param _addr: VRC parameter address
        :param _args: VRC parameter value
        :return: NONE
        """
        num = _addr.split("_")[-1]
        idx = int("".join(num))
        intensity = INTENSITY if _args[0] else 0

        if "v1_VestBack" in _addr:
            self.haptics_player.set(BhapticsPosition.VestBack, idx, intensity)
            if self.show_log:
                print(Flag.Info.value + "Position: VestBack idx: {} Value: {}".format(idx, _args[0]))
        elif "v1_VestFront" in _addr:
            self.haptics_player.set(BhapticsPosition.VestFront, idx, intensity)
            if self.show_log:
                print(Flag.Info.value + "Position: VestFront idx: {} Value: {}".format(idx, _args[0]))

    def head_handler(self, _addr, *_args):
        """
        (STATIC) This works with dispatcher.

        send feedback to head when receive contact
        :param _addr: VRC parameter address
        :param _args: VRC parameter value
        :return: NONE
        """
        num = _addr.split("_")[-1]
        idx = int("".join(num)) - 1
        idx = 5 - idx  # reverse index

        self.haptics_player.set(BhapticsPosition.Head, idx, _args[0])

        if self.show_log:
            print(Flag.Info.value + "Position: Head idx: {} Value: {}".format(idx, _args[0]))

    def v1_head_handler(self, _addr, *_args):
        """
        (STATIC) (Legacy) This works with dispatcher.
        send feedback to head when receive contact

        :param _addr: VRC parameter address
        :param _args: VRC parameter value
        :return: NONE
        """
        num = _addr.split("_")[-1]
        idx = int("".join(num))
        intensity = INTENSITY if _args[0] else 0

        self.haptics_player.set(BhapticsPosition.Head, idx, intensity)

        if self.show_log:
            print(Flag.Info.value + "Position: Head idx: {} Value: {}".format(idx, _args[0]))

    def arm_handler(self, _addr, *_args):
        """
        (STATIC) This works with dispatcher.

        send feedback to arms when receive contact
        :param _addr: VRC parameter address
        :param _args: VRC parameter value
        :return: NONE
        """
        num = _addr.split("_")[-1]
        idx = int("".join(num)) - 1

        if "bHapticsOSC_Arm_Left" in _addr:
            self.haptics_player.set(BhapticsPosition.ForearmL, idx, _args[0])

            if self.show_log:
                print(Flag.Info.value + "Position: ForearmL idx: {} Value: {}".format(idx, _args[0]))
        elif "bHapticsOSC_Arm_Right" in _addr:
            self.haptics_player.set(BhapticsPosition.ForearmR, idx, _args[0])

            if self.show_log:
                print(Flag.Info.value + "Position: ForearmR idx: {} Value: {}".format(idx, _args[0]))

    def v1_arm_handler(self, _addr, *_args):
        """
        (STATIC) This works with dispatcher.

        send feedback to arms when receive contact
        :param _addr: VRC parameter address
        :param _args: VRC parameter value
        :return: NONE
        """
        num = _addr.split("_")[-1]
        idx = int("".join(num))
        intensity = INTENSITY if _args[0] else 0

        if "v1_ForearemL" in _addr:
            self.haptics_player.set(BhapticsPosition.ForearmL, idx, intensity)

            if self.show_log:
                print(Flag.Info.value + "Position: ForearmL: {} Value: {}".format(idx, _args[0]))
        elif "v1_ForearemR" in _addr:
            self.haptics_player.set(BhapticsPosition.ForearmR, idx, intensity)

            if self.show_log:
                print(Flag.Info.value + "Position: ForearmR: {} Value: {}".format(idx, _args[0]))

    def hand_handler(self, _addr, *_args):
        """
        (STATIC) This works with dispatcher.

        send feedback to hands when receive contact
        :param _addr: VRC parameter address
        :param _args: VRC parameter value
        :return: NONE
        """
        num = _addr.split("_")[-1]
        idx = int("".join(num)) - 1

        if "bHapticsOSC_Hand_Left" in _addr:
            self.haptics_player.set(BhapticsPosition.HandL, idx, _args[0])

            if self.show_log:
                print(Flag.Info.value + "Position: HandL idx: {} Value: {}".format(idx, _args[0]))
        elif "bHapticsOSC_Hand_Right" in _addr:
            self.haptics_player.set(BhapticsPosition.HandR, idx, _args[0])

            if self.show_log:
                print(Flag.Info.value + "Position: HandR idx: {} Value: {}".format(idx, _args[0]))

    def foot_handler(self, _addr, *_args):
        """
        (STATIC) This works with dispatcher.

        send feedback to feet when receive contact
        :param _addr: VRC parameter address
        :param _args: VRC parameter value
        :return: NONE
        """
        num = _addr.split("_")[-1]
        idx = int("".join(num)) - 1

        if "bHapticsOSC_Foot_Left" in _addr:
            self.haptics_player.set(BhapticsPosition.FootL, idx, _args[0])

            if self.show_log:
                print(Flag.Info.value + "Position: FootL idx: {} Value: {}".format(idx, _args[0]))
        elif "bHapticsOSC_Foot_Right" in _addr:
            idx = 2 - idx  # reverse index

            self.haptics_player.set(BhapticsPosition.FootR, idx, _args[0])

            if self.show_log:
                print(Flag.Info.value + "Position: HandR idx: {} Value: {}".format(idx, _args[0]))

    def glove_handler(self, _addr, *_args):
        """
        (STATIC) This works with dispatcher.

        send feedback to glove when receive contact
        :param _addr: VRC parameter address
        :param _args: VRC parameter value
        :return: NONE
        """
        num = _addr.split("_")[-1]
        idx = int("".join(num)) - 1

        if "bHapticsOSC_GloveL" in _addr:
            self.haptics_player.set(BhapticsPosition.GloveL, idx, _args[0])

            if self.show_log:
                print(Flag.Info.value + "Position: GloveR idx: {} Value: {} \033".format(idx, _args[0]))
        elif "bHapticsOSC_GloveR" in _addr:
            self.haptics_player.set(BhapticsPosition.GloveR, idx, _args[0])

            if self.show_log:
                print(Flag.Info.value + "Position: GloveR idx: {} Value: {} \033".format(idx, _args[0]))

    def avi_changed_handler(self, _addr, *_args):
        self.haptics_player.reset()

    def reset_handler(self, _addr, *_args):
        """
            (STATIC) This works with dispatcher.

            reset all position to zero
            :param _addr: VRC parameter address
            :param _args: VRC parameter value
            :return: NONE
        """

        if _args[0]:
            self.haptics_player.reset()