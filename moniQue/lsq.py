from lmfit import Parameters, minimize
import numpy as np
from .helpers import alzeka2rot

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
        params.add("obj_x0", value=init_params["obj_x0"] + offset['offset_x'], vary=False)
        params.add("obj_y0", value=init_params["obj_y0"] + offset['offset_y'], vary=False)
        params.add("obj_z0", value=init_params["obj_z0"] + offset['offset_z'], vary=False)

    params.add("alpha", value=init_params["alpha"], vary=True)
    params.add("zeta", value=init_params["zeta"], vary=True)
    params.add("kappa", value=init_params["kappa"], vary=True)
        
    params.add("f", value=init_params["f"], vary=True)
        
    params.add("img_x0", value=init_params["img_x0"], vary=False)
    params.add("img_y0", value=init_params["img_y0"], vary=False)

    r = minimize(residual, params, args=(gcp_img, gcp_obj), method="leastsq")
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
