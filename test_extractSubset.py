'''
4.30
load 1 frame .vts
vtkStructuredGRid -> vtkResampleToImage -> extract attribute vtkArray & convert to ImageData
extract attributes
volume rendering on fire and watervapor
add legend bar
load predefined colormap
fix camera pos
'''
import os
from pathlib import Path
import vtk
import numpy as np
colors = vtk.vtkNamedColors()
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
from scipy.interpolate import interp1d, interp2d
import colormap

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

def main():
    print("[WildFireB]")
    ### =================  IO  =================
    grid_file_name = "dataset\\mountain_backcurve40\\output.40000.vts"
    grid_datasetReader = vtk.vtkXMLStructuredGridReader()
    grid_datasetReader.SetFileName(grid_file_name)
    grid_datasetReader.Update()
    grid_dataset = grid_datasetReader.GetOutput()
    # print(grid_dataset)


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
    grassImage = vtk.vtkImageData()
    grassImage.SetOrigin(resampledOrigin)
    grassImage.SetDimensions(grassPointsDims)    ### set for #points
    grassImage.SetSpacing(grassCellSpacing)   ### for #cells
    grassImage.GetPointData().SetScalars(grassVtkArray)
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
    thetaImage = vtk.vtkImageData()
    thetaImage.SetOrigin(resampledOrigin)
    thetaImage.SetDimensions(resampledPointsDims)    ### set for #points
    thetaImage.SetSpacing(resampledCellSpacing)   ### for #cells
    thetaImage.GetPointData().SetScalars(thetaVtkArray)
    print("thetaImage:", thetaImage.GetScalarRange())

    vaporVtkArray = ImageData.GetPointData().GetArray("rhowatervapor")
    vaporImage = vtk.vtkImageData()
    vaporImage.DeepCopy(thetaImage)
    vaporImage.GetPointData().SetScalars(vaporVtkArray)
    print("vaporImage:", vaporImage.GetScalarRange())


    ### =================  mapper  =================
    ### one mapper for each volume
    ### All mappers work, but vtkGPUVolumeRayCastMapper seems faster for interacting?
    # theta_volume_mapper = vtk.vtkFixedPointVolumeRayCastMapper()
    # theta_volume_mapper = vtk.vtkGPUVolumeRayCastMapper()
    thetaVolumeMapper = vtk.vtkSmartVolumeMapper()
    thetaVolumeMapper.SetInputData(thetaImage)
    thetaVolumeMapper.Update()

    vaporVolumeMapper = vtk.vtkSmartVolumeMapper()
    vaporVolumeMapper.SetInputData(vaporImage)
    vaporVolumeMapper.Update()

    grassVolumeMapper = vtk.vtkSmartVolumeMapper()
    grassVolumeMapper.SetInputData(grassImage)
    grassVolumeMapper.Update()

    soilSurfaceMapper = vtk.vtkDataSetMapper()
    soilSurfaceMapper.SetInputData(soilGrid)
    soilSurfaceMapper.SetLookupTable(colormap.soilLookupTable)
    soilSurfaceMapper.Update()


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


    ### =================  legend  =================
    thetaLegend = vtk.vtkScalarBarActor()
    thetaLegend.SetLookupTable(colormap.thetaColormap)
    thetaLegend.SetNumberOfLabels(3)
    thetaLegend.SetTitle("theta")
    thetaLegend.SetVerticalTitleSeparation(6)
    thetaLegend.GetPositionCoordinate().SetValue(0.9, 0.1)
    thetaLegend.SetWidth(0.05)


    ### =================  renderer  =================
    ### reversely ordered in occulusion relationship
    renderer = vtk.vtkRenderer()
    renderer.AddActor(grassVolumeActor)
    renderer.AddActor(soilSurfaceActor)
    renderer.AddActor(thetaVolumeActor)
    renderer.AddActor(thetaLegend)
    renderer.AddActor(vaporVolumeActor)

    ### set default camera
    renderer.SetBackground(82.0/255, 87.0/255, 110.0/255)
    camera = renderer.GetActiveCamera()
    camera.SetPosition(1083.2227304747453, -1641.2222349367626, 2619.057849876556)
    camera.SetFocalPoint(282.39377692021907, -204.98942274883282, 263.6253663432378)
    camera.SetViewUp(-0.37040966573044387, 0.7317561916543173, 0.5721272196889701)
    camera.SetViewAngle(30)
    camera.SetEyeAngle(2)
    camera.SetFocalDisk(1)
    camera.SetFocalDistance(0)
    camera.Roll(0.0)
    camera.Elevation(0.0)
    camera.Azimuth(0.0)
    camera.SetClippingRange(0.1, 100)
    renderer.SetActiveCamera(camera)

    renWin = vtk.vtkRenderWindow()
    renWin.AddRenderer(renderer)
    renWin.SetWindowName("test")
    renWin.SetSize(1920, 1080)

    renWinInteractor = vtk.vtkRenderWindowInteractor()
    renWinInteractor.SetInteractorStyle(MyInteractorStyle())
    renWinInteractor.SetRenderWindow(renWin)
    renWinInteractor.Initialize()
    renWinInteractor.Start()

if __name__ == "__main__":
    main()
