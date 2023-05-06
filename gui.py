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

def setupStreamlineButton(renderer, buttonWidget, renderWindowInteractor):
    green = [145, 207, 96]
    gray = [153, 153, 153]
    image1 = vtk.vtkImageData()
    image2 = vtk.vtkImageData()
    createImage(image1, green, gray)
    createImage(image2, gray, green)

    buttonRepresentation = vtk.vtkTexturedButtonRepresentation2D()
    buttonRepresentation.SetNumberOfStates(2)
    buttonRepresentation.SetButtonTexture(0, image1)
    buttonRepresentation.SetButtonTexture(1, image2)

    buttonWidget.SetInteractor(renderWindowInteractor)
    buttonWidget.SetRepresentation(buttonRepresentation)

    upperLeft = vtk.vtkCoordinate()
    upperLeft.SetCoordinateSystemToNormalizedDisplay()
    upperLeft.SetValue(0, 1.0)

    bds = [0] * 6
    sz = 50.0
    bds[0] = upperLeft.GetComputedDisplayValue(renderer)[0] - sz
    bds[1] = bds[0] + sz
    bds[2] = upperLeft.GetComputedDisplayValue(renderer)[1] - sz
    bds[3] = bds[2] + sz
    bds[4] = bds[5] = 0.0

    buttonRepresentation.SetPlaceFactor(1)
    buttonRepresentation.PlaceWidget(bds)
    buttonRepresentation.SetState(0)
    buttonWidget.On()

def setupTimeSlider(sliderWidget, renderWindowInteractor):
    sliderRep = vtk.vtkSliderRepresentation2D()
    sliderRep.SetMinimumValue(1)
    sliderRep.SetMaximumValue(15)
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

def setup(renderer, buttonWidget, sliderWidget, renderWindowInteractor):
    setupLegends(renderer)
    setupStreamlineButton(renderer, buttonWidget, renderWindowInteractor)
    setupTimeSlider(sliderWidget, renderWindowInteractor)