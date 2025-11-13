import numpy as np
import matplotlib.pyplot as plt

if __name__ == "__main__":
    
    mean = [0, 0, 0]
    cov = np.array([[1, 0, 0], 
                    [0, 7, 0],
                    [0, 0, 10]])
    
    smpls = np.random.multivariate_normal(mean, cov, 1000)
    
    smpl_cov = np.cov(smpls, rowvar=False)
    print(smpl_cov)
    print(np.cov(smpls[:, :2], rowvar=False))
          
    # eval, evec = np.linalg.eigh(smpl_cov)
    
    # max_ex = np.argmax(eval)
    # max_eval = eval[max_ex]
    # max_evec = evec[:, max_ex]
    
    # if max_evec[0] < 0:
    #     max_evec *= -1
    
    # max_start_pnt = 0*max_evec.T
    # max_end_pnt = np.sqrt(max_eval) * max_evec.T

    # min_ex = np.argmin(eval)
    # min_eval = eval[min_ex]
    # min_evec = evec[:, min_ex]
    # min_start_pnt = 0*min_evec.T
    # min_end_pnt = np.sqrt(min_eval) * min_evec.T
    
    # north_dir = np.array([0, 1])
    # max_evec_dir = max_evec/np.linalg.norm(max_evec)
    # dir_north_evec = np.arccos((np.dot(north_dir, max_evec_dir)))
    
    # print(np.rad2deg(dir_north_evec))
    
    # fix, ax = plt.subplots(nrows=1, ncols=1)
    # ax.scatter(x=smpls[:, 0], y=smpls[:, 1], s=2)
    # ax.plot([max_start_pnt[0], max_end_pnt[0]], [max_start_pnt[1], max_end_pnt[1]], c="red")
    # ax.plot([min_start_pnt[0], min_end_pnt[0]], [min_start_pnt[1], min_end_pnt[1]], c="green")
    # ax.axis('equal')
    # plt.show()