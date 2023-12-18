'''
5.8
load 1 frame .vts
vtkStructuredGRid -> vtkResampleToImage -> extract attribute vtkArray & convert to ImageData
extract attributes
volume rendering on fire and watervapor
compose wind velocity
show vorticity
add legend bar
load predefined colormap
fix camera pos
fix blank window bug
'''
import os
import vtk
import numpy as np
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
import colormap
from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk

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
    print("GetViewUp: ", camera.GetViewUp())

def main():
    print("[WildFireB]")
    ### =================  IO  =================
    # grid_file_name = "dataset\\mountain_backcurve40\\output.40000.vts"
    grid_file_name = "dataset\\mountain_backcurve320\\output.40000.vts"
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
    grassImage = vtkArray2vtkImageData(grassVtkArray, resampledOrigin, grassPointsDims, grassCellSpacing)
    print("grassImage:", grassImage.GetScalarRange())

    ### extract soil  
    extractor_sub5 = vtk.vtkExtractGrid()
    extractor_sub5.SetInputData(grid_dataset)
    extractor_sub5.SetVOI(extent[0], extent[1], extent[2], extent[3], 0, 5)
    extractor_sub5.Update()
    GridDataset_sub5 = extractor_sub5.GetOutput()

    soilGrid = vtk.vtkStructuredGrid()
    soilGrid.CopyStructure(GridDataset_sub5)
    soilGrid.GetPointData().SetScalars(GridDataset_sub5.GetPointData().GetArray("rhof_1"))
    print("soilGrid:", soilGrid.GetScalarRange())


    ### =================  resample to image & extract attributes  =================
    ### vtkResampleToImage
    resampler = vtk.vtkResampleToImage()
    resampler.AddInputDataObject(grid_dataset)
    resampler.SetSamplingDimensions(resampledPointsDims)  ### set for #points
    resampler.SetSamplingBounds(bounds)
    resampler.Update()
    ImageData = resampler.GetOutput()
    
    thetaVtkArray = ImageData.GetPointData().GetArray("theta")
    thetaImage = vtkArray2vtkImageData(thetaVtkArray, resampledOrigin, resampledPointsDims, resampledCellSpacing)
    print("thetaImage:", thetaImage.GetScalarRange())

    vaporVtkArray = ImageData.GetPointData().GetArray("rhowatervapor")
    vaporImage = vtk.vtkImageData()
    vaporImage.DeepCopy(thetaImage)
    vaporImage.GetPointData().SetScalars(vaporVtkArray)
    print("vaporImage:", vaporImage.GetScalarRange())


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

    ### create an image data containing both scalars and magtitude
    ### NOTE: must set both magnitude and velocity field
    windVelocityImage = vtkArray2vtkImageData(windVelMagVtkArray, resampledOrigin, 
                                              resampledPointsDims, resampledCellSpacing)
    windVelocityImage.GetPointData().SetVectors(windVelocityVtkArray)
    print("windVelocityVtkArray:", windVelocityVtkArray.GetRange())
    print("windVelocityImage:", windVelocityImage.GetScalarRange())
    
    # line seed
    lineSeed = vtk.vtkLineSource()
    lineSeed.SetPoint1(3.15, -750, 222)
    lineSeed.SetPoint2(3.15, 750, 222)
    lineSeed.SetResolution(300)
    lineSeed.Update()
    # streamline tracer
    streamTracer = vtk.vtkStreamTracer()
    streamTracer.SetSourceConnection(lineSeed.GetOutputPort())
    streamTracer.SetInputData(windVelocityImage)
    streamTracer.SetIntegrator(vtk.vtkRungeKutta4())
    streamTracer.SetIntegrationDirectionToBoth()
    streamTracer.SetMaximumPropagation(2000)
    streamTracer.SetInitialIntegrationStep(0.1)
    streamTracer.SetMinimumIntegrationStep(0.05)
    streamTracer.SetMaximumIntegrationStep(0.5)
    streamTracer.SetMaximumError(1e-6)
    streamTracer.SetMaximumNumberOfSteps(3000)
    streamTracer.SetTerminalSpeed(1e-13)
    streamTracer.Update()


    ### =================  vorticity field  =================
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
    vortImage = vtkArray2vtkImageData(vortVtkArray, resampledOrigin, 
                                      resampledPointsDims, resampledCellSpacing)
    

    ### =================  mapper  =================
    ### one mapper for each volume
    thetaVolumeMapper = vtk.vtkGPUVolumeRayCastMapper()
    thetaVolumeMapper.SetInputData(thetaImage)
    thetaVolumeMapper.Update()

    vaporVolumeMapper = vtk.vtkGPUVolumeRayCastMapper()
    vaporVolumeMapper.SetInputData(vaporImage)
    vaporVolumeMapper.Update()

    grassVolumeMapper = vtk.vtkGPUVolumeRayCastMapper()
    grassVolumeMapper.SetInputData(grassImage)
    grassVolumeMapper.Update()

    soilSurfaceMapper = vtk.vtkDataSetMapper()
    soilSurfaceMapper.SetInputData(soilGrid)
    soilSurfaceMapper.SetLookupTable(colormap.soilLookupTable)
    soilSurfaceMapper.Update()

    streamlinesMapper = vtk.vtkPolyDataMapper()
    streamlinesMapper.SetInputConnection(streamTracer.GetOutputPort())
    streamlinesMapper.SetLookupTable(colormap.streamLookupTable)
    streamlinesMapper.SetScalarRange(0, 27)
    streamlinesMapper.Update()
    
    vortVolumeMapper = vtk.vtkGPUVolumeRayCastMapper()
    vortVolumeMapper.SetInputData(vortImage)
    vortVolumeMapper.Update()


    ### =================  actor  =================
    ### one actor for each volume
    thetaVolumeActor = vtk.vtkVolume()
    thetaVolumeActor.SetMapper(thetaVolumeMapper)
    thetaVolumeActor.SetProperty(colormap.thetaVolumeProperty)
    
    vaporVolumeActor = vtk.vtkVolume()
    vaporVolumeActor.SetMapper(vaporVolumeMapper)
    vaporVolumeActor.SetProperty(colormap.vaporVolumeProperty)
    
    grassVolumeActor = vtk.vtkVolume()
    grassVolumeActor.SetMapper(grassVolumeMapper)
    grassVolumeActor.SetProperty(colormap.grassVolumeProperty)
    
    soilSurfaceActor = vtk.vtkActor()
    soilSurfaceActor.SetMapper(soilSurfaceMapper)
    soilSurfaceActor.GetProperty().SetRepresentationToSurface()
    
    streamlinesActor = vtk.vtkActor()
    streamlinesActor.SetMapper(streamlinesMapper)
    streamlinesActor.GetProperty().SetRepresentationToSurface()
    streamlinesActor.GetProperty().SetLineWidth(1)
    streamlinesActor.GetProperty().SetPointSize(1)
    streamlinesActor.GetProperty().SetOpacity(1)

    vortVolumeActor = vtk.vtkVolume()
    vortVolumeActor.SetMapper(vortVolumeMapper)
    vortVolumeActor.SetProperty(colormap.vorticityVolumeProperty)


    ### =================  legend  =================
    thetaLegend = vtk.vtkScalarBarActor()
    thetaLegend.SetLookupTable(colormap.thetaColormap)
    thetaLegend.SetNumberOfLabels(2)
    thetaLegend.SetTitle("theta")
    thetaLegend.SetVerticalTitleSeparation(6)
    thetaLegend.GetPositionCoordinate().SetValue(0.95, 0.5)
    thetaLegend.SetWidth(0.03)
    thetaLegend.SetHeight(0.3)
    
    windMagLegend = vtk.vtkScalarBarActor()
    windMagLegend.SetLookupTable(colormap.streamLookupTable)
    windMagLegend.SetNumberOfLabels(2)
    windMagLegend.SetTitle("Wind Mag.")
    windMagLegend.SetVerticalTitleSeparation(6)
    windMagLegend.GetPositionCoordinate().SetValue(0.95, 0.1)
    windMagLegend.SetWidth(0.03)
    windMagLegend.SetHeight(0.3)
    
    vortMagLegend = vtk.vtkScalarBarActor()
    vortMagLegend.SetLookupTable(colormap.vorticityColormap)
    vortMagLegend.SetNumberOfLabels(2)
    vortMagLegend.SetTitle("Vorticity Mag.")
    vortMagLegend.SetVerticalTitleSeparation(6)
    vortMagLegend.GetPositionCoordinate().SetValue(0.95, 0.1)
    vortMagLegend.SetWidth(0.03)
    vortMagLegend.SetHeight(0.3)


    ### =================  renderer  =================
    renderer = vtk.vtkRenderer()

    # ### Sol1: reversely ordered in occulusion relationship
    # renderer.AddActor(grassVolumeActor)
    # # renderer.AddActor(soilSurfaceActor)
    # renderer.AddActor(thetaVolumeActor)
    # # renderer.AddActor(thetaLegend)
    # # renderer.AddActor(vaporVolumeActor)
    # # renderer.AddActor(streamlinesActor)
    # # renderer.AddActor(windMagLegend)
    # # renderer.AddActor(vortMagLegend)
    # # renderer.AddActor(vortVolumeActor)
    # renderer.ResetCamera()


    ### Sol2: vtkMultiVolume
    multiVolActor = vtk.vtkMultiVolume()
    multiVolMapper = vtk.vtkGPUVolumeRayCastMapper()
    multiVolActor.SetMapper(multiVolMapper)
    multiVolMapper.SetUseJittering(0)

    dataList = [grassImage, thetaImage, vaporImage, vortImage]
    volumeList = [grassVolumeActor, thetaVolumeActor, vaporVolumeActor, vortVolumeActor]
    for i in reversed(range(4)):
    # for i in range(4):
        multiVolMapper.SetInputDataObject(i, dataList[i])
        multiVolActor.SetVolume(volumeList[i], i)
    renderer.AddActor(soilSurfaceActor)
    renderer.AddActor(thetaLegend)
    renderer.AddVolume(multiVolActor)
    # renderer.AddActor(streamlinesActor)
    # renderer.AddActor(windMagLegend)
    renderer.AddActor(vortMagLegend)
    renderer.ResetCamera()

    ### set default camera
    renderer.SetBackground(82.0/255, 87.0/255, 110.0/255)
    camera = renderer.GetActiveCamera()
    # ### for backcurves
    if "backcurve" in grid_file_name:
        ### side view for presentation
        camera.SetPosition(-425.7190273550342, 15.820371796525059, -1676.8871868019382)
        camera.SetFocalPoint(108.61175642382888, -19.32402345626258, 210.68961333957043)
        camera.SetViewUp(-0.00983623968679208, -0.9998262966756408, -0.015831135925690028)
        
        # ### side view for presentation
        # camera.SetPosition(375.7255845388927, -2093.707490227028, 87.64975623746376)
        # camera.SetFocalPoint(187.2355013093441, -142.84245662076927, 178.6871146155854)
        # camera.SetViewUp(-0.007335728706120157, -0.04732035960055222, 0.9988528273232371)

        ### view for video
        camera.SetPosition(1387.6849356801695, -1506.2467098983288, 2556.8024005565303)
        camera.SetFocalPoint(310.6637708489459, -166.44588727049756, 255.25660385125215)
        camera.SetViewUp(-0.37040966573044387, 0.7317561916543173, 0.5721272196889701)
        camera.Zoom(1.3)
    ### for headcurves
    elif "headcurve" in grid_file_name:
        camera.SetPosition(-815.6233940186918, 1211.2377832946756, 1829.6086948523784)
        camera.SetFocalPoint(53.09335083347671, 39.05737530202661, -43.26816237979907)
        camera.SetViewUp(0.3549008855287047, -0.7095787673286341, 0.6087227073202688)
        camera.Zoom(1.0)
    else:
        raise ValueError("!!! Invalid grid_file_name: {}. Please use default datset name that contains either \"backcurve\" or \"headcurve\".".format(grid_file_name))
    ### general settings
    camera.SetClippingRange(1, 20000)   ### (0.01, 20k) will fail
    camera.SetThickness(20000)
    renderer.SetActiveCamera(camera)

    renWin = vtk.vtkRenderWindow()
    renWin.AddRenderer(renderer)
    renWin.SetWindowName("test")
    renWin.SetSize(1920, 1080)

    renWinInteractor = vtk.vtkRenderWindowInteractor()
    renWinInteractor.SetInteractorStyle(MyInteractorStyle())
    renWinInteractor.SetRenderWindow(renWin)
    renWinInteractor.AddObserver("InteractionEvent", observeCamera)
    renWinInteractor.Initialize()
    print("> Start:")
    renWinInteractor.Start()

if __name__ == "__main__":
    main()
