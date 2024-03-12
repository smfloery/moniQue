from lmfit import Parameters, minimize
import numpy as np
<<<<<<< HEAD

def alzeka2rot(euler):
    
    al = euler[0]
    ze = euler[1]
    ka = euler[2]
    
    R = np.empty((3, 3))

    R[0,0] = np.cos(al) * np.cos(ze) * np.cos(ka) - np.sin(al) * np.sin(ka)
    R[0,1] = -np.cos(al) * np.cos(ze) * np.sin(ka) - np.sin(al) * np.cos(ka)
    R[0,2] = np.cos(al) * np.sin(ze)
    R[1,0] = np.sin(al) * np.cos(ze) * np.cos(ka) + np.cos(al) * np.sin(ka)
    R[1,1] = -np.sin(al) * np.cos(ze) * np.sin(ka) + np.cos(al) * np.cos(ka)
    R[1,2] = np.sin(al) * np.sin(ze)
    R[2,0] = -np.sin(ze) * np.cos(ka)
    R[2,1] = np.sin(ze) * np.sin(ka)
    R[2,2] = np.cos(ze)
    
    return R

def srs_lm(init_params, gcp_obj, gcp_img):
    params = Parameters()
    params.add("X", value=init_params["X"], vary=True)
    params.add("Y", value=init_params["Y"], vary=True)
    params.add("Z", value=init_params["Z"], vary=True)
=======
from .helpers import alzeka2rot

def srs_lm(data):
    
    gcp_obj = np.array(data["obj"])
    gcp_img = np.array(data["img"])
    
    assert np.shape(gcp_obj)[1] == 3
    assert np.shape(gcp_img)[1] == 2
    assert np.shape(gcp_obj)[0] == np.shape(gcp_img)[0]
    
    init_params = data["init_params"]
    
    params = Parameters()
    params.add("obj_x0", value=init_params["obj_x0"], vary=True)
    params.add("obj_y0", value=init_params["obj_y0"], vary=True)
    params.add("obj_z0", value=init_params["obj_z0"], vary=True)
>>>>>>> restructure
    
    params.add("alpha", value=init_params["alpha"], vary=True)
    params.add("zeta", value=init_params["zeta"], vary=True)
    params.add("kappa", value=init_params["kappa"], vary=True)
    
    params.add("f", value=init_params["f"], vary=True)
    
<<<<<<< HEAD
    params.add("x0", value=init_params["x0"], vary=False)
    params.add("y0", value=init_params["y0"], vary=False)

    r = minimize(residual, params, args=(gcp_img, gcp_obj), method="leastsq")

    if r.success == False:
        return None
    
    est_prc_x = r.params["X"].value
    est_prc_y = r.params["Y"].value
    est_prc_h = r.params["Z"].value
    est_alpha = r.params["alpha"].value
    est_zeta = r.params["zeta"].value
    est_kappa = r.params["kappa"].value
    est_focal = r.params["f"].value
    
    est_params = {"X":est_prc_x, 
                  "Y":est_prc_y, 
                  "Z":est_prc_h, 
                  "alpha":est_alpha, 
                  "zeta": est_zeta, 
                  "kappa": est_kappa, 
                  "f": est_focal, 
                  "x0": init_params["x0"], 
                  "y0": init_params["y0"]
                  }

    cxx = r.covar
    cxx_names = r.var_names
    
    return (est_params, cxx, cxx_names, r.residual)
=======
    params.add("img_x0", value=init_params["img_x0"], vary=False)
    params.add("img_y0", value=init_params["img_y0"], vary=False)

    r = minimize(residual, params, args=(gcp_img, gcp_obj), method="leastsq")
    return r
>>>>>>> restructure

def world2img(gcp_obj, p):

    """Transform world coordinates in camera coordinates.
    Parameters:
    XYZ (matrix 3xn): n points in world coordinates
    p (array or Parameters): 8 pose parameters
    Returns:
    xyz (array 2xn): n points in camera coordinates
    """
    if isinstance(p, dict):
<<<<<<< HEAD
        X = p["X"]
        Y = p["Y"]
        Z = p["Z"]
=======
        obj_x0 = p["obj_x0"]
        obj_y0 = p["obj_y0"]
        obj_z0 = p["obj_z0"]
>>>>>>> restructure
        alpha = p["alpha"]
        zeta = p["zeta"]
        kappa = p["kappa"]
        f = p["f"]
<<<<<<< HEAD
        cx = p["x0"]
        cy = p["y0"]
    else:
        X = p["X"].value
        Y = p["Y"].value
        Z = p["Z"].value
=======
        img_x0 = p["img_x0"]
        img_y0 = p["img_y0"]
    else:
        obj_x0 = p["obj_x0"].value
        obj_y0 = p["obj_y0"].value
        obj_z0 = p["obj_z0"].value
>>>>>>> restructure
        alpha = p["alpha"].value
        zeta = p["zeta"].value
        kappa = p["kappa"].value
        f = p["f"].value
<<<<<<< HEAD
        cx = p["x0"].value
        cy = p["y0"].value
        
    rot = alzeka2rot(np.array([alpha, zeta, kappa]))
    
    # Vector camera DEM
    prc = np.array([X, Y, Z])

    # Translate
    gcp_min_prc = gcp_obj - prc

    den = gcp_min_prc[:, 0] * rot[0, 2] + gcp_min_prc[:, 1] * rot[1, 2] + gcp_min_prc[:, 2] * rot[2, 2]
    x_nom = gcp_min_prc[:, 0] * rot[0, 0] + gcp_min_prc[:, 1] * rot[1, 0] + gcp_min_prc[:, 2] * rot[2, 0]
    y_nom = gcp_min_prc[:, 0] * rot[0, 1] + gcp_min_prc[:, 1] * rot[1, 1] + gcp_min_prc[:, 2] * rot[2, 1]
    
    x = -f * (x_nom/den) + cx
    y = -f * (y_nom/den) + cy
    
    return np.hstack((x.reshape(-1, 1), y.reshape(-1, 1)))

def residual(params, xy, XYZ):
    """Function which compares the measurements with the model
    params (Parameters): 8 perspective parameters
    xy (array nx2): image coordinates GCP
    XYZ (array nx3): world coordinates GCP
    Returns:
    r (array nx1): residuals
    """
    xy_p = world2img(XYZ, params)
    
    nObs = len(xy_p)
    
    # Computation of the residuals
    dx = xy[:, 0] - xy_p[:, 0]
    dy = xy[:, 1] - xy_p[:, 1]

    # 1D vector of the residual
    r = []
    for i in range(nObs):
        r.append(dx[i])
        r.append(dy[i])
    r = np.asarray(r)

    return r
=======
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
>>>>>>> restructure
