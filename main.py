import argparse
import os
import numpy as np

import vtk
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera

from callbacks import vtkSliderCallback, vtkButtonCallback
from render import renderVolume,renderStreamline, renderSurface
import gui

def main(datadir):
    # ---------- load data --------------------
    dataset = np.load(os.path.join(datadir, 'preprocessed/output.1000.npz'))

    # ----------- Global Variables ------------
    extent = dataset["extent"]
    resampledOrigin = dataset['resampledOrigin']
    resampledPointsDims = dataset["resampledPointsDims"]
    resampledCellSpacing = dataset["resampledCellSpacing"]
    grassPointsDims = dataset["grassPointsDims"]
    grassCellSpacing = dataset["grassCellSpacing"]

    # ---------  renderer and window interactor -------------
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.SetSize(1920, 1080)

    renderer = vtk.vtkRenderer()
    renderer.SetViewport(0, 0, 1.0, 1.0)
    renderer.SetBackground(0, 0, 0)

    # --------------- setup visualization -----------------------
    grassImage, _ = renderVolume(renderer, dataset, 'grass', resampledOrigin, grassPointsDims, grassCellSpacing)
    thetaImage, _ = renderVolume(renderer, dataset, 'theta', resampledOrigin, resampledPointsDims, resampledCellSpacing)
    vaporImage, _ = renderVolume(renderer, dataset, 'vapor', resampledOrigin, resampledPointsDims, resampledCellSpacing)
    vortImage, vortActor = renderVolume(renderer, dataset, 'vorticity', resampledOrigin, resampledPointsDims, resampledCellSpacing)
    renderer.RemoveActor(vortActor) # default init without vorticity

    # --------------- soil --------------------
    # TODO: another way to avoid this preprocess
    rawDataset = vtk.vtkXMLStructuredGridReader()
    rawDataset.SetFileName('dataset/mountain_backcurve40/output.40000.vts')
    rawDataset.Update()

    extractor = vtk.vtkExtractGrid()
    extractor.SetInputConnection(rawDataset.GetOutputPort())
    extractor.SetVOI(extent[0], extent[1], extent[2], extent[3], 0, 5)
    extractor.Update()
    soilSurface = renderSurface(renderer, extractor.GetOutput(), dataset, 'soil')
    windVelocityImage, streamlineActors = \
        renderStreamline(dataset, resampledOrigin, resampledPointsDims, resampledCellSpacing)

    renderWindow.AddRenderer(renderer)
    renderWindowInteractor = vtk.vtkRenderWindowInteractor()
    renderWindowInteractor.SetInteractorStyle(vtkInteractorStyleTrackballCamera())
    renderWindowInteractor.SetRenderWindow(renderWindow)

    # -------------- GUI -----------------------------
    streamlineButton = vtk.vtkButtonWidget()
    vorticityButton = vtk.vtkButtonWidget()
    sliderWidget = vtk.vtkSliderWidget()
    gui.setup(renderer, 
              {'vorticity': vorticityButton, 'streamline': streamlineButton}, 
              sliderWidget, renderWindowInteractor)

    # ------------------- callbacks --------------------
    streamlineCallback = vtkButtonCallback(renderer=renderer, actors=streamlineActors, dataset=dataset,
                                       watchDict={'windVelocityMag': windVelocityImage,
                                                  'windVelocity': windVelocityImage})
    streamlineButton.AddObserver("StateChangedEvent", streamlineCallback)
    vorticityCallback = vtkButtonCallback(renderer=renderer, actors=[vortActor], dataset=dataset,
                                          watchDict={'vorticity': vortImage})
    vorticityButton.AddObserver("StateChangedEvent", vorticityCallback)
    callbackSlider = vtkSliderCallback(datadir, buttonCallbacks=[streamlineCallback, vorticityCallback], dataset=dataset,
                                       watchDict={'theta': thetaImage, 'grass': grassImage, 
                                                  'vapor': vaporImage, 'soil': soilSurface,
                                                  'windVelocityMag': windVelocityImage,
                                                  'windVelocity': windVelocityImage,
                                                  'vorticity': vortImage})
    sliderWidget.AddObserver('InteractionEvent', callbackSlider)
    sliderWidget.EnabledOn()

    # ------------- rendering loop --------------
    renderWindow.Render()
    renderWindow.SetWindowName('Wildfire B')
    renderWindowInteractor.Start()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--datadir', type=str, default='dataset/mountain_backcurve40',
                        help='Path to the dataset')
    args = parser.parse_args()
    datadir = args.datadir

    # TODO: option to select dataset to load 
    main(datadir)