import argparse
import os
import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk

from utils import vtkArray2vtkImageData

def preProcess(filename):
    datasetReader = vtk.vtkXMLStructuredGridReader()
    datasetReader.SetFileName(filename)
    datasetReader.Update()
    dataset = datasetReader.GetOutput()

    # ----------- Global Variables ------------
    bounds = np.array(dataset.GetBounds()) 
    extent = np.array(dataset.GetExtent())
    resampledOrigin = bounds[::2]
    resampledPointsDims = np.array([300, 250, 150], dtype=int)
    resampledCellsDims = resampledPointsDims - 1
    resampledCellSpacing = (bounds[1::2] - bounds[:-1:2]) / resampledCellsDims

    # ----------- grass -----------------------
    extractorGrass = vtk.vtkExtractGrid()
    extractorGrass.SetInputData(dataset)
    extractorGrass.SetVOI(extent[0], extent[1], extent[2], extent[3], 0, 10)
    extractorGrass.Update()
    datasetGrass = extractorGrass.GetOutput()    
    grassBounds = np.array(datasetGrass.GetBounds())
    grassPointsDims = np.array([300, 250, 200], dtype=int)
    grassCellsDims = grassPointsDims - 1
    grassCellSpacing = (grassBounds[1::2] - grassBounds[:-1:2]) / grassCellsDims
    resamplerGrass = vtk.vtkResampleToImage()
    resamplerGrass.AddInputDataObject(datasetGrass)
    resamplerGrass.SetSamplingDimensions(grassPointsDims)  ### set for #points
    resamplerGrass.SetSamplingBounds(bounds)
    resamplerGrass.Update()
    grassVtkArray = resamplerGrass.GetOutput().GetPointData().GetArray('rhof_1')
    grassImage = vtkArray2vtkImageData(grassVtkArray, resampledOrigin, grassPointsDims, grassCellSpacing)

    # -------------------- soil ------------------------
    extractorSoil = vtk.vtkExtractGrid()
    extractorSoil.SetInputData(dataset)
    extractorSoil.SetVOI(extent[0], extent[1], extent[2], extent[3], 0, 5)
    extractorSoil.Update()
    soilGrid = vtk.vtkStructuredGrid()
    soilGrid.CopyStructure(extractorSoil.GetOutput())
    soilVtkArray = extractorSoil.GetOutput().GetPointData().GetArray('rhof_1')
    soilGrid.GetPointData().SetScalars(soilVtkArray)

    # ------------------ resampler for other attributes -------------------
    resampler = vtk.vtkResampleToImage()
    resampler.AddInputDataObject(dataset)
    resampler.SetSamplingDimensions(resampledPointsDims)  ### set for #points
    resampler.SetSamplingBounds(bounds)
    resampler.Update()
    ImageData = resampler.GetOutput()

    # ----------------- theta -------------------------------------
    thetaVtkArray = ImageData.GetPointData().GetArray('theta')
    
    # ------------------ watervapor -----------------------------------
    vaporVtkArray = ImageData.GetPointData().GetArray('rhowatervapor')

    # ------------------ derived wind properties ------------------ 
    # ------------------ velocity magnitude -----------------------
    calcMag = vtk.vtkArrayCalculator()
    calcMag.SetInputData(ImageData)
    calcMag.AddScalarVariable('u_var', 'u', 0)
    calcMag.AddScalarVariable('v_var', 'v', 0)
    calcMag.AddScalarVariable('w_var', 'w', 0)
    calcMag.SetResultArrayName('wind_velocity_mag')
    calcMag.SetFunction('sqrt(u_var^2+v_var^2+w_var^2)')
    calcMag.SetAttributeTypeToPointData()
    calcMag.Update()
    windVelMagVtkArray = calcMag.GetOutput().GetPointData().GetArray('wind_velocity_mag')

    # ------------------ velocity vector --------------------------
    calcCompose = vtk.vtkArrayCalculator()
    calcCompose.SetInputConnection(calcMag.GetOutputPort())
    calcCompose.AddScalarVariable('u_var', 'u', 0)
    calcCompose.AddScalarVariable('v_var', 'v', 0)
    calcCompose.AddScalarVariable('w_var', 'w', 0)
    calcCompose.SetResultArrayName('wind_velocity')
    calcCompose.SetFunction('u_var*iHat+v_var*jHat+w_var*kHat')
    calcCompose.SetAttributeTypeToPointData()
    calcCompose.Update()
    windVelocityVtkArray = calcCompose.GetOutput().GetPointData().GetArray('wind_velocity')

    # ------------------ vorticity --------------------------------
    cellDerivative = vtk.vtkCellDerivatives()
    cellDerivative.SetInputConnection(calcCompose.GetOutputPort())
    cellDerivative.SetInputArrayToProcess(0, 0, 0, vtk.VTK_SCALAR_MODE_USE_POINT_DATA, 'wind_velocity')
    cellDerivative.SetVectorModeToComputeVorticity()
    cellDerivative.SetTensorModeToPassTensors()
    cellDerivative.Update()
    pointDerivative = vtk.vtkCellDataToPointData()
    pointDerivative.SetInputConnection(cellDerivative.GetOutputPort())
    pointDerivative.SetInputArrayToProcess(0, 0, 0, vtk.VTK_SCALAR_MODE_USE_CELL_DATA, 'Vorticity')
    pointDerivative.SetProcessAllArrays(True)
    pointDerivative.Update()
    vortPointImage = pointDerivative.GetOutput()

    vortNP = vtk_to_numpy(vortPointImage.GetPointData().GetArray('Vorticity'))
    vortMagNP = np.linalg.norm(vortNP, ord=2, axis=1)
    vortMagNP_3d = vortMagNP.reshape(resampledPointsDims)
    vortMagNP_3d[-5:, :, :] = int(0)    ### indexing in z, y, x order
    vortVtkArray = numpy_to_vtk(vortMagNP_3d.reshape(-1))

    ret = {}
    ret['extent'] = extent
    ret['resampledOrigin'] = resampledOrigin
    ret['resampledPointsDims'] = resampledPointsDims
    ret['resampledCellSpacing'] = resampledCellSpacing
    ret['grassPointsDims'] = grassPointsDims
    ret['grassCellSpacing'] = grassCellSpacing
    ret['soil'] = soilVtkArray
    ret['grass'] = grassVtkArray
    ret['theta'] = thetaVtkArray
    ret['vapor'] = vaporVtkArray
    ret['windVelocityMag'] = windVelMagVtkArray
    ret['windVelocity'] = windVelocityVtkArray
    ret['vorticity'] = vortVtkArray

    return ret

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--datadir', type=str, default='dataset/mountain_backcurve40',
                        help='Path to the dataset')
    args = parser.parse_args()
    datadir = args.datadir
    datalist = sorted(os.listdir(datadir))
    print(f'Preprocessing {datadir} dataset......')
    for file in datalist:
        if not 'vts' in file:
            continue
        print(file)
        name = file[:-4]
        processed = preProcess(os.path.join(datadir, file))
        os.makedirs(os.path.join(datadir, 'preprocessed'), exist_ok=True)
        np.savez(os.path.join(datadir, 'preprocessed', f'{name}.npz'), **processed)