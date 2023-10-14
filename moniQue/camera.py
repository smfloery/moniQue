import open3d as o3d
import numpy as np
import urllib.request
import json
import ssl

context = ssl._create_unverified_context()
            
class Camera():
    
    def __init__(self, name, path, ext, is_oriented=False):
        
        self.is_oriented=is_oriented
        
        self.iid = name
        self.path = path
        self.ext = ext
        
        self.s0 = None
        
        self.prc = None
        self.prc_std = None
        self.rmat = None
        
        self.ior = None
        self.ior_std = None
        
        self.gcps = None
        self.gcp_img_coords = None
        self.gcp_obj_coords = None
        
        self.alpha = None
        self.zeta = None
        self.kappa = None
        
        self.alzeka = None
        self.alzeka_std = None
        
        self.meta = None
        
        self.w = None
        self.h = None
        
        self.hfov = None
        self.vfov = None
        
    def set_img_dim(self, h, w):
        self.h = h
        self.w = w
          
    #     if not token:
    #         token = "40622e289e7005b3007a499eac4ecb3a"
        
    #     if img_id:
            
    #         cam_api_url = "https://sehag.geo.tuwien.ac.at/export/camera/?token=%s&img_id=%s" % (token, img_id)
                
    #         try:
    #             api_resp = urllib.request.urlopen(cam_api_url, context=context)
            
    #         except urllib.error.HTTPError as e:            
    #             api_resp = json.loads(e.read().decode("utf-8"))
    #             # print(api_resp)
    #             self.status = "error"
    #             self.status_msg = api_resp["message"]
    #             api_resp = None
    #             # raise ValueError(api_resp["message"])
            
    #         if api_resp:
                
    #             cam_data = json.loads(api_resp.read().decode("utf-8"))["camera"]
                
    #             self.name = str(cam_data["name"])
    #             self.id = str(cam_data["img_id"])
    #             self.s0 = float(cam_data["sigma_0"])
                
    #             cam_eor = cam_data["eor"]
    #             self.prc = np.array([cam_eor["prj_ctr"]["E"], cam_eor["prj_ctr"]["N"], cam_eor["prj_ctr"]["H"]])
    #             self.prc_std = np.array([cam_eor["prj_ctr"]["std_E"], cam_eor["prj_ctr"]["std_N"], cam_eor["prj_ctr"]["std_H"]])
    #             self.R = np.array(cam_eor["rot"]["rot_mat_utm"]).reshape(3, 3)
                
    #             cam_ior = cam_data["ior"]
    #             self.ior = np.array([cam_data["ior"]["x0"], cam_data["ior"]["y0"], cam_data["ior"]["f0"]])
    #             self.ior_std = np.array([cam_data["ior"]["std_x0"], cam_data["ior"]["std_y0"], cam_data["ior"]["std_f0"]])
                
    #             self.gcps = cam_data["gcps"]   
                
    #             gcp_obj_coords = []
    #             gcp_img_coords = []
                
                
    #             for gcp_id in self.gcps.keys():
    #                 gcp = self.gcps[gcp_id]
    #                 gcp_obj_coords.append([gcp["E"], gcp["N"], gcp["H"]])
    #                 gcp_img_coords.append([gcp["x"], gcp["y"]])
                
    #             self.gcp_obj_coords = np.array(gcp_obj_coords)
    #             self.gcp_img_coords = np.array(gcp_img_coords)
    #             self.gcp_ids = list(self.gcps.keys())
                
    #             #extract both possible sets of rotation angles alpha, zeta and kappa
    #             ze_1_rad = np.arccos(self.R[2,2])
    #             ze_2_rad = 2*np.pi - ze_1_rad
    #             if ze_2_rad < 0:
    #                 ze_2_rad += 2*np.pi

    #             ka_1_rad = np.arctan2(self.R[2, 1], self.R[2, 0]*(-1))
    #             if ka_1_rad < 0:
    #                 ka_2_rad = ka_1_rad + np.pi
    #             else:
    #                 ka_2_rad = ka_1_rad - np.pi

    #             al_1_rad = np.arctan2(self.R[1, 2], self.R[0, 2])
    #             if al_1_rad < 0:
    #                 al_2_rad = al_1_rad + np.pi
    #             else:
    #                 al_2_rad = al_1_rad - np.pi

    #             alzekas = np.array([[al_1_rad, ze_1_rad, ka_1_rad], [al_2_rad, ze_2_rad, ka_2_rad]])
                
    #             diff_e = self.gcp_obj_coords[:, 0] - self.prc[0]
    #             diff_n = self.gcp_obj_coords[:, 1] - self.prc[1]
    #             dir_2_gcp = np.arctan2(diff_e, diff_n)
    #             dir_2_gcp[dir_2_gcp < 0] = dir_2_gcp[dir_2_gcp < 0] + 2*np.pi #make sure directions are between 0 and 360 degrees
                
    #             al_1_rad_n = self.alpha_from_north(al_1_rad)
    #             al_2_rad_n = self.alpha_from_north(al_2_rad)
                
    #             diff_gcp_2_alzeka_a = np.mean(np.abs(al_1_rad_n - dir_2_gcp))
    #             diff_gcp_2_alzeka_b = np.mean(np.abs(al_2_rad_n - dir_2_gcp))
                
    #             if diff_gcp_2_alzeka_a < diff_gcp_2_alzeka_b:
    #                 self.alpha = alzekas[0, 0]
    #                 self.zeta = alzekas[0, 1]
    #                 self.kappa = alzekas[0, 2]
    #             else:
    #                 self.alpha = alzekas[1, 0]
    #                 self.zeta = alzekas[1, 1]
    #                 self.kappa = alzekas[1, 2]
                
    #             self.euler = np.array([self.alpha, self.zeta, self.kappa])
    #             self.euler_std = np.array([cam_data["eor"]["rot"]["std_rot_a"], cam_data["eor"]["rot"]["std_rot_z"], cam_data["eor"]["rot"]["std_rot_k"]])
                
    #             self.qvv = cam_data["qvv"]
    #             self.cxx = cam_data["cxx"]
    #             self.meta = cam_data["meta"]
                
    #             self.img_w = int(self.meta["width"])
    #             self.img_h = int(self.meta["height"])
                
    #             self.hfov = np.arctan(self.img_w/(self.ior[2]*2))*2
    #             self.vfov = np.arctan(self.img_h/(self.ior[2]*2))*2

    #             self.status = "ok"
    
    # def __str__(self):
    #     return "%s | (E=%.3f[m], N=%.3f[m], H=%.3f[m], A=%.6f[rad], Z=%.6f[rad], K=%.6f[rad])" % (self.name, self.prc[0], self.prc[1], self.prc[2], self.alpha, self.zeta, self.kappa)
    
    # def R_ori2cv(self):
    #     rx_200 = np.diag((1, -1, -1))
    #     return rx_200 @ np.transpose(self.R)
          
    # def to_open3d(self, img_w=None, img_h=None):
    #     if img_w is None:
    #         img_w = self.img_w
    #         img_h = self.img_h
    #         f_ratio = 1
    #     else:
    #         f_ratio = img_w/float(self.img_w)
            
    #     cam_rot_cv = self.R_ori2cv()
    #     cam_tvec = np.matmul(cam_rot_cv*(-1), self.prc.reshape(3, 1))
    #     cam_Rt = np.vstack((np.concatenate([cam_rot_cv, cam_tvec], axis=-1), np.array([0, 0, 0, 1])))

    #     o3d_cam_intrinsic = o3d.camera.PinholeCameraIntrinsic(img_w, img_h, self.ior[2]*(f_ratio), self.ior[2]*(f_ratio), img_w/2.-0.5, img_h/2.-0.5)

    #     o3d_cam = o3d.camera.PinholeCameraParameters()
    #     o3d_cam.intrinsic = o3d_cam_intrinsic
    #     o3d_cam.extrinsic = cam_Rt

    #     return o3d_cam
    
    # def alpha_from_north(self, alpha):
    #     if alpha <= 0:
    #         return alpha * (-1) + np.pi/2.
    #     else:
    #         alpha_north = 2*np.pi - (alpha + 3*np.pi/2.)
    #         if alpha_north < 0:
    #             return alpha_north + 2*np.pi
    #         else:
    #             return alpha_north
    
    # def ray(self, img_x=None, img_y=None, min_dist=None):
        
    #     if img_y > 0:
    #         img_y*=-1
            
    #     pnts_img = np.array([img_x, img_y, 0])
    #     pnts_img_p0 = np.subtract(pnts_img, self.ior)
    #     pnts_obj_dir = (np.dot(self.R, pnts_img_p0.T)).T
    #     pnts_obj_dir_norm = pnts_obj_dir / (np.sum(np.abs(pnts_obj_dir)**2, axis=-1)**(1./2)).reshape(-1, 1)
        
    #     if min_dist is not None:
    #         ray_start = self.prc + min_dist * pnts_obj_dir_norm
    #         return [ray_start[0], ray_start[1], ray_start[2], pnts_obj_dir_norm[0, 0], pnts_obj_dir_norm[0, 1], pnts_obj_dir_norm[0, 2]]
    #     else: 
    #         return [self.prc[0], self.prc[1], self.prc[2], pnts_obj_dir_norm[0, 0], pnts_obj_dir_norm[0, 1], pnts_obj_dir_norm[0, 2]]
       
    # # def rays(self, mode=None, step_x=None, step_y=None, wdeg=None, hdeg=None, min_dist=None):
                
    # #     if wdeg and hdeg:
    # #         pix_per_deg_h = int(self.img_w / (self.hfov*180/np.pi))
    # #         pix_per_deg_v = int(self.img_h / (self.vfov*180/np.pi))
            
    # #         img_x = np.arange(0, self.img_w, step=pix_per_deg_h*wdeg)
    # #         img_x = np.append(img_x, self.img_w)
    # #         img_y = np.arange(0, -self.img_h, step=-pix_per_deg_v*hdeg)
    # #         img_y = np.append(img_y, self.img_h*(-1))
        
    # #     elif step_x and step_y:
    # #         img_x = np.arange(0, self.img_w, step=step_x)
    # #         img_x = np.append(img_x, self.img_w)
    # #         img_y = np.arange(0, -self.img_h, step=step_y*(-1))
    # #         img_y = np.append(img_y, self.img_h*(-1))
                
    # #     img_xx, img_yy = np.meshgrid(img_x, img_y)
    # #     img_xx = img_xx.reshape(-1, 1)
    # #     img_yy = img_yy.reshape(-1, 1)
        
    # #     pnts_img = np.hstack((img_xx, img_yy, np.zeros_like(img_xx)))
    # #     pnts_img_p0 = np.subtract(pnts_img, self.ior)
    # #     pnts_obj_dir = (np.dot(self.R, pnts_img_p0.T)).T
    # #     pnts_obj_dir_norm = pnts_obj_dir / (np.sum(np.abs(pnts_obj_dir)**2, axis=-1)**(1./2)).reshape(-1, 1)
        
    # #     if min_dist is not None:
    # #         rays_start = self.prc + min_dist * pnts_obj_dir_norm
            
    # #     rays = []
    # #     for ix, row in enumerate(pnts_obj_dir_norm):
    # #         if min_dist is None:
    # #             rays.append(Ray([self.prc[0], self.prc[1], self.prc[2]], [row[0], row[1], row[2]]))
    # #         else:
    # #             rays.append(Ray([rays_start[ix, 0], rays_start[ix, 1], rays_start[ix, 2]], [row[0], row[1], row[2]]))
                
    # #     return rays
    
    # def euler2rot(self, euler):
    
    #     al = self.euler[0]
    #     ze = self.euler[1]
    #     ka = self.euler[2]
        
    #     R = np.empty((3, 3))

    #     R[0,0] = np.cos(al) * np.cos(ze) * np.cos(ka) - np.sin(al) * np.sin(ka)
    #     R[0,1] = -np.cos(al) * np.cos(ze) * np.sin(ka) - np.sin(al) * np.cos(ka)
    #     R[0,2] = np.cos(al) * np.sin(ze)
    #     R[1,0] = np.sin(al) * np.cos(ze) * np.cos(ka) + np.cos(al) * np.sin(ka)
    #     R[1,1] = -np.sin(al) * np.cos(ze) * np.sin(ka) + np.cos(al) * np.cos(ka)
    #     R[1,2] = np.sin(al) * np.sin(ze)
    #     R[2,0] = -np.sin(ze) * np.cos(ka)
    #     R[2,1] = np.sin(ze) * np.sin(ka)
    #     R[2,2] = np.cos(ze)
        
    #     return R
    
    # def from_dict(self, cam_data):
    #     self.s0 = cam_data["sigma0"]
    #     self.id = cam_data["img_id"]
    #     self.name = cam_data["name"]
        
    #     cam_eor = cam_data["eor"]
    #     self.prc = np.array([cam_eor["prj_ctr"]["E"], cam_eor["prj_ctr"]["N"], cam_eor["prj_ctr"]["H"]])
    #     self.prc_std = np.array([cam_eor["prj_ctr"]["std_E"], cam_eor["prj_ctr"]["std_N"], cam_eor["prj_ctr"]["std_H"]])
                
    #     cam_ior = cam_data["ior"]
    #     self.ior = np.array([cam_ior["x0"], cam_ior["y0"], cam_ior["f0"]])
    #     self.ior_std = np.array([cam_ior["std_x0"], cam_ior["std_y0"], cam_ior["std_f0"]])
        
    #     self.alpha = cam_data["eor"]["rot"]["alpha"]
    #     self.zeta = cam_data["eor"]["rot"]["zeta"]
    #     self.kappa = cam_data["eor"]["rot"]["kappa"]
        
    #     self.euler = np.array([self.alpha, self.zeta, self.kappa])
    #     self.euler_std = np.array([cam_data["eor"]["rot"]["std_rot_a"], cam_data["eor"]["rot"]["std_rot_z"], cam_data["eor"]["rot"]["std_rot_k"]])
        
    #     self.R = self.euler2rot(self.euler)
        
    #     self.meta = cam_data["meta"]
        
    #     self.img_w = int(self.meta["width"])
    #     self.img_h = int(self.meta["height"])
        
    #     self.hfov = np.arctan(self.img_w/(self.ior[2]*2))*2
    #     self.vfov = np.arctan(self.img_h/(self.ior[2]*2))*2
        
    #     self.status = "ok"
        
    # def hfov_geom(self, dist=100):

    #     #left side
    #     l_pnt_e = self.prc[0] + dist * np.sin(self.alpha_from_north(self.alpha) - self.hfov/2.)
    #     l_pnt_n = self.prc[1] + dist * np.cos(self.alpha_from_north(self.alpha) - self.hfov/2.)
        
    #     #right side
    #     r_pnt_e = self.prc[0] + dist * np.sin(self.alpha_from_north(self.alpha) + self.hfov/2.)
    #     r_pnt_n = self.prc[1] + dist * np.cos(self.alpha_from_north(self.alpha) + self.hfov/2.)
                               
    #     return "POLYGON((%.3f %.3f, %.3f %.3f, %.3f %.3f, %.3f %.3f))" % (self.prc[0], self.prc[1],
    #                                                                       l_pnt_e, l_pnt_n,
    #                                                                       r_pnt_e, r_pnt_n,
    #                                                                       self.prc[0], self.prc[1])
        
    #     fov_arr = np.array([[self.prc[0], self.prc[1]],
    #                         [l_pnt_e, l_pnt_n],
    #                         [r_pnt_e, r_pnt_n],
    #                         [self.prc[0], self.prc[1]]])
        
    #     #return Polygon(np.squeeze(fov_arr))
