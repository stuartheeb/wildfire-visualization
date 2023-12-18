'''
5.15 Stuart
Preprocessing for fast GUI
'''
import os
import vtk
import numpy as np
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
import colormap
from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk
import time
import argparse


Attribute2IndexDict = {"O2": 0,
                        "convht_1": 1,
                        "frhosiesrad_1": 2,
                        "rhof_1": 3,
                        "rhowatervapor": 4,
                        "theta": 5,
                        "u": 6,
                        "v": 7,
                        "w": 8,
                        "vtkValidPointMask": 9,
                        "vtkGhostType": 10}

### for better ui interaction
class MyInteractorStyle(vtkInteractorStyleTrackballCamera):
    def __init__(self, parent=None):
        pass

def vtkArray2vtkImageData(vtkArray, origin, dimension, spacing, isScalar=True, isPoint=True):
    """
    Converting extracted vtkArray into vtkImageData.
    Can be either scalar points or vector points.

    Args:
        vtkArray (_type_): _description_
        origin (_type_): _description_
        dimension (_type_): point dimes
        spacing (_type_): cell spacing

    Returns:
        _type_: _description_
    """
    image = vtk.vtkImageData()
    image.SetOrigin(origin)
    image.SetDimensions(dimension)
    image.SetSpacing(spacing)
    if isPoint is True:
        if isScalar is True:
            image.GetPointData().SetScalars(vtkArray)
        else:
            image.GetPointData().SetVectors(vtkArray)
    else:
        raise ValueError(">>> Cannot use for cell data. Please manually convert it to vtkImageData.")
    return image

def observeCamera(obj, event):
    camera = obj.GetRenderWindow().GetRenderers().GetFirstRenderer().GetActiveCamera()
    print("GetPosition: ", camera.GetPosition())
    print("GetFocalPoint: ", camera.GetFocalPoint())

def preprocess(grid_file_name):

    temp = dict()

    grid_datasetReader = vtk.vtkXMLStructuredGridReader()
    grid_datasetReader.SetFileName(grid_file_name)
    grid_datasetReader.Update()
    grid_dataset = grid_datasetReader.GetOutput()

    ### =================  Setting for resampling  =================
    bounds = np.array(grid_dataset.GetBounds())     ### point bounds
    extent = np.array(grid_dataset.GetExtent())     ### point index
    resampledOrigin = bounds[::2]
    resampledPointsDims = np.array([300, 250, 150], dtype=int)
    resampledCellsDims = resampledPointsDims - 1
    resampledCellSpacing = (bounds[1::2] - bounds[:-1:2]) / resampledCellsDims


    ### =================  extract subset of curvilinear data  =================
    ### extract grass
    extractor_sub10 = vtk.vtkExtractGrid()
    extractor_sub10.SetInputData(grid_dataset)
    extractor_sub10.SetVOI(extent[0], extent[1], extent[2], extent[3], 0, 10)
    extractor_sub10.Update()
    GridDataset_sub10 = extractor_sub10.GetOutput()    

    grassBounds = np.array(GridDataset_sub10.GetBounds())
    grassExtent = np.array(GridDataset_sub10.GetExtent())
    grassOrigin = grassBounds[::2]
    grassPointsDims = np.array([300, 250, 200], dtype=int)
    grassCellsDims = grassPointsDims - 1
    grassCellSpacing = (grassBounds[1::2] - grassBounds[:-1:2]) / grassCellsDims
    resampler_sub10 = vtk.vtkResampleToImage()
    resampler_sub10.AddInputDataObject(GridDataset_sub10)
    resampler_sub10.SetSamplingDimensions(grassPointsDims)  ### set for #points
    resampler_sub10.SetSamplingBounds(bounds)
    resampler_sub10.Update()
    ImageData_sub10 = resampler_sub10.GetOutput()

    grassVtkArray = ImageData_sub10.GetPointData().GetArray("rhof_1")

    ### extract soil  
    extractor_sub5 = vtk.vtkExtractGrid()
    extractor_sub5.SetInputData(grid_dataset)
    extractor_sub5.SetVOI(extent[0], extent[1], extent[2], extent[3], 0, 5)
    extractor_sub5.Update()
    GridDataset_sub5 = extractor_sub5.GetOutput()

    soilGrid = vtk.vtkStructuredGrid()
    soilGrid.CopyStructure(GridDataset_sub5)
    soilVtkArray = GridDataset_sub5.GetPointData().GetArray("rhof_1")
    soilGrid.GetPointData().SetScalars(soilVtkArray)

    ### =================  resample to image & extract attributes  =================
    resampler = vtk.vtkResampleToImage()
    resampler.AddInputDataObject(grid_dataset)
    resampler.SetSamplingDimensions(resampledPointsDims)  ### set for #points
    resampler.SetSamplingBounds(bounds)
    resampler.Update()
    ImageData = resampler.GetOutput()

    ### =================  extract attributes  =================
    thetaVtkArray = ImageData.GetPointData().GetArray("theta")
    vaporVtkArray = ImageData.GetPointData().GetArray("rhowatervapor")


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

    # ### =================  vorticity field  =================
    cellDerivative = vtk.vtkCellDerivatives()
    cellDerivative.SetInputConnection(calcCompose.GetOutputPort())
    cellDerivative.SetInputArrayToProcess(0, 0, 0, vtk.VTK_SCALAR_MODE_USE_POINT_DATA, "wind_velocity")
    cellDerivative.SetVectorModeToComputeVorticity()
    cellDerivative.SetTensorModeToPassTensors()
    cellDerivative.Update()

    pointDerivative = vtk.vtkCellDataToPointData()
    pointDerivative.SetInputConnection(cellDerivative.GetOutputPort())
    pointDerivative.SetInputArrayToProcess(0, 0, 0, vtk.VTK_SCALAR_MODE_USE_CELL_DATA, "Vorticity")
    pointDerivative.SetProcessAllArrays(True)
    pointDerivative.Update()
    vortPointImage = pointDerivative.GetOutput()

    vortNP = vtk_to_numpy(vortPointImage.GetPointData().GetArray("Vorticity"))
    vortMagNP = np.linalg.norm(vortNP, ord=2, axis=1)
    vortMagNP_3d = vortMagNP.reshape(resampledPointsDims)
    vortMagNP_3d[-5:, :, :] = int(0)    ### indexing in z, y, x order
    vortVtkArray = numpy_to_vtk(vortMagNP_3d.reshape(-1))
    vortVtkArray.SetName("vortMag")
    vortImage = vtkArray2vtkImageData(vortVtkArray, resampledOrigin, resampledPointsDims, resampledCellSpacing)

    temp["extent"] = extent
    temp["resampledOrigin"] = resampledOrigin
    temp["resampledPointsDims"] = resampledPointsDims
    temp["resampledCellSpacing"] = resampledCellSpacing
    temp["grassPointsDims"] = grassPointsDims
    temp["grassCellSpacing"] = grassCellSpacing
    temp["soil"] = soilVtkArray
    temp["grass"] = grassVtkArray
    temp["theta"] = thetaVtkArray
    temp["vapor"] = vaporVtkArray
    temp["windVelocityMag"] = windVelMagVtkArray
    temp["windVelocity"] = windVelocityVtkArray
    temp["vorticity"] = vortVtkArray

    return temp

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--datadir', type=str, default='dataset/mountain_backcurve40',
                        help='Path to the dataset')
    args = parser.parse_args()
    datasetDir = args.datadir
    _file_list = os.listdir(datasetDir)
    if not os.path.exists(os.path.join(datasetDir, "preprocessed")):
        os.mkdir(os.path.join(datasetDir, "preprocessed"))
    for i, grid_file in enumerate(_file_list):
        if not grid_file.endswith(".vts"):
            _file_list.pop(i)
    grid_file_list = sorted(_file_list, key=lambda s: int(s.split('.')[1]))
    

    for i, grid_file in enumerate(grid_file_list):
        grid_file_path = os.path.join(datasetDir, grid_file)
        
        npz_file_name = os.path.join(datasetDir, "preprocessed", "output.{0}.npz".format(int(1000*(i+1))))
        if os.path.exists(npz_file_name):
            print("> {0:<20s} already exists.".format(npz_file_name))
        else:
            preprocessed = preprocess(grid_file_path)
            np.savez(npz_file_name, **preprocessed)
            print("> {0:<20s} saved".format(npz_file_name))

    
    
if __name__ == "__main__":
    main()
