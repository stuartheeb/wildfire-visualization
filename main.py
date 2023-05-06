import numpy as np

import vtk
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera

from callbacks import vtkSliderCallback, vtkButtonCallback
from render import renderVolume,renderStreamline
import gui

def main():
    # ---------- load data --------------------
    # TODO: take data dir as an argument
    datasetReader = vtk.vtkXMLImageDataReader()
    datasetReader.SetFileName('../paraview/data/output.01000.vti')
    datasetReader.Update()
    dataset = datasetReader.GetOutput()

    # ----------- Global Variables ------------
    bounds = np.array(dataset.GetBounds()) 
    resampledOrigin = bounds[::2]
    resampledPointsDims = np.array([300, 250, 150], dtype=int)
    resampledCellsDims = resampledPointsDims - 1
    resampledCellSpacing = (bounds[1::2] - bounds[:-1:2]) / resampledCellsDims

    # ---------  renderer and window interactor -------------
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.SetSize(1920, 1080)

    renderer = vtk.vtkRenderer()
    renderer.SetViewport(0, 0, 1.0, 1.0)
    renderer.SetBackground(0, 0, 0)

    # --------------- setup visualization -----------------------
    grassImage = renderVolume(renderer, datasetReader, resampledOrigin, resampledPointsDims, resampledCellSpacing,
                              dataName='rhof_1', imageName='grass')
    thetaImage = renderVolume(renderer, datasetReader, resampledOrigin, resampledPointsDims, resampledCellSpacing,
                              dataName='theta', imageName='theta')
    vaporImage = renderVolume(renderer, datasetReader, resampledOrigin, resampledPointsDims, resampledCellSpacing,
                              dataName='rhowatervapor', imageName='vapor')
    calcMag, calcVec, windVelocityImage, streamlineActors = \
        renderStreamline(renderer, datasetReader, resampledOrigin, resampledPointsDims, resampledCellSpacing)

    renderWindow.AddRenderer(renderer)
    renderWindowInteractor = vtk.vtkRenderWindowInteractor()
    renderWindowInteractor.SetInteractorStyle(vtkInteractorStyleTrackballCamera())
    renderWindowInteractor.SetRenderWindow(renderWindow)

    # -------------- GUI -----------------------------
    buttonWidget = vtk.vtkButtonWidget()
    sliderWidget = vtk.vtkSliderWidget()
    gui.setup(renderer, buttonWidget, sliderWidget, renderWindowInteractor)

    # ------------------- callbacks --------------------
    callbackButton = vtkButtonCallback(renderer=renderer, actors=streamlineActors, 
                                       calcMag=calcMag, calcVec=calcVec, wind=windVelocityImage)
    buttonWidget.AddObserver("StateChangedEvent", callbackButton)
    callbackSlider = vtkSliderCallback(datasetReader, buttonWidget=buttonWidget,
                                 images={'theta': thetaImage, 'rhof_1': grassImage, 'rhowatervapor': vaporImage},
                                  calcMag=calcMag,
                                  calcVec=calcVec,
                                  wind=windVelocityImage)
    sliderWidget.AddObserver('InteractionEvent', callbackSlider)
    sliderWidget.EnabledOn()

    # ------------- rendering loop --------------
    renderWindow.Render()
    renderWindow.SetWindowName('Wildfire B')
    renderWindowInteractor.Start()


if __name__ == '__main__':
    main()