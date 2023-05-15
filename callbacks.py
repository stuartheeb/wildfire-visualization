import os
import numpy as np

import vtk
from vtk.util.numpy_support import numpy_to_vtk

def updateFrame(watchDict, dataset, state=1):
    for name, item in watchDict.items():
        vtkArray = numpy_to_vtk(dataset[name])
        vtkArray.SetName(name)
        if state == 0 and 'wind' in name:
            continue
        if name != 'windVelocity':
            item.GetPointData().SetScalars(vtkArray)
        else:
            item.GetPointData().SetVectors(vtkArray)

class vtkSliderCallback(object):
    def __init__(self, datadir, buttonCallbacks, dataset, watchDict):
        self.buttonCallbacks = buttonCallbacks
        self.datadir = datadir
        self.dataset = dataset
        self.watchDict = watchDict

    def __call__(self, sliderWidget, eventId):
        time = sliderWidget.GetRepresentation().GetValue()
        filename = os.path.join(self.datadir, 'preprocessed', f'output.{int(time) * 1000}.npz')
        self.dataset = np.load(filename)
        for button in self.buttonCallbacks:
            button.dataset = self.dataset
        updateFrame(self.watchDict, self.dataset)
    
class vtkButtonCallback(object):
    def __init__(self, renderer, actors, dataset, watchDict):
        self.renderer = renderer
        self.actors = actors
        self.dataset = dataset
        self.watchDict = watchDict

    def __call__(self, buttonWidget, eventId):
        state = buttonWidget.GetSliderRepresentation().GetState()
        if state == 0:
            for actor in self.actors:
                self.renderer.RemoveActor(actor)
        else:
            updateFrame(self.watchDict, self.dataset, state)
            for actor in self.actors:
                self.renderer.AddActor(actor)
