import open3d as o3d
import numpy as np
import json
from .helpers import alzeka2rot, rot2alzeka
class Camera():
    
    def __init__(self, iid, path=None, ext=None, is_oriented=False, hfov=None, vfov=None, img_h=None, img_w=None,
                 obj_x0=None, obj_y0=None, obj_z0=None, obj_x0_std=None, obj_y0_std=None, obj_z0_std=None, 
                 alpha=None, alpha_std=None, kappa=None, kappa_std=None, zeta = None, zeta_std=None, 
                 s0=None, img_x0=None, img_y0=None, f=None, f_std=None, 
                 gcps=None, img_gcps=None, obj_gcps=None):
        
        self.is_oriented=is_oriented
        
        self.min_dist = 100
        
        self.iid = iid
        self.path = path
        self.ext = ext
        
        self.s0 = s0
        
        self.obj_x0 = obj_x0
        self.obj_x0_std = obj_x0_std
        
        self.obj_y0 = obj_y0
        self.obj_y0_std = obj_y0_std
        
        self.obj_z0 = obj_z0
        self.obj_z0_std = obj_z0_std
                
        self.prc = [self.obj_x0, self.obj_y0, self.obj_z0]
        self.prc_std = [self.obj_x0_std, self.obj_y0_std, self.obj_z0_std]
        
        self.alpha = alpha
        self.alpha_std = alpha_std
        
        self.zeta = zeta
        self.zeta_std = zeta_std
        
        self.kappa = kappa
        self.kappa_std = kappa_std
        
        self.alzeka = [alpha, zeta, kappa]
        self.alzeka_std = [alpha_std, zeta_std, kappa_std]
        
        if None in self.alzeka:
            self.rmat = None
        else:
            self.rmat = alzeka2rot(self.alzeka)
        
        self.img_x0 = img_x0
        self.img_y0 = img_y0
        
        self.f = f
        self.f_std = f_std
        
        self.ior = [img_x0, img_y0, f]
        
        self.gcps = gcps
        self.gcp_img_coords = img_gcps
        self.gcp_obj_coords = obj_gcps
        
        self.img_w = img_w
        self.img_h = img_h
        
        self.hfov = hfov
        self.vfov = vfov
    
    def from_json(self, data):
        meta = data["meta"]
        self.s0 = meta["s0"]
        self.img_w = meta["w"]
        self.img_h = meta["h"]
        self.hfov = meta["hfov"]
        self.vfov = meta["vfov"]
        self.path = meta["path"]
        
        eor = data["eor"]
        self.obj_x0 = eor["obj_x0"]
        self.obj_x0_std = eor["obj_x0_std"]
        self.obj_y0 = eor["obj_y0"]
        self.obj_y0_std = eor["obj_y0_std"]
        self.obj_z0 = eor["obj_z0"]
        self.obj_z0_std = eor["obj_z0_std"]
        
        self.prc = [self.obj_x0, self.obj_y0, self.obj_z0]
        self.prc_std = [self.obj_x0_std, self.obj_y0_std, self.obj_z0_std]
        
        self.alpha = eor["alpha"]
        self.alpha_std = eor["alpha_std"]
        self.zeta = eor["zeta"]
        self.zeta_std = eor["zeta_std"]
        self.kappa = eor["kappa"]
        self.kappa_std = eor["kappa_std"]
        
        self.alzeka = [self.alpha, self.zeta, self.kappa]
        self.alzeka_std = [self.alpha_std, self.zeta_std, self.kappa_std]
        
        self.rmat = alzeka2rot(self.alzeka)
        
        ior = data["ior"]
        self.f = ior["f"]
        self.f_std = ior["f_std"]
        self.x0 = ior["x0"]
        self.x0_std = ior["x0_std"]
        self.y0 = ior["y0"]
        self.y0_std = ior["y0_std"]
        
        self.ior = [self.x0, self.y0, self.f]
        self.ior_Std = [self.x0_Std, self.y0_std, self.f_std]

        
        
    # def alpha2azi(self):
    #     pass
    
    def asdict(self):
        return {"obj_x0":self.obj_x0, "obj_y0":self.obj_y0, "obj_z0":self.obj_z0, 
                "obj_x0_std":self.obj_x0_std, "obj_y0_std":self.obj_y0_std, "obj_z0_std":self.obj_z0_std,
                "alpha":self.alpha, "zeta":self.zeta, "kappa":self.kappa,
                "alpha_std":self.alpha_std, "zeta_std":self.zeta_std, "kappa_std":self.kappa_std,
                "img_x0":self.img_x0, "img_y0":self.img_y0, "f":self.f, "f_std":self.f_std, "hfov":self.hfov, "vfov":self.vfov}
    
    def ray(self, img_x=None, img_y=None):
        
        if img_y > 0:
            img_y*=-1
            
        pnts_img = np.array([img_x, img_y, 0])
        pnts_img_p0 = np.subtract(pnts_img, self.ior)
        pnts_obj_dir = (np.dot(self.rmat, pnts_img_p0.T)).T
        pnts_obj_dir_norm = np.ravel(pnts_obj_dir / (np.sum(np.abs(pnts_obj_dir)**2, axis=-1)**(1./2)).reshape(-1, 1))
        
        # if min_dist is not None:
        ray_start = np.ravel(self.prc + self.min_dist * pnts_obj_dir_norm)
        return np.array([[ray_start[0], ray_start[1], ray_start[2], pnts_obj_dir_norm[0], pnts_obj_dir_norm[1], pnts_obj_dir_norm[2]]])
       