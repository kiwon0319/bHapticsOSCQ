from bhaptics.better_haptic_player import BhapticsPosition
from bhaptics import better_haptic_player as player

class HapticsPlayer:

    def __init__(self, _id, _name):
        player.initialize(_id, _name)
        self. positions = {key.value: list() for key in BhapticsPosition}

        for key in self.positions.keys():
            if key in ["VestBack", "VestFront"]:
                self.positions[key] = [{"index": i, "intensity": 0} for i in range(20)]
            elif key in ["Head", "ForearmL", "ForearmR", "GloveL", "GloveR"]:
                self.positions[key] = [{"index": i, "intensity": 0} for i in range(6)]
            elif key in ["HandL", "HandR", "FootL", "FootR"]:
                self.positions[key] = [{"index": i, "intensity": 0} for i in range(3)]

    def set(self, _position: BhapticsPosition, _index: int, _intensity) -> None:
        """
        Updates the intensity value of a specific actuator position in the positions attribute
        using the BhapticsPosition enumeration. The intensity value is determined by the type
        and value of the `_intensity` parameter. If `_intensity` is of int type, its value is
        directly assigned to the intensity of the specified actuator. If `_intensity` is a
        boolean, the intensity is set to 100 if `_intensity` is True, or 0 if it is False.

        :param _position: The position on the haptic device to be updated, represented as a
            BhapticsPosition enumeration.
        :param _index: The specific index of the actuator within the position to which the
            intensity should be applied.
        :param _intensity: The intensity value for the actuator, which can be either an
            integer or a boolean. An integer sets the exact intensity value, while a boolean
            determines whether the intensity should be set as fully active (100) or inactive (0).
        :return: None
        """
        if type(_intensity) is not int:
            self.positions[_position.value][_index]["intensity"] = _intensity
        if type(_intensity) is bool:
            self.positions[_position.value][_index]["intensity"] = 100 if _intensity else 0

    def reset(self):
        """
        Resets the intensity of all positions in the `positions` dictionary.

        The method iterates over all objects in the `positions` dictionary and
        sets the "intensity" value of each position to 0.

        :return: None
        """
        for obj in self.positions.values():
            for pos in obj:
                pos["intensity"] = 0

    def sumit_dot(self, _position: BhapticsPosition, _duration: int = 100):
        """
        Submit a tactile feedback dot pattern to the haptic player based on the given
        position and duration. The function utilizes the provided position object to
        identify the specific point on the device and triggers the feedback for the
        specified duration.

        :param _position: A position object that determines the location on the haptic
            device where the feedback is applied.
        :type _position: BhapticsPosition
        :param _duration: Optional duration in milliseconds for how long the feedback
            should last. Defaults to DEFAULT_DURATION.
        :type _duration: int
        :return: None
        """
        pos = _position.value
        player.submit_dot(pos, pos, self.positions[pos], _duration)