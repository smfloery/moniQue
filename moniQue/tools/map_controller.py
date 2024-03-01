from typing import Tuple

import pylinalg as la

from pygfx import TrackballController
import numpy as np

class MapController(TrackballController):
    _default_controls = {
       "mouse1": ("rotate", "drag", (0.005, 0.005)),
        "mouse2": ("move", "drag", (1, 1)),
        # "mouse4": ("quickzoom", "peek", 2),
        # "wheel": ("pan", "drag", (1, 1)),
        "alt+mouse1": ("pan", "drag", (1, 1)),
    }
    
    # def rotate(self, delta: Tuple, rect: Tuple, *, animate=False):
    #     self._update_rotate(delta)
    #     return self._update_cameras()

    # def _update_rotate(self, delta):
    #     assert isinstance(delta, tuple) and len(delta) == 2

    #     delta_azimuth, delta_elevation = delta
    #     camera_state = self._get_camera_state()

    #     # Note: this code does not use la.vec_euclidean_to_spherical and
    #     # la.vec_spherical_to_euclidean, because those functions currently
    #     # have no way to specify a different up vector.

    #     position = camera_state["position"]
    #     rotation = camera_state["rotation"]
    #     up = camera_state["reference_up"]

    #     # Where is the camera looking at right now
    #     forward = la.vec_normalize(la.vec_transform_quat((0, 0, -1), rotation))
    #     right = np.cross(forward, up)
     
    #     # Get current elevation, so we can clip it.
    #     # We don't need the azimuth. When we do, it'd need more care to get a proper 0..2pi range
    #     elevation = la.vec_angle(forward, up) - 0.5 * np.pi

    #     # Apply boundaries to the elevation
    #     new_elevation = elevation + delta_elevation
    #     # bounds = -89 * np.pi / 180, 89 * np.pi / 180
    #     # if new_elevation < bounds[0]:
    #     #     delta_elevation = bounds[0] - elevation
    #     # elif new_elevation > bounds[1]:
    #     #     delta_elevation = bounds[1] - elevation

    #     r_azimuth = la.quat_from_axis_angle(up, -delta_azimuth*0.005)
    #     r_elevation = la.quat_from_axis_angle(right, -delta_elevation*0.005)

    #     # Get rotations
    #     rot1 = rotation
    #     # rot2 = la.quat_mul(forward, la.quat_mul(r_azimuth, r_elevation))

    #     forward_new = la.vec_transform_quat(forward, la.quat_mul(r_azimuth, r_elevation))
    #     rot2 = la.quat_mul(rot1, la.quat_from_vecs(forward, forward_new))
        
    #     # Calculate new position
    #     pos1 = position
    #     pos2target1 = self._get_target_vec(camera_state, rotation=rot1)
    #     pos2target2 = self._get_target_vec(camera_state, rotation=rot2)
    #     pos2 = pos1 + pos2target1 - pos2target2
        
    #     # Apply new state
    #     new_camera_state = {"position": pos2, "rotation": rot2}
    #     self._set_camera_state(new_camera_state)

    #     # Note that for ortho cameras, we also orbit around the scene,
    #     # even though it could be positioned at the center (i.e.
    #     # target). Doing it this way makes the code in the controllers
    #     # easier. The only downside I can think of is that the far plane
    #     # is now less far away but this effect is only 0.2%, since the
    #     # far plane is 500 * dist.
    
    def move(self, delta):
        self._update_move(delta)
        return self._update_cameras()
        
    def _update_move(self, delta):
        
        camera_state = self._get_camera_state()
        
        position = camera_state["position"]
        rotation = camera_state["rotation"]
        up = camera_state["reference_up"]

        # Where is the camera looking at right now
        forward = la.vec_transform_quat((0, 0, -1), rotation)
        
        upd_position = position + 10*delta[1]*forward
        
        new_camera_state = {"position": upd_position}
        self._set_camera_state(new_camera_state)