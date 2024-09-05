# from ._panzoom import PanZoomController
from pygfx import Controller
from typing import Tuple
import numpy as np

class ImageController(Controller):
       
    _default_controls = {
        "wheel": ("position", "push", -0.001),
        "alt+wheel": ("opacity", "push", -0.01),
    }
    
    def set_image(self, image, pnts_dir, prc, distance=1000):
        self.image = image
        self.distance = 1000
        self.pnts_dir = pnts_dir
        self.prc = prc
        
    def position(self, delta: Tuple, rect: Tuple, *, animate=False):
        if animate:
            pass
        else:
            self._update_position(delta)
            return self._update_cameras()

    def _update_position(self, delta):
        upd_dist = self.distance+delta*1000
        if upd_dist < 10:
            upd_dist = 10
            
        upd_pnts = self.prc + upd_dist*self.pnts_dir
        self.image.geometry.positions.data[:, :] = upd_pnts
        self.image.geometry.positions.update_range(0, 4)

        self.distance = upd_dist
    
    def opacity(self, delta: Tuple, rect: Tuple, *, animate=False):
        if animate:
            pass
        else:
            self._update_opacity(delta)
            return self._update_cameras()
    
    def _update_opacity(self, delta):
        print("ARGHH", delta)
        