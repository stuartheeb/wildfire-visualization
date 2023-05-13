import vtk
import numpy as np
import json
from scipy.interpolate import interp1d

fire_path = "dataset/SV_fire.json"
vapor_path = "dataset/SV_vapor.json"
grass_path = "dataset/SV_grass.json"
soil_path = "dataset/SV_soil.json"
vorticity_path = "dataset/SV_vorticity.json"


### =================  theta  =================
f = open(fire_path)
SV_fire = json.load(f)
f.close()
thetaColormap = vtk.vtkColorTransferFunction()
thetaColormap.SetColorSpaceToRGB()
for i in range(len(SV_fire[0]["RGBPoints"]) // 4):
    xrgb = SV_fire[0]["RGBPoints"][i*4:(i+1)*4]
    thetaColormap.AddRGBPoint(xrgb[0], xrgb[1], xrgb[2], xrgb[3])
thetaOpacity = vtk.vtkPiecewiseFunction()
thetaOpacity.AddPoint(303, 0.0)
thetaOpacity.AddPoint(353, 0.0029)
thetaOpacity.AddPoint(568, 0.745)
thetaOpacity.AddPoint(979, 1)
thetaOpacity.SetClamping(True)

thetaVolumeProperty = vtk.vtkVolumeProperty()
thetaVolumeProperty.SetColor(thetaColormap)
thetaVolumeProperty.SetScalarOpacity(thetaOpacity)
thetaVolumeProperty.SetInterpolationTypeToLinear()


### =================  watervapor  =================
f = open(vapor_path)
SV_vapor = json.load(f)
f.close()
vaporColormap = vtk.vtkColorTransferFunction()
vaporColormap.SetColorSpaceToRGB()
for i in range(len(SV_vapor[0]["RGBPoints"]) // 4):
    xrgb = SV_vapor[0]["RGBPoints"][i*4:(i+1)*4]
    vaporColormap.AddRGBPoint(xrgb[0], xrgb[1], xrgb[2], xrgb[3])    
vaporOpacity = vtk.vtkPiecewiseFunction()
vaporOpacity.AddPoint(0.00039894226938486099, 0)
vaporOpacity.AddPoint(0.0826896, 0.323214)
vaporOpacity.SetClamping(True)    
   
vaporVolumeProperty = vtk.vtkVolumeProperty()
vaporVolumeProperty.SetColor(vaporColormap)
vaporVolumeProperty.SetScalarOpacity(vaporOpacity)
vaporVolumeProperty.SetInterpolationTypeToLinear()


### =================  grass  =================
f = open(grass_path)
SV_grass = json.load(f)
f.close()
grassColormap = vtk.vtkColorTransferFunction()
grassColormap.SetColorSpaceToLab()
for i in range(len(SV_grass[0]["RGBPoints"]) // 4):
    xrgb = SV_grass[0]["RGBPoints"][i*4:(i+1)*4]
    grassColormap.AddRGBPoint(xrgb[0], xrgb[1], xrgb[2], xrgb[3])
grassOpacity = vtk.vtkPiecewiseFunction()
grassOpacity.AddPoint(0, 0)
grassOpacity.AddPoint(0.0864706, 0.425595)
grassOpacity.AddPoint(0.161963, 0.895833)
grassOpacity.AddPoint(0.6, 0.991071)

grassVolumeProperty = vtk.vtkVolumeProperty()
grassVolumeProperty.SetColor(grassColormap)
grassVolumeProperty.SetScalarOpacity(grassOpacity)
grassVolumeProperty.SetInterpolationTypeToLinear()


f = open(soil_path)
SV_soil = json.load(f)
f.close()
numColors = 128
rgba_list = []
for i in range(len(SV_soil[0]["RGBPoints"]) // 4):
    xrgb = SV_soil[0]["RGBPoints"][i*4:(i+1)*4]
    rgba_list.append(xrgb[-3:] + [1.0])
soil_RGBA = np.array(rgba_list)
x = np.linspace(0, 1, len(soil_RGBA))
getColorCorrespondingToValue = interp1d(x, soil_RGBA.T)

soilLookupTable = vtk.vtkLookupTable()
soilLookupTable.SetScaleToLinear()
soilLookupTable.SetNumberOfTableValues(numColors)
for i in range(numColors):
    val = i / (numColors - 1)
    r, g, b, a = getColorCorrespondingToValue(val) ### a 1d interpolate mapper
    soilLookupTable.SetTableValue(i, r, g, b, a) 
soilLookupTable.Build()

### =================  streamline  =================
stream_RGBA = np.array([[0.231373, 0.298039, 0.752941, 1], 
                        [0.865003, 0.865003, 0.865003, 1],
                        [1, 0, 0, 1]])
x = np.linspace(0, 1, len(stream_RGBA))
getColorCorrespondingToValue = interp1d(x, stream_RGBA.T)
streamLookupTable = vtk.vtkLookupTable()
streamLookupTable.SetScaleToLinear()
streamLookupTable.SetNumberOfTableValues(numColors)
for i in range(numColors):
    val = i / (numColors - 1)
    r, g, b, a = getColorCorrespondingToValue(val)
    streamLookupTable.SetTableValue(i, r, g, b, a)
streamLookupTable.Build()

### =================  vorticity  =================
f = open(vorticity_path)
SV_vorticity = json.load(f)
f.close()
vorticityColormap = vtk.vtkColorTransferFunction()
vorticityColormap.SetColorSpaceToDiverging()
for i in range(len(SV_vorticity[0]["RGBPoints"]) // 4):
    xrgb = SV_vorticity[0]["RGBPoints"][i*4:(i+1)*4]
    vorticityColormap.AddRGBPoint(xrgb[0], xrgb[1], xrgb[2], xrgb[3])
vorticityOpacity = vtk.vtkPiecewiseFunction()
vorticityOpacity.AddPoint(0.0, 0)
vorticityOpacity.AddPoint(0.395686, 0)
vorticityOpacity.AddPoint(3.18132, 0.1525)

vorticityVolumeProperty = vtk.vtkVolumeProperty()
vorticityVolumeProperty.SetColor(vorticityColormap)
vorticityVolumeProperty.SetScalarOpacity(vorticityOpacity)
vorticityVolumeProperty.SetInterpolationTypeToLinear()


volumePropertiess = {
    'grass': grassVolumeProperty,
    'theta': thetaVolumeProperty,
    'vapor': vaporVolumeProperty,
    'vorticity': vorticityVolumeProperty
}