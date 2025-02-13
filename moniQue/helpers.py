import pygfx as gfx
import numpy as np

def create_point_3d(pos, gid, clr):

    click_geom = gfx.Geometry(positions=np.array(pos).astype(np.float32).reshape(1, 3), 
                              gid=[gid])
    click_obj = gfx.Points(click_geom, 
                           gfx.PointsMaterial(color=clr, size=10))
                
    click_text = gfx.Text(
        gfx.TextGeometry(markdown="**%s**" % (gid), font_size=16, anchor="Bottom-Center", screen_space=True),
        gfx.TextMaterial(color="#000", outline_color="#fff", outline_thickness=0.25))
    click_text.local.position = click_obj.geometry.positions.data[0, :] + [0, 0, 10]
    
    click_obj.add(click_text)   
    return click_obj
   
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