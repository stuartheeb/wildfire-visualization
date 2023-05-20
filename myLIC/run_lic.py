"""
5.17
LIC
"""
import torch
import numpy as np
import math
import matplotlib.pyplot as plt
from scipy import signal
import argparse
torch.random.manual_seed(414)

def GaussianKernel(s, length):
    sigma = length / 3.0
    return 1.0/math.sqrt(2.0 * sigma ** 2) * torch.exp(-0.5 * (s / sigma)**2)

def AsymForwardKernel(s, length, asym_scale = 1.0/5.0):
    sigma = length / 3.0
    peak = 1.0/math.sqrt(2.0 * sigma ** 2)
    res = torch.where(s < 0, 
                       peak * torch.exp(-0.5 * (s / sigma)**2),
                       -peak/(sigma/asym_scale) * s + peak)
    res = torch.where(s >= sigma/asym_scale, 0.0, res)
    return res

def getTangent(u, f):
    direction = torch.where(torch.greater(u, 0.0), (1.0 - f) / u, -(f + 1.0) / u)
    res = torch.where(torch.abs(u) < 1e-6, 1e10, direction)
    return res

def boundaryCondition(x, y, offset_x, offset_y, W, H):
    zeros = torch.zeros_like(x)
    fzeros = torch.zeros_like(offset_x)
    x = x.clone()
    y = y.clone()
    offset_x = offset_x.clone()
    offset_y = offset_y.clone()

    x = torch.where(x < 0, zeros, x)
    offset_x = torch.where(x < 0, fzeros, offset_x)
    x = torch.where(x >= W, zeros + W - 1, x)
    offset_x = torch.where(x >= W, fzeros + 1, offset_x)

    y = torch.where(y < 0, zeros, y)
    offset_y = torch.where(y < 0, fzeros, offset_y)
    y = torch.where(y >= H, zeros + H - 1, y)
    offset_y = torch.where(y >= H, fzeros + 1, offset_y)

    return x, y, offset_x, offset_y

def getButterWhite(W, H, wn):
    white = np.random.rand(W, H)
    b, a = signal.butter(4, wn, 'lowpass')
    butter_white = signal.filtfilt(b, a, white)
    return torch.tensor(butter_white.copy(), dtype=torch.float32)
    
def getNoise(W: int, H: int, noiseType: str="white", wn: float=0.8):
    if noiseType == "white":
        print("> White")
        return torch.rand(W, H)
    elif noiseType == "butter_white":
        print("> Butterworth White")
        return getButterWhite(W, H, wn)
    else:
        raise TypeError("Invalid noise type.")
    
def advection(ux, uy, offset_x, offset_y):
    tx = getTangent(ux, offset_x)
    ty = getTangent(uy, offset_y)
    condition = tx < ty
    dt = torch.where(condition, tx, ty)
    offset_x += ux * dt
    offset_y += uy * dt

    zeros = torch.zeros_like(offset_x, dtype=torch.float32)
    ones = torch.ones_like(offset_y, dtype=torch.float32)
    fx_proj = torch.where(condition, 
                          torch.where(ux > 0, zeros, ones), 
                          offset_x)
    fy_proj = torch.where(condition, 
                          offset_y, 
                          torch.where(uy > 0, zeros, ones))

    zeros = zeros.clone().detach().to(torch.int32)
    ones = ones.clone().detach().to(torch.int32)
    dx = torch.where(condition, torch.where(ux > 0, ones, -ones), zeros)
    dy = torch.where(condition, zeros, torch.where(uy > 0, ones, -ones))

    return dt, dx, dy, fx_proj, fy_proj

def convLoop(noise, x, y, vx, vy, offset_x, offset_y, h, s, t, length, W, H, kernelType="gauss", forward=None):
    ux = vx.detach().clone()
    uy = vy.detach().clone()
    shifted_noise = noise.detach().clone()
    x = x.clone()
    y = y.clone()
    offset_x = offset_x.clone()
    offset_y = offset_y.clone()
    h = h.clone()
    s = s.clone()
    pixels = torch.zeros_like(noise)
    dh = torch.zeros_like(h)
    while s.abs().mean() < length:
        ux = vx[x, y]
        uy = vy[x, y]
        shifted_noise = noise[x, y]
        dt, dx, dy, offset_x, offset_y = advection(ux, uy, offset_x, offset_y)
        v = torch.sqrt(ux ** 2.0 + uy ** 2.0)
        ds = v * dt ### arc length seg
        if kernelType == "gauss":
            dh = GaussianKernel(s, length) * ds
        elif kernelType == "asymf":
            dh = AsymForwardKernel(s, length, 1.0) * ds
        else:
            raise ValueError("Invalid convType")
        pixels += shifted_noise * dh    ### conv
        h += dh
        if forward:
            s += ds
        else:
            s -= ds
        x += dx
        y += dy
        x, y, offset_x, offset_y = boundaryCondition(x, y, offset_x, offset_y, W, H)
    return pixels, h, s, x, y, offset_x, offset_y

def lic(vx, vy, length=25.0, convType="gauss", noiseType="white", wn=0.75, return_magnitude=True):
    W, H = vx.shape
    noise = getNoise(W, H, noiseType, wn=wn)
    # if convType == "asymf":
    #     print("> using sparse noise")
    #     i = torch.randperm(W)[:600]
    #     j = torch.randperm(H)[:600]
    #     noise = torch.zeros(W, H)
    #     noise[i, j] = 1.0

    x, y = torch.meshgrid(torch.arange(W), torch.arange(H), indexing="ij")
    fx = 0.5 * torch.ones_like(vx)
    fy = 0.5 * torch.ones_like(vy)
    h, s, t = torch.zeros_like(noise), torch.zeros_like(noise), torch.zeros_like(noise)
    pixel_1, pixel_2, h1, h2 = None, None, None, None
    if convType == "gauss":
        pixel_1, h1, _, _, _, _, _ = convLoop(noise, x, y, vx, vy, fx, fy, h, s, t, length, W, H, "gauss", True)
        print("> forward done")
        pixel_2, h2, _, _, _, _, _ = convLoop(noise, x, y, -vx, -vy, fx, fy, h, s, t, length, W, H, "gauss", False)
        print("> backward done")
    elif convType == "asymf":
        pixel_1, h1, _, _, _, _, _ = convLoop(noise, x, y, vx, vy, fx, fy, h, s, t, 0.01*length, W, H, "asymf", True)
        print("> forward done")
        pixel_2, h2, _, _, _, _, _ = convLoop(noise, x, y, -vx, -vy, fx, fy, h, s, t, length, W, H, "asymf", False)
        print("> backward done")
    res = (pixel_1 + pixel_2) / (h1 + h2)
    if return_magnitude:
        res *= torch.erf(torch.sqrt(vx ** 2.0 + vy ** 2.0))
    def normalize(arr: np.ndarray): return (arr - arr.min()) / (arr - arr.min()).max()
    def contrast(v: np.ndarray): return 0.5*(1.0-np.cos(np.pi*v))
    # return contrast(normalize(res))
    return res

def runLIC(npArray: np.ndarray, imgName: str, args: argparse.ArgumentError):
    velocityField = torch.tensor(npArray, dtype=torch.float32)
    vx = velocityField[:, :, 0]
    vy = velocityField[:, :, 1]
    assert args.convType in ["gauss", "asymf"]
    assert args.noiseType in ["white", "butter_white"]
    resTorch = lic(vx, vy, args.kernelLength, args.convType, args.noiseType, args.wn, return_magnitude=True)

    resNP = resTorch.numpy()
    if resNP.shape[0] < resNP.shape[1]:
        resNP = resNP.transpose()
    save_grey(imgName, resNP)

def save_grey(name, img):
    img = img[:, ::-1]
    img = img.T
    W, H = img.shape
    texture = np.empty((W, H, 4), np.float32)
    texture[:, :, 0] = img
    texture[:, :, 1] = img
    texture[:, :, 2] = img
    texture[:, :, 3] = 1
    texture = np.clip(texture, 0.0, 1.0)
    plt.imsave(name, texture)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--npy_path', type=str, default='./slice_backcurve40_8000.npy', help="Path to the NPY file")
    parser.add_argument('--convType', type=str, default='gauss', help="gauss | asymf: asympotic forward")
    parser.add_argument('--noiseType', type=str, default='white', help="white | butter_white: asympotic forward")
    parser.add_argument('--kernelLength', type=float, default=100.0, help="")
    parser.add_argument('--wn', type=float, default=0.75, help="[0.0, 1.0], for butter worth band width")
    args = parser.parse_args()
    print(args)
    
    vf_np = np.load(args.npy_path)
    convType = args.convType
    noiseType= args.noiseType
    file_name = args.npy_path.split('/')[-1].split('.npy')[0]
    img_name = "LIC_{}_{}_{}_{}.png".format(file_name, args.convType, args.kernelLength, args.noiseType)
    runLIC(vf_np, img_name, args)
    print("> saved to: {}".format(img_name))