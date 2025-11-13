import pygfx as gfx
import numpy as np
from scipy.stats import multivariate_normal
from lmfit import Parameters, minimize

def srs_lm(data, offset):
    gcp_obj = np.array(data["obj"])
    gcp_img = np.array(data["img"])
        
    assert np.shape(gcp_obj)[1] == 3
    assert np.shape(gcp_img)[1] == 2
    assert np.shape(gcp_obj)[0] == np.shape(gcp_img)[0]
        
    init_params = data["init_params"]
    params = Parameters()
    
    if offset is None:
        params.add("obj_x0", value=init_params["obj_x0"], vary=True)
        params.add("obj_y0", value=init_params["obj_y0"], vary=True)
        params.add("obj_z0", value=init_params["obj_z0"], vary=True)
                
    else:
        init_x0 = offset["offset_prc"][0]
        init_y0 = offset["offset_prc"][1]
        init_z0 = offset["offset_prc"][2]
        
        params.add("obj_x0", value=init_x0, min=init_x0 - 0.25, max=init_x0 + 0.25, vary=True)
        params.add("obj_y0", value=init_y0, min=init_y0 - 0.25, max=init_y0 + 0.25, vary=True)
        params.add("obj_z0", value=init_z0, min=init_z0 - 0.25, max=init_z0 + 0.25, vary=True)

    params.add("alpha", value=init_params["alpha"], vary=True)
    params.add("zeta", value=init_params["zeta"], vary=True)
    params.add("kappa", value=init_params["kappa"], vary=True)
        
    params.add("f", value=init_params["f"], vary=True)
        
    params.add("img_x0", value=init_params["img_x0"], vary=False)
    params.add("img_y0", value=init_params["img_y0"], vary=False)
    
    r = minimize(residual, params, args=(gcp_img, gcp_obj), method="least_squares")

    return r

def world2img(gcp_obj, p):

    """Transform world coordinates in camera coordinates.
    Parameters:
    XYZ (matrix 3xn): n points in world coordinates
    p (array or Parameters): 8 pose parameters
    Returns:
    xyz (array 2xn): n points in camera coordinates
    """
    if isinstance(p, dict):
        obj_x0 = p["obj_x0"]
        obj_y0 = p["obj_y0"]
        obj_z0 = p["obj_z0"]
        alpha = p["alpha"]
        zeta = p["zeta"]
        kappa = p["kappa"]
        f = p["f"]
        img_x0 = p["img_x0"]
        img_y0 = p["img_y0"]
    else:
        obj_x0 = p["obj_x0"].value
        obj_y0 = p["obj_y0"].value
        obj_z0 = p["obj_z0"].value
        alpha = p["alpha"].value
        zeta = p["zeta"].value
        kappa = p["kappa"].value
        f = p["f"].value
        img_x0 = p["img_x0"].value
        img_y0 = p["img_y0"].value
    
    rot = alzeka2rot(np.array([alpha, zeta, kappa]))
    
    # Vector camera DEM
    prc = np.array([obj_x0, obj_y0, obj_z0])

    # Translate
    gcp_obj_red = gcp_obj - prc
    
    den = gcp_obj_red[:, 0] * rot[0, 2] + gcp_obj_red[:, 1] * rot[1, 2] + gcp_obj_red[:, 2] * rot[2, 2]
    x_nom = gcp_obj_red[:, 0] * rot[0, 0] + gcp_obj_red[:, 1] * rot[1, 0] + gcp_obj_red[:, 2] * rot[2, 0]
    y_nom = gcp_obj_red[:, 0] * rot[0, 1] + gcp_obj_red[:, 1] * rot[1, 1] + gcp_obj_red[:, 2] * rot[2, 1]
    
    img_x = img_x0 - f * (x_nom/den)
    img_y = img_y0 - f * (y_nom/den)
        
    return np.hstack((img_x.reshape(-1, 1), 
                      img_y.reshape(-1, 1)))

def residual(params, img_gcp, obj_gcp):

    #obj_gcps reprojected into image using currently estimated paramters
    obj_gcp_img = world2img(obj_gcp, params)
    
    # difference between observed image coordinates and reprojected
    dx = img_gcp[:, 0] - obj_gcp_img[:, 0]
    dy = img_gcp[:, 1] - obj_gcp_img[:, 1]

    #reshape to dx0,dy0,dx1,dy1,dx2,dy2,....dxn,dyn
    res_xy = np.vstack((dx, dy)).ravel("F")
    
    return res_xy

def create_point_3d(pos, gid, clr):

    click_geom = gfx.Geometry(positions=np.array(pos).astype(np.float32).reshape(1, 3), 
                              gid=[gid])
    click_obj = gfx.Points(click_geom, 
                           gfx.PointsMaterial(color=clr, size=10))
                
    click_text = gfx.Text(geometry=None,
                          material=gfx.TextMaterial(color="#000", outline_color="#fff", outline_thickness=0.25),
                          markdown="**%s**" % (gid), 
                          font_size=30, 
                          anchor="Bottom-Center", 
                          screen_space=True)
    click_text.local.position = click_obj.geometry.positions.data[0, :] + [0, 0, 10]
    
    click_obj.add(click_text)   
    return click_obj
   
def alzeka2rot(alzeka):

    alzeka = np.atleast_2d(alzeka)
    
    alpha = alzeka[:, 0]
    zeta = alzeka[:, 1]
    kappa = alzeka[:, 2]
    
    rmat = np.empty((3, 3, alzeka.shape[0]), dtype=np.float64)
            
    rmat[0,0,:] = np.cos(alpha) * np.cos(zeta) * np.cos(kappa) - np.sin(alpha) * np.sin(kappa)
    rmat[0,1,:] = -np.cos(alpha) * np.cos(zeta) * np.sin(kappa) - np.sin(alpha) * np.cos(kappa)
    rmat[0,2,:] = np.cos(alpha) * np.sin(zeta)
    rmat[1,0,:] = np.sin(alpha) * np.cos(zeta) * np.cos(kappa) + np.cos(alpha) * np.sin(kappa)
    rmat[1,1,:] = -np.sin(alpha) * np.cos(zeta) * np.sin(kappa) + np.cos(alpha) * np.cos(kappa)
    rmat[1,2,:] = np.sin(alpha) * np.sin(zeta)
    rmat[2,0,:] = -np.sin(zeta) * np.cos(kappa)
    rmat[2,1,:] = np.sin(zeta) * np.sin(kappa)
    rmat[2,2,:] = np.cos(zeta)

    return np.squeeze(rmat)

def rot2alzeka(rot_mat):
    ze_1_rad = np.arccos(rot_mat[2,2])
    ze_2_rad = 2*np.pi - ze_1_rad
    if ze_2_rad < 0:
        ze_2_rad += 2*np.pi

    ka_1_rad = np.arctan2(rot_mat[2, 1], rot_mat[2, 0]*(-1))
    if ka_1_rad < 0:
        ka_2_rad = ka_1_rad + np.pi
    else:
        ka_2_rad = ka_1_rad - np.pi

    al_1_rad = np.arctan2(rot_mat[1, 2], rot_mat[0, 2])
    if al_1_rad < 0:
        al_2_rad = al_1_rad + np.pi
    else:
        al_2_rad = al_1_rad - np.pi

    alzekas = np.array([[al_1_rad, ze_1_rad, ka_1_rad], [al_2_rad, ze_2_rad, ka_2_rad]])
    return alzekas

def calc_hfov(img_w, focal):
    return 2*np.arctan(img_w/(2*focal))

def calc_vfov(img_h, focal):
    return 2*np.arctan(img_h/(2*focal))

def alpha2azi(alpha):
    return np.deg2rad((450 - np.rad2deg(alpha)) % 360)

def create_mono_smpls(cam_params, gcps):
    
    ori_data = {"gid":[], "img":[], "obj":[], "init_params":cam_params}

    for gid, gcp in gcps.items():
        if gcp["active"] == "1":
            ori_data["gid"].append(gid)
            ori_data["img"].append([gcp["img_x"], gcp["img_y"]])
            ori_data["obj"].append([gcp["obj_x"], gcp["obj_y"], gcp["obj_z"]])
            
    curr_offset = {"offset_prc":[cam_params["obj_x0"], 
                                    cam_params["obj_y0"], 
                                    cam_params["obj_z0"]]}

    res = srs_lm(ori_data, offset=curr_offset)

    cov_xx = np.array(res.covar)
    cov_xx_xy = np.pad(cov_xx, ((0,2),(0,2)), mode="constant", constant_values=0)

    img_xx = cam_params["xx_std"]
    img_yy = cam_params["yy_std"]
    trials = cam_params["nr_trials"]

    #image measurement accuracy
    cov_xx_xy[-2, -2] = img_xx
    cov_xx_xy[-1, -1] = img_yy

    means = np.array([cam_params["obj_x0"], cam_params["obj_y0"], cam_params["obj_z0"], 
                        cam_params["alpha"], cam_params["zeta"], cam_params["kappa"],
                        cam_params["f"], 0, 0])   #we draw samples around 0 0; True image point coordinates will be added later

    smpls = multivariate_normal.rvs(means, cov_xx_xy, size=trials)
    smpls = np.vstack((means, smpls))

    nr_s = smpls.shape[0]

    smpls_alzekas = smpls[:, 3:6]    
    rmats = alzeka2rot(smpls_alzekas)
    
    cmats = np.array([[np.ones((1, 1, nr_s)), np.zeros((1, 1, nr_s)), np.full((1, 1, nr_s), -cam_params["img_x0"])],
                      [np.zeros((1, 1, nr_s)), np.ones((1, 1, nr_s)), np.full((1, 1, nr_s), -cam_params["img_y0"])],
                      [np.zeros((1, 1, nr_s)), np.zeros((1, 1, nr_s)), -smpls[:, 6].reshape(1, 1, nr_s)]]).squeeze()
    
    dir2pnts = np.einsum("ijk,jmk->imk", rmats, cmats)
    
    return means, smpls, dir2pnts

def smpls_to_rays(smpls, dir2pnts, img_x, img_y, min_d_mono, min_xyz):       
    
    img_pnts = smpls[:, -2:] + np.array([img_x, img_y])
    img_pnts = np.hstack((img_pnts, np.ones((np.shape(img_pnts)[0], 1)))).T
    
    ray_dir = np.einsum('ijk,jk -> ik', dir2pnts, img_pnts).T
    ray_dir /= np.linalg.norm(ray_dir, axis=1).reshape(-1, 1)
    
    smpls_prc_local = smpls[:, :3] - min_xyz
    
    rays = np.hstack((smpls_prc_local + min_d_mono*ray_dir, ray_dir))
    return rays

def max_evec_dir_north(cmat):
    ans_covar_xy = cmat[:2, :2]
    eval, evec = np.linalg.eigh(ans_covar_xy)
    max_ex = np.argmax(eval)
    max_eval = eval[max_ex]
    max_evec = evec[:, max_ex]
    
    if max_evec[0] < 0:
        max_evec *= -1
    
    north_dir = np.array([0, 1])
    max_evec_xy_dir = max_evec/np.linalg.norm(max_evec)
    dir_north_evec = np.arccos((np.dot(north_dir, max_evec_xy_dir)))
    
    return dir_north_evec