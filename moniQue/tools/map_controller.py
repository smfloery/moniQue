from typing import Tuple

import numpy as np
import pylinalg as la

# from ._panzoom import PanZoomController
from pygfx import PanZoomController


def _get_axis_aligned_up_vector(up):
    # Not actually used, but I have a feeling we might need it at some point :)
    ref_up, largest_dot = None, 0
    for up_vec in [(1, 0, 0), (0, 1, 0), (0, 0, 1), (-1, 0, 0), (0, -1, 0), (0, 0, -1)]:
        up_vec = np.array(up_vec)
        v = np.dot(up_vec, up)
        if v > largest_dot:
            ref_up, largest_dot = up_vec, v
    return ref_up


class OrbitFlightController(PanZoomController):
    """A controller to move a camera in an orbit around a center position.

    Supports panning parallel to the screen, zooming, orbiting.

    The direction of rotation is defined such that it feels like you're
    grabbing onto something in the foreground; if you move the mouse
    to the right, the objects in the foreground move to the right, and
    those in the background (on the opposite side of the center of rotation)
    move to the left.

    Default controls:

    * Left mouse button: orbit / rotate.
    * Right mouse button: pan.
    * Fourth mouse button: quickzoom
    * wheel: zoom to point.
    * alt+wheel: adjust fov.

    """

    _default_controls = {
        "mouse1": ("rotate", "drag", (0.005, 0.005)),
        "mouse2": ("pan", "drag", (1, 1)),
        "mouse4": ("quickzoom", "peek", 2),
        "wheel": ("zoom", "push", -0.001),
        "alt+wheel": ("fov", "push", -0.01),
        "control+wheel": ("speed", "push", -0.001),
        "control+mouse1": ("rotate", "drag", (0.005, 0)),
        "alt+mouse1": ("rotate", "drag", (0, 0.005)),
        "q": ("roll", "repeat", -2),
        "e": ("roll", "repeat", +2),
        "w": ("move", "repeat", (0, 0, -1)),
        "s": ("move", "repeat", (0, 0, +1)),
        "a": ("move", "repeat", (-1, 0, 0)),
        "d": ("move", "repeat", (+1, 0, 0)),
        "arrowup": ("pitch", "repeat", -2),
        "arrowdown": ("pitch", "repeat", +2),
        "arrowleft": ("yaw", "repeat", -2),
        "arrowright": ("yaw", "repeat", +2),
        " ": ("move", "repeat", (0, +1, 0)),
        "shift": ("move", "repeat", (0, -1, 0)),
    }

    def __init__(self, camera, *, speed=None, **kwargs):
        super().__init__(camera, **kwargs)

        if speed is None:
            cam_state = camera.get_state()
            approx_scene_size = 0.5 * (cam_state["width"] + cam_state["height"])
            scene_fly_thru_time = 5  # seconds
            speed = approx_scene_size / scene_fly_thru_time
        self.speed = speed

    @property
    def speed(self):
        """The (maximum) speed that the camera will move, in units per second.
        By default it's based off the width and height of the camera.
        """
        return self._speed

    @speed.setter
    def speed(self, value):
        self._speed = float(value)


    def rotate(self, delta: Tuple, rect: Tuple, *, animate=False):
        """Rotate in an orbit around the target, using two angles (azimuth and elevation, in radians).

        If animate is True, the motion is damped. This requires the
        controller to receive events from the renderer/viewport.
        """

        if animate:
            action_tuple = ("rotate", "push", (1.0, 1.0))
            action = self._create_action(None, action_tuple, (0.0, 0.0), None, rect)
            action.set_target(delta)
            action.snap_distance = 0.01
            action.done = True
        elif self._cameras:
            self._update_rotate(delta)
            return self._update_cameras()

    def _update_rotate(self, delta):
        assert isinstance(delta, tuple) and len(delta) == 2

        delta_azimuth, delta_elevation = delta
        
        print(delta_azimuth, delta_elevation)
        
        camera_state = self._get_camera_state()
        print(camera_state)
        
        # Note: this code does not use la.vec_euclidean_to_spherical and
        # la.vec_spherical_to_euclidean, because those functions currently
        # have no way to specify a different up vector.

        position = camera_state["position"]
        rotation = camera_state["rotation"]
        
        # up = camera_state["reference_up"]
        up = la.vec_transform_quat((0, 1, 0), rotation)
        forward = la.vec_transform_quat((0, 0, -1), rotation)
        right = la.vec_normalize(np.cross(forward, up))
        
        # # Get current elevation, so we can clip it.
        # # We don't need the azimuth. When we do, it'd need more care to get a proper 0..2pi range
        elevation = la.vec_angle(forward, up) - 0.5 * np.pi
        
        # Apply boundaries to the elevation
        new_elevation = elevation + delta_elevation
        bounds = -89 * np.pi / 180, 89 * np.pi / 180
        if new_elevation < bounds[0]:
            delta_elevation = bounds[0] - elevation
        elif new_elevation > bounds[1]:
            delta_elevation = bounds[1] - elevation

        r_azimuth = la.quat_from_axis_angle(up, -delta_azimuth)
        r_elevation = la.quat_from_axis_angle((1, 0, 0), -delta_elevation)

        # # # Get rotations
        rot1 = rotation
        rot2 = la.quat_mul(r_azimuth, la.quat_mul(rot1, r_elevation))
        
        # # # Calculate new position
        pos1 = position
        pos2target1 = self._get_target_vec(camera_state, rotation=rot1)
        pos2target2 = self._get_target_vec(camera_state, rotation=rot2)
        pos2 = pos1 + pos2target1 - pos2target2

        # # Apply new state
        new_camera_state = {"position": pos2, "rotation": rot2}
        self._set_camera_state(new_camera_state)


    def roll(self, delta: float, rect: Tuple, *, animate=False):
        """Rotate the camera over the z-axis (roll, in radians).

        If animate is True, the motion is damped. This requires the
        controller to receive events from the renderer/viewport.
        """
        if animate:
            action_tuple = ("roll", "push", 1.0)
            action = self._create_action(None, action_tuple, 0.0, None, rect)
            action.set_target(delta)
            action.snap_distance = 0.01
            action.done = True
        elif self._cameras:
            self._update_rotate(delta)
            return self._update_cameras()

    def _update_roll(self, delta):
        assert isinstance(delta, float)

        camera_state = self._get_camera_state()
        rotation = camera_state["rotation"]

        qz = la.quat_from_axis_angle((0, 0, 1), -delta)
        new_rotation = la.quat_mul(rotation, qz)

        new_camera_state = {"rotation": new_rotation}
        self._set_camera_state(new_camera_state)


    def pitch(self, delta: float, rect: Tuple, *, animate=False):
        if animate:
            action_tuple = ("pitch", "push", 1.0)
            action = self._create_action(None, action_tuple, 0.0, None, rect)
            action.set_target(delta)
            action.snap_distance = 0.01
            action.done = True
        elif self._cameras:
            self._update_rotate(delta)
            return self._update_cameras()

    def _update_pitch(self, delta):
        assert isinstance(delta, float)

        camera_state = self._get_camera_state()
        rotation = camera_state["rotation"]

        qz = la.quat_from_axis_angle((1, 0, 0), -delta)
        new_rotation = la.quat_mul(rotation, qz)

        new_camera_state = {"rotation": new_rotation}
        self._set_camera_state(new_camera_state)


    def yaw(self, delta: float, rect: Tuple, *, animate=False):
        if animate:
            action_tuple = ("yaw", "push", 1.0)
            action = self._create_action(None, action_tuple, 0.0, None, rect)
            action.set_target(delta)
            action.snap_distance = 0.01
            action.done = True
        elif self._cameras:
            self._update_rotate(delta)
            return self._update_cameras()

    def _update_yaw(self, delta):
        assert isinstance(delta, float)

        camera_state = self._get_camera_state()
        rotation = camera_state["rotation"]

        qz = la.quat_from_axis_angle((0, 1, 0), -delta)
        new_rotation = la.quat_mul(rotation, qz)

        new_camera_state = {"rotation": new_rotation}
        self._set_camera_state(new_camera_state)


    def move(self, delta: Tuple, rect: Tuple, *, animate=False):
        """Move the camera in the given (x, y, z) direction.

        The delta is expressed in the camera's local coordinate frame.
        Forward is in -z direction, because as (per the gltf spec) a
        camera looks down it's negative Z-axis.

        If animate is True, the motion is damped. This requires the
        controller to receive events from the renderer/viewport.
        """

        if animate:
            action_tuple = ("move", "push", (1.0, 1.0, 1.0))
            action = self._create_action(
                None, action_tuple, (0.0, 0.0, 0.0), None, rect
            )
            action.set_target(delta)
            action.done = True
        elif self._cameras:
            self._update_move(delta)
            return self._update_cameras()

    def _update_move(self, delta):
        assert isinstance(delta, tuple) and len(delta) == 3

        cam_state = self._get_camera_state()
        position = cam_state["position"]
        rotation = cam_state["rotation"]
        delta_world = la.vec_transform_quat(delta, rotation)

        new_position = position + delta_world * self.speed
        self._set_camera_state({"position": new_position})


    def _update_speed(self, delta):
        assert isinstance(delta, float)
        speed = self.speed * 2**delta
        self.speed = max(0.001, speed)

    def get_speed(self):
        return self.speed