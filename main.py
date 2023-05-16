import argparse
import os
import numpy as np

import vtk
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera

from callbacks import vtkSliderCallback, vtkButtonCallback, vtkTransferFunctionButtonCallback
from render import renderVolume, renderStreamline, renderSurface
import gui

from vtkEasyTransfer import vtkEasyTransfer

def main(datadir, num_frames):
    print("Loading " + str(datadir) + ", there are " + str(num_frames) + " frames to render")
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
    renderer.SetBackground(0.3, 0.3, 0.3)

    # --------------- setup visualization -----------------------
    grassImage, _ = renderVolume(renderer, dataset, 'grass', resampledOrigin, grassPointsDims, grassCellSpacing)
    thetaImage, _ = renderVolume(renderer, dataset, 'theta', resampledOrigin, resampledPointsDims, resampledCellSpacing)
    vaporImage, _ = renderVolume(renderer, dataset, 'vapor', resampledOrigin, resampledPointsDims, resampledCellSpacing)
    vortImage, vortActor = renderVolume(renderer, dataset, 'vorticity', resampledOrigin, resampledPointsDims, resampledCellSpacing)
    renderer.RemoveActor(vortActor) # default init without vorticity

    # --------------- soil --------------------
    # TODO: another way to avoid this preprocess
    rawDataset = vtk.vtkXMLStructuredGridReader()
    rawDataset.SetFileName(os.path.join(datadir, 'output.1000.vts'))
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


    # --------------- transfer function --------------------
    easyTransfer = vtkEasyTransfer()
    easyTransfer.SetColormapHeat()  # set initial color map
    easyTransfer.SetColorRange(0.28494199737906456, 3.1813182236022746)  # set the value range that is mapped to color
    easyTransfer.SetOpacityRange(0, 0.1525)  # set the value range that is mapped to opacity
    easyTransfer.RefreshImage()

    # assign transfer function to volume properties
    volumeProperty = vtk.vtkVolumeProperty()
    volumeProperty.SetColor(easyTransfer.GetColorTransferFunction())
    volumeProperty.SetScalarOpacity(easyTransfer.GetOpacityTransferFunction())

    # This transfer function is for vorticity
    vortActor.SetProperty(volumeProperty)

    transferRenderer = easyTransfer.GetRenderer()
    transferRenderer.SetViewport([0.8, 0.2, 1, 0.8])

    # -------------- GUI -----------------------------
    streamlineButton = vtk.vtkButtonWidget()
    vorticityButton = vtk.vtkButtonWidget()
    editTransferFunctionToggle = vtk.vtkButtonWidget()
    sliderWidget = vtk.vtkSliderWidget()
    gui.setup(renderer, 
              {'transfer': editTransferFunctionToggle, 'vorticity': vorticityButton, 'streamline': streamlineButton}, 
              sliderWidget, num_frames, renderWindowInteractor)

    # ------------------- callbacks --------------------
    streamlineCallback = vtkButtonCallback(renderer=renderer, actors=streamlineActors, dataset=dataset,
                                       watchDict={'windVelocityMag': windVelocityImage,
                                                  'windVelocity': windVelocityImage})
    streamlineButton.AddObserver("StateChangedEvent", streamlineCallback)

    vorticityCallback = vtkButtonCallback(renderer=renderer, actors=[vortActor], dataset=dataset,
                                          watchDict={'vorticity': vortImage})
    vorticityButton.AddObserver("StateChangedEvent", vorticityCallback)

    transferCallback = vtkTransferFunctionButtonCallback(renderWindow=renderWindow, transferRenderer=transferRenderer, renderWindowInteractor=renderWindowInteractor, interactor=vtkInteractorStyleTrackballCamera(), transferInteractor=easyTransfer)
    editTransferFunctionToggle.AddObserver("StateChangedEvent", transferCallback)

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

    if not os.path.exists(os.path.join(datadir, "preprocessed")):
        print("> Preprocessed files do not exist")
    else:
        _file_list = os.listdir(os.path.join(datadir, "preprocessed"))
        num_frames = 0
        for i, grid_file in enumerate(_file_list):
            if grid_file.endswith(".npz"):
                num_frames += 1
        if(num_frames == 0):
            print("> Preprocessed files do not exist")
        else:
            main(datadir, num_frames)