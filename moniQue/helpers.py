import pygfx as gfx
import numpy as np

def create_point_3d(pos, gid):

    click_geom = gfx.Geometry(positions=np.array(pos).astype(np.float32).reshape(1, 3), 
                              gid=[gid])
    click_obj = gfx.Points(click_geom, 
                           gfx.PointsMaterial(color=(0.78, 0, 0, 1), size=10))
                
    click_text = gfx.Text(
        gfx.TextGeometry(markdown="**%s**" % (gid), font_size=16, anchor="Bottom-Center", screen_space=True),
        gfx.TextMaterial(color="#000", outline_color="#fff", outline_thickness=0.25))
    click_text.local.position = click_obj.geometry.positions.data[0, :] + [0, 0, 10]
    
    click_obj.add(click_text)   
    return click_obj

def proj_mat_to_rkz(proj_mat):
    a_mat = proj_mat[:3, :3]
    a_vec = proj_mat[:, 3].reshape(3, 1)    #last row of P
    
    z_vec = - np.linalg.inv(a_mat)@a_vec
    print(z_vec)    