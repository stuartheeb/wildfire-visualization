'''
5.14
following test_vorticity.py
for LIC
'''
import os
import vtk
import numpy as np
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
import colormap
from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk


def main():
    print("[WildFireB]")
    # lic("vortices", "test_licpy.png")

    ### =================  IO  =================
    grid_file_name = "../dataset/mountain_backcurve320/output.40000.vts"
    # grid_file_name = "../dataset\\mountain_backcurve320\\output.40000.vts"
    grid_datasetReader = vtk.vtkXMLStructuredGridReader()
    grid_datasetReader.SetFileName(grid_file_name)
    grid_datasetReader.Update()
    grid_dataset = grid_datasetReader.GetOutput()


    ### =================  Setting for resampling  =================
    bounds = np.array(grid_dataset.GetBounds())     ### point bounds
    bbox = np.array(grid_dataset.GetExtent())     ### point index
    resampledOrigin = bounds[::2]
    resampledPointsDims = np.array([1200, 10, 800], dtype=int)
    resampledCellsDims = resampledPointsDims - 1
    resampledCellSpacing = (bounds[1::2] - bounds[:-1:2]) / resampledCellsDims

    ### =================  resample to image & extract attributes  =================
    ### vtkResampleToImage
    resampler = vtk.vtkResampleToImage()
    resampler.AddInputDataObject(grid_dataset)
    resampler.SetSamplingDimensions(resampledPointsDims)  ### set for #points
    resampler.SetSamplingBounds(bounds)
    resampler.Update()
    ImageData = resampler.GetOutput()


    ### =================  velocity field  =================
    calcMag = vtk.vtkArrayCalculator()
    calcMag.SetInputData(ImageData)
    calcMag.AddScalarVariable("u_var", "u", 0)
    calcMag.AddScalarVariable("v_var", "v", 0)
    calcMag.AddScalarVariable("w_var", "w", 0)
    calcMag.SetResultArrayName("wind_velocity_mag")
    calcMag.SetFunction("sqrt(u_var^2+v_var^2+w_var^2)")
    calcMag.SetAttributeTypeToPointData()
    calcMag.Update()
    windVelMagVtkArray = calcMag.GetOutput().GetPointData().GetArray("wind_velocity_mag")

    calcCompose = vtk.vtkArrayCalculator()
    calcCompose.SetInputConnection(calcMag.GetOutputPort())
    calcCompose.AddScalarVariable("u_var", "u", 0)
    calcCompose.AddScalarVariable("v_var", "v", 0)
    calcCompose.AddScalarVariable("w_var", "w", 0)
    calcCompose.SetResultArrayName("wind_velocity")
    calcCompose.SetFunction("u_var*iHat+v_var*jHat+w_var*kHat")
    calcCompose.SetAttributeTypeToPointData()
    calcCompose.Update()
    windVelocityVtkArray = calcCompose.GetOutput().GetPointData().GetArray("wind_velocity")
    
    
    ### =================  LIC ==================
    validMaskVtkArray = ImageData.GetPointData().GetArray("vtkValidPointMask")
    validMaskNP = vtk_to_numpy(validMaskVtkArray)
    validMaskSlice = validMaskNP.reshape(list(resampledPointsDims)[::-1])[:, resampledPointsDims[1]//2, :].astype(np.float32)
    
    windWelocityNP = vtk_to_numpy(windVelocityVtkArray)
    vec = windWelocityNP.reshape(list(resampledPointsDims)[::-1] + [3])  # (z, y, x, (w, v, u))
    xData = vec[:, resampledPointsDims[1]//2, :, 2]
    yData = vec[:, resampledPointsDims[1]//2, :, 0]
    # xData = np.multiply(xData, validMaskSlice)
    # yData = np.multiply(yData, validMaskSlice)
    xData = np.expand_dims(xData, -1)
    yData = np.expand_dims(yData, -1)

    vectorField = np.concatenate([xData, yData], -1)
    if "backcurve40" in grid_file_name:
        np.save("backcurve40.npy", vectorField)
    elif "backcurve320" in grid_file_name:
        np.save("backcurve320.npy", vectorField)
    print("> saved: npy")
    
if __name__ == "__main__":
    main()
