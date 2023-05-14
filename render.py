import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk

import colormap

def renderVolume(renderer, dataset, name, origin, dimensions, spacing):
    vtkArray = numpy_to_vtk(dataset[name])
    image = vtk.vtkImageData()
    image.SetOrigin(origin)
    image.SetDimensions(dimensions)
    image.SetSpacing(spacing)
    image.GetPointData().SetScalars(vtkArray)

    volumeMapper = vtk.vtkSmartVolumeMapper()
    volumeMapper.SetInputData(image)
    volumeMapper.Update()

    actor = vtk.vtkVolume()
    actor.SetMapper(volumeMapper)
    actor.SetProperty(colormap.properties[name])

    renderer.AddActor(actor)

    return image, actor

def renderStreamline(dataset, origin, dimensions, spacing):
    windVelocityImage = vtk.vtkImageData()
    windVelocityImage.SetOrigin(origin)
    windVelocityImage.SetDimensions(dimensions)
    windVelocityImage.SetSpacing(spacing)
    windVelMagVtkArray = numpy_to_vtk(dataset['windVelocityMag'])
    windVelMagVtkArray.SetName("wind_velocity_mag")
    windVelocityImage.GetPointData().SetScalars(windVelMagVtkArray)
    windVelocityVtkArray = numpy_to_vtk(dataset['windVelocity'])
    windVelocityVtkArray.SetName("wind_velocity")
    windVelocityImage.GetPointData().SetVectors(windVelocityVtkArray)
    lineSeed = vtk.vtkLineSource()
    lineSeed.SetPoint1(3.15, -750, 222)
    lineSeed.SetPoint2(3.15, 750, 222)
    lineSeed.SetResolution(300)
    lineSeed.Update()
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

    streamlinesMapper = vtk.vtkPolyDataMapper()
    streamlinesMapper.SetInputConnection(streamTracer.GetOutputPort())
    streamlinesMapper.SetLookupTable(colormap.streamLookupTable)
    streamlinesMapper.SetScalarRange(0, 27)
    streamlinesMapper.Update()

    streamlinesActor = vtk.vtkActor()
    streamlinesActor.SetMapper(streamlinesMapper)
    streamlinesActor.GetProperty().SetRepresentationToSurface()
    streamlinesActor.GetProperty().SetLineWidth(1)
    streamlinesActor.GetProperty().SetPointSize(1)
    streamlinesActor.GetProperty().SetOpacity(1)

    windMagLegend = vtk.vtkScalarBarActor()
    windMagLegend.SetLookupTable(colormap.streamLookupTable)
    windMagLegend.SetNumberOfLabels(2)
    windMagLegend.SetTitle('Wind Mag.')
    windMagLegend.SetVerticalTitleSeparation(6)
    windMagLegend.GetPositionCoordinate().SetValue(0.95, 0.1)
    windMagLegend.SetWidth(0.03)
    windMagLegend.SetHeight(0.3)

    return windVelocityImage, [streamlinesActor, windMagLegend]

def renderSurface(renderer, rawDataset, dataset, name):
    vtkArray = numpy_to_vtk(dataset[name])
    grid = vtk.vtkStructuredGrid()
    grid.CopyStructure(rawDataset)
    grid.GetPointData().SetScalars(vtkArray)
    
    surfaceMapper = vtk.vtkDataSetMapper()
    surfaceMapper.SetInputData(grid)
    surfaceMapper.SetLookupTable(colormap.properties[name])
    surfaceMapper.Update()

    actor = vtk.vtkActor()
    actor.SetMapper(surfaceMapper)
    actor.GetProperty().SetRepresentationToSurface()

    renderer.AddActor(actor)

    return grid