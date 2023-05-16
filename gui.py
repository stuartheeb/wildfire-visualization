import os

import vtk
import colormap
from utils import createImage

def setupLegends(renderer):
    thetaLegend = vtk.vtkScalarBarActor()
    thetaLegend.SetLookupTable(colormap.thetaColormap)
    thetaLegend.SetNumberOfLabels(2)
    thetaLegend.SetTitle('theta')
    thetaLegend.SetVerticalTitleSeparation(6)
    thetaLegend.GetPositionCoordinate().SetValue(0.95, 0.5)
    thetaLegend.SetWidth(0.03)
    thetaLegend.SetHeight(0.3)

    renderer.AddActor(thetaLegend)

def setupButton(name, location, renderer, buttonWidget, renderWindowInteractor):
    imageReaderOn = vtk.vtkPNGReader()
    imageReaderOn.SetFileName(os.path.join('assets', f'{name}On.png'))
    imageReaderOn.Update()
    imageReaderOff = vtk.vtkPNGReader()
    imageReaderOff.SetFileName(os.path.join('assets', f'{name}Off.png'))
    imageReaderOff.Update()

    buttonRepresentation = vtk.vtkTexturedButtonRepresentation2D()
    buttonRepresentation.SetNumberOfStates(2)
    buttonRepresentation.SetButtonTexture(0, imageReaderOff.GetOutput())
    buttonRepresentation.SetButtonTexture(1, imageReaderOn.GetOutput())

    buttonWidget.SetInteractor(renderWindowInteractor)
    buttonWidget.SetRepresentation(buttonRepresentation)

    upperLeft = vtk.vtkCoordinate()
    upperLeft.SetCoordinateSystemToNormalizedDisplay()
    upperLeft.SetValue(0, location)

    bds = [0] * 6
    sz = 200.0
    bds[0] = upperLeft.GetComputedDisplayValue(renderer)[0] - sz
    bds[1] = bds[0] + sz
    bds[2] = upperLeft.GetComputedDisplayValue(renderer)[1] - sz
    bds[3] = bds[2] + sz
    bds[4] = bds[5] = 0.0

    buttonRepresentation.SetPlaceFactor(1)
    buttonRepresentation.PlaceWidget(bds)
    buttonRepresentation.SetState(0)
    buttonWidget.On()

def setupTimeSlider(sliderWidget, num_frames, renderWindowInteractor):
    sliderRep = vtk.vtkSliderRepresentation2D()
    sliderRep.SetMinimumValue(1)
    sliderRep.SetMaximumValue(num_frames)
    sliderRep.SetValue(1)
    sliderRep.SetTitleText('Time')
    sliderRep.GetSliderProperty().SetColor(0.2, 0.2, 0.6)
    sliderRep.GetTitleProperty().SetColor(1, 1, 1)
    sliderRep.GetLabelProperty().SetColor(1, 1, 1)
    sliderRep.GetSelectedProperty().SetColor(0.4, 0.8, 0.4)
    sliderRep.GetTubeProperty().SetColor(0.7, 0.7, 0.7)
    sliderRep.GetCapProperty().SetColor(0.7, 0.7, 0.7)  
    sliderRep.GetPoint1Coordinate().SetCoordinateSystemToDisplay()
    sliderRep.GetPoint1Coordinate().SetValue(40, 70)
    sliderRep.GetPoint2Coordinate().SetCoordinateSystemToDisplay()
    sliderRep.GetPoint2Coordinate().SetValue(300, 70)
    sliderRep.SetEndCapWidth(0.025)
    sliderRep.SetLabelFormat('%2.0f')
    sliderWidget.SetInteractor(renderWindowInteractor)
    sliderWidget.SetRepresentation(sliderRep)
    sliderWidget.SetAnimationModeToAnimate()

def setup(renderer, buttons, sliderWidget, num_frames, renderWindowInteractor):
    setupLegends(renderer)
    setupTimeSlider(sliderWidget, num_frames, renderWindowInteractor)
    location = 0.8
    for name, button in buttons.items():
        setupButton(name, location, renderer, button, renderWindowInteractor)
        location += 0.1