def updateWind(buttonWidget, calcMag, calcVec, wind):
    state = buttonWidget.GetSliderRepresentation().GetState()
    if state == 0:
        return
    calcMag.Update()
    calcVec.Update()
    windVelMagVtkArray = calcMag.GetOutput().GetPointData().GetArray("wind_velocity_mag")
    wind.GetPointData().SetScalars(windVelMagVtkArray)
    windVelocityVtkArray = calcVec.GetOutput().GetPointData().GetArray('wind_velocity')
    wind.GetPointData().SetVectors(windVelocityVtkArray)


class vtkSliderCallback(object):
    def __init__(self, datasetReader, buttonWidget, images, calcMag, calcVec, wind):
        self.datasetReader = datasetReader
        self.buttonWidget = buttonWidget
        self.images = images
        self.calcMag = calcMag
        self.calcVec = calcVec
        self.wind = wind

    def __call__(self, sliderWidget, eventId):
        time = sliderWidget.GetRepresentation().GetValue()
        self.updateFrame(time)
    
    def updateFrame(self, time):
        filename = f'../paraview/data/output.{int(time):02d}000.vti'
        self.datasetReader.SetFileName(filename)
        self.datasetReader.Update()
        for k, img in self.images.items():
            scalars = self.datasetReader.GetOutput().GetPointData().GetArray(k)
            img.GetPointData().SetScalars(scalars)
        updateWind(self.buttonWidget, self.calcMag, self.calcVec, self.wind)

class vtkButtonCallback(object):
    def __init__(self, renderer, actors, calcMag, calcVec, wind):
        self.renderer = renderer
        self.actors = actors
        self.calcMag = calcMag
        self.calcVec = calcVec
        self.wind = wind

    def __call__(self, buttonWidget, eventId):
        state = buttonWidget.GetSliderRepresentation().GetState()
        if state == 0:
            for actor in self.actors:
                self.renderer.RemoveActor(actor)
        else:
            updateWind(buttonWidget, self.calcMag, self.calcVec, self.wind)
            for actor in self.actors:
                self.renderer.AddActor(actor)
