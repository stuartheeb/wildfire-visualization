import vtk
import colormap

def renderVolume(renderer, datasetReader, origin, dimensions, spacing, dataName, imageName):
    image = vtk.vtkImageData()
    image.SetOrigin(origin)
    image.SetDimensions(dimensions)
    image.SetSpacing(spacing)
    image.GetPointData().SetScalars(datasetReader.GetOutput().GetPointData().GetArray(dataName))

    volumeMapper = vtk.vtkSmartVolumeMapper()
    volumeMapper.SetInputData(image)
    volumeMapper.Update()

    actor = vtk.vtkVolume()
    actor.SetMapper(volumeMapper)
    actor.SetProperty(colormap.volumePropertiess[imageName])

    renderer.AddActor(actor)

    return image

def renderStreamline(renderer, datasetReader, origin, dimensions, spacing):
    # TODO: move the computation below to preprocess
    calcMag = vtk.vtkArrayCalculator()
    calcMag.SetInputConnection(datasetReader.GetOutputPort())
    calcMag.AddScalarVariable("u_var", "u", 0)
    calcMag.AddScalarVariable("v_var", "v", 0)
    calcMag.AddScalarVariable("w_var", "w", 0)
    calcMag.SetResultArrayName("wind_velocity_mag")
    calcMag.SetFunction("sqrt(u_var^2+v_var^2+w_var^2)")
    calcMag.SetAttributeTypeToPointData()
    calcMag.Update()

    calcVec = vtk.vtkArrayCalculator()
    calcVec.SetInputConnection(datasetReader.GetOutputPort())
    calcVec.AddScalarVariable("u_var", "u", 0)
    calcVec.AddScalarVariable("v_var", "v", 0)
    calcVec.AddScalarVariable("w_var", "w", 0)
    calcVec.SetResultArrayName('wind_velocity')
    calcVec.SetFunction('u_var*iHat+v_var*jHat+w_var*kHat')
    calcVec.SetAttributeTypeToPointData()
    calcVec.Update()

    windVelocityImage = vtk.vtkImageData()
    windVelocityImage.SetOrigin(origin)
    windVelocityImage.SetDimensions(dimensions)
    windVelocityImage.SetSpacing(spacing)
    windVelMagVtkArray = calcMag.GetOutput().GetPointData().GetArray("wind_velocity_mag")
    windVelocityImage.GetPointData().SetScalars(windVelMagVtkArray)
    windVelocityVtkArray = calcVec.GetOutput().GetPointData().GetArray('wind_velocity')
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

    return calcMag, calcVec, windVelocityImage, [streamlinesActor, windMagLegend]
