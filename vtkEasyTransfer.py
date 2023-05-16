import vtk


class vtkEasyTransferInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self):
        self.EasyTransfer = None
        self.MouseDown = False
        self.LastX = -1
        self.LastPlot = -1
        self.AddObserver("LeftButtonPressEvent", self.OnLeftButtonDown)
        self.AddObserver("LeftButtonReleaseEvent", self.OnLeftButtonUp)
        self.AddObserver("MouseMoveEvent", self.OnMouseMove)

    def SetEasyTransfer(self, easyTransfer):
        self.EasyTransfer = easyTransfer

    def OnLeftButtonDown(self, obj, event):
        clickPos = self.GetInteractor().GetEventPosition()
        self.MouseDown = True
        size = self.EasyTransfer.Renderer.GetRenderWindow().GetSize()
        windowRelative = [clickPos[0] / size[0], clickPos[1] / size[1]]
        viewport = self.EasyTransfer.Renderer.GetViewport()
        viewportRelative = [
            (windowRelative[0] - viewport[0]) / (viewport[2] - viewport[0]),
            (windowRelative[1] - viewport[1]) / (viewport[3] - viewport[1]),
        ]
        if (
            viewportRelative[0] >= 0
            and viewportRelative[0] <= 1
            and viewportRelative[1] >= 0
            and viewportRelative[1] <= 1
        ):
            # x = viewportRelative[0] * self.EasyTransfer.CanvasWidth
            self.LastX = -1
            yfull = int(viewportRelative[1] * (self.EasyTransfer.CanvasHeight * 4))
            plot = yfull // self.EasyTransfer.CanvasHeight
            self.LastPlot = plot
            self.processPixel(clickPos)
        else:
            self.LastPlot = -1
        super().OnLeftButtonDown()

    def OnLeftButtonUp(self, obj, event):
        self.MouseDown = False
        super().OnLeftButtonUp()

    def OnMouseMove(self, obj, event):
        if self.MouseDown:
            clickPos = self.GetInteractor().GetEventPosition()
            self.processPixel(clickPos)
        super().OnMouseMove()

    def processPixel(self, clickPos):
        size = self.EasyTransfer.Renderer.GetRenderWindow().GetSize()
        windowRelative = [clickPos[0] / size[0], clickPos[1] / size[1]]
        viewport = self.EasyTransfer.Renderer.GetViewport()
        viewportRelative = [
            (windowRelative[0] - viewport[0]) / (viewport[2] - viewport[0]),
            (windowRelative[1] - viewport[1]) / (viewport[3] - viewport[1]),
        ]
        if (
            viewportRelative[0] >= 0
            and viewportRelative[0] <= 1
            and viewportRelative[1] >= 0
            and viewportRelative[1] <= 1
        ):
            # x = viewportRelative[0] * self.EasyTransfer.CanvasWidth
            yfull = int(viewportRelative[1] * (self.EasyTransfer.CanvasHeight * 4))
            plot = yfull // self.EasyTransfer.CanvasHeight
            if self.LastPlot != plot:
                return
            y = yfull % self.EasyTransfer.CanvasHeight
            # color plots: 3=R, 2=G, 1=B
            if plot >= 1:
                vrange = self.EasyTransfer.ColorTransferFunction.GetRange()
                size = self.EasyTransfer.ColorTransferFunction.GetSize()
                T = viewportRelative[0] * (vrange[1] - vrange[0]) + vrange[0]
                L = 0
                R = size
                while L < R:
                    m = (L + R) // 2
                    if self.EasyTransfer.ColorData[m][0] < T:
                        L = m + 1
                    else:
                        R = m
                L = max(L - 1, 0)
                self.EasyTransfer.ColorData[L][4 - plot] = (
                    y / self.EasyTransfer.CanvasHeight
                )
                if self.LastX == -1:
                    self.LastX = L
                for index in range(self.LastX, L + 2):
                    t = self.EasyTransfer.ColorData[index][0]
                    idx = L if plot == 3 else index
                    r = self.EasyTransfer.ColorData[idx][1]
                    idx = L if plot == 2 else index
                    g = self.EasyTransfer.ColorData[idx][2]
                    idx = L if plot == 1 else index
                    b = self.EasyTransfer.ColorData[idx][3]
                    self.EasyTransfer.ColorTransferFunction.AddRGBPoint(t, r, g, b)
                    self.EasyTransfer.ColorData.append([t, r, g, b])
                for index in range(L, self.LastX + 2):
                    t = self.EasyTransfer.ColorData[index][0]
                    idx = L if plot == 3 else index
                    r = self.EasyTransfer.ColorData[idx][1]
                    idx = L if plot == 2 else index
                    g = self.EasyTransfer.ColorData[idx][2]
                    idx = L if plot == 1 else index
                    b = self.EasyTransfer.ColorData[idx][3]
                    self.EasyTransfer.ColorTransferFunction.AddRGBPoint(t, r, g, b)
                    self.EasyTransfer.ColorData.append([t, r, g, b])

                self.LastX = L
                self.EasyTransfer.RefreshImage()
            # opacity plot: 0
            else:
                vrange = self.EasyTransfer.OpacityTransferFunction.GetRange()
                size = self.EasyTransfer.OpacityTransferFunction.GetSize()
                T = viewportRelative[0] * (vrange[1] - vrange[0]) + vrange[0]
                L = 0
                R = size
                while L < R:
                    m = (L + R) // 2
                    if self.EasyTransfer.OpacityData[m][0] < T:
                        L = m + 1
                    else:
                        R = m

                L = max(L - 1, 0)
                self.EasyTransfer.OpacityData[L][1] = y / self.EasyTransfer.CanvasHeight
                if self.LastX == -1:
                    self.LastX = L
                for index in range(self.LastX, L + 2):
                    t = self.EasyTransfer.OpacityData[index][0]
                    o = self.EasyTransfer.OpacityData[L][1]
                    self.EasyTransfer.OpacityTransferFunction.AddPoint(t, o)
                    self.EasyTransfer.OpacityData.append([t, o])
                for index in range(L, self.LastX + 2):
                    t = self.EasyTransfer.OpacityData[index][0]
                    o = self.EasyTransfer.OpacityData[L][1]
                    self.EasyTransfer.OpacityTransferFunction.AddPoint(t, o)
                    self.EasyTransfer.OpacityData.append([t, o])
                self.LastX = L
                self.EasyTransfer.RefreshImage()


class vtkEasyTransfer(vtk.vtkObject):
    def __init__(self):
        self.CanvasWidth = 256
        self.CanvasHeight = 100
        self.numPoints = 256
        self.minValue = 0
        self.maxValue = 255

        self.ColorTransferFunction = vtk.vtkColorTransferFunction()
        self.OpacityTransferFunction = vtk.vtkPiecewiseFunction()
        self.ColorData = []
        self.OpacityData = []

        self.Renderer = vtk.vtkRenderer()
        self.Renderer.ResetCamera()

        self.Drawing = vtk.vtkImageCanvasSource2D()
        self.Drawing.SetNumberOfScalarComponents(3)
        self.Drawing.SetScalarTypeToUnsignedChar()
        self.Drawing.SetExtent(
            0, self.CanvasWidth - 1, 0, 4 * self.CanvasHeight - 1, 0, 1
        )

        imageMapper = vtk.vtkImageMapper()
        imageMapper.SetInputConnection(self.Drawing.GetOutputPort())
        imageMapper.SetColorWindow(1)
        imageMapper.SetColorLevel(0)

        imageActor = vtk.vtkActor2D()
        imageActor.SetMapper(imageMapper)
        self.Renderer.AddActor2D(imageActor)

        self.InteractorStyle = vtkEasyTransferInteractorStyle()
        self.InteractorStyle.SetEasyTransfer(self)

    def SetColormapHeat(self):
        self.ColorTransferFunction.RemoveAllPoints()
        self.OpacityTransferFunction.RemoveAllPoints()
        self.ColorData = []
        self.OpacityData = []

        for i in range(self.numPoints):
            t = i / (self.numPoints - 1)
            x = self.minValue + t * (self.maxValue - self.minValue)
            r = min(max(0.0, ((-1.0411 * t + 0.4149) * t + 0.0162) * t + 0.9949), 1.0)
            g = min(max(0.0, ((1.7442 * t + -2.7388) * t + 0.1454) * t + 0.9971), 1.0)
            b = min(max(0.0, ((0.9397 * t + -0.2565) * t + -1.5570) * t + 0.9161), 1.0)
            self.ColorData.append([x, r, g, b])
            self.OpacityData.append([x, t])
            self.ColorTransferFunction.AddRGBPoint(x, r, g, b)
            self.OpacityTransferFunction.AddPoint(x, t)
        self.RefreshImage()

    # Sets a default color map.
    def SetColormapBlue2Red(self):
        self.ColorTransferFunction.RemoveAllPoints()
        self.OpacityTransferFunction.RemoveAllPoints()
        self.ColorData = []
        self.OpacityData = []
        for i in range(self.numPoints):
            t = i / (self.numPoints - 1)
            x = self.minValue + t * (self.maxValue - self.minValue)
            r = min(
                max(
                    0.0,
                    (((5.0048 * t + -8.0915) * t + 1.1657) * t + 1.4380) * t + 0.6639,
                ),
                1.0,
            )
            g = min(
                max(
                    0.0,
                    (((7.4158 * t + -15.9415) * t + 7.4696) * t + 1.2767) * t + -0.0013,
                ),
                1.0,
            )
            b = min(
                max(
                    0.0,
                    (((6.1246 * t + -16.2287) * t + 11.9910) * t + -1.4886) * t
                    + 0.1685,
                ),
                1.0,
            )
            self.ColorData.append([x, r, g, b])
            self.OpacityData.append([x, t])
            self.ColorTransferFunction.AddRGBPoint(x, r, g, b)
            self.OpacityTransferFunction.AddPoint(x, t)
        self.RefreshImage()

    # Sets the color map range
    def SetColorRange(self, minValue, maxValue):
        vrange = self.ColorTransferFunction.GetRange()
        size = self.ColorTransferFunction.GetSize()
        self.ColorTransferFunction.RemoveAllPoints()
        for i in range(size):
            told = (self.ColorData[i][0] - vrange[0]) / (vrange[1] - vrange[0])
            tnew = told * (maxValue - minValue) + minValue
            r, g, b = self.ColorData[i][1], self.ColorData[i][2], self.ColorData[i][3]
            self.ColorData[i][0] = tnew
            self.ColorTransferFunction.AddRGBPoint(tnew, r, g, b)

    # Sets the opacity map range
    def SetOpacityRange(self, minValue, maxValue):
        vrange = self.OpacityTransferFunction.GetRange()
        size = self.OpacityTransferFunction.GetSize()
        self.OpacityTransferFunction.RemoveAllPoints()
        for i in range(size):
            told = (self.OpacityData[i][0] - vrange[0]) / (vrange[1] - vrange[0])
            tnew = told * (maxValue - minValue) + minValue
            o = self.OpacityData[i][1]
            self.OpacityData[i][0] = tnew
            self.OpacityTransferFunction.AddPoint(tnew, o)

    # Gets the color transfer function.
    def GetColorTransferFunction(self):
        return self.ColorTransferFunction

    # Gets the opacity transfer function.
    def GetOpacityTransferFunction(self):
        return self.OpacityTransferFunction

    #  Gets the renderer.
    def GetRenderer(self):
        return self.Renderer

    # Gets the interactor for user interactions.
    def GetInteractorStyle(self):
        return self.InteractorStyle

    # Recomputes the color map images. Call this function, whenever the viewport has changed! (only updates the viewport bounds, if this is already assigned to a vtkRenderWindow)
    def RefreshImage(self):
        if self.Renderer.GetRenderWindow():
            size = self.Renderer.GetRenderWindow().GetSize()
            viewport = self.Renderer.GetViewport()
            self.CanvasWidth = int(size[0] * (viewport[2] - viewport[0]))
            self.CanvasHeight = int(size[1] * (viewport[3] - viewport[1]) / 4)
            self.Drawing.SetExtent(
                0,
                int(size[0] * (viewport[2] - viewport[0]) - 1),
                0,
                int(size[1] * (viewport[3] - viewport[1]) - 1),
                0,
                1,
            )

        self.Drawing.SetDrawColor(1, 1, 1)
        self.Drawing.FillBox(0, self.CanvasWidth, 0, 4 * self.CanvasHeight)

        # draw color maps
        vrange = self.ColorTransferFunction.GetRange()
        size = self.ColorTransferFunction.GetSize()

        for i in range(size):
            lower = int(
                (self.ColorData[i][0] - vrange[0])
                / (vrange[1] - vrange[0])
                * (self.CanvasWidth - 1)
            )
            upper = int(
                self.CanvasWidth
                if i == size - 1
                else (self.ColorData[i + 1][0] - vrange[0])
                / (vrange[1] - vrange[0])
                * (self.CanvasWidth - 1)
            )
            valueR = int(self.ColorData[i][1] * self.CanvasHeight)
            valueG = int(self.ColorData[i][2] * self.CanvasHeight)
            valueB = int(self.ColorData[i][3] * self.CanvasHeight)

            self.Drawing.SetDrawColor(1.0, 0.1, 0.1)
            self.Drawing.FillBox(
                lower, upper, 3 * self.CanvasHeight, 3 * self.CanvasHeight + valueR
            )
            self.Drawing.SetDrawColor(0.1, 1.0, 0.1)
            self.Drawing.FillBox(
                lower, upper, 2 * self.CanvasHeight, 2 * self.CanvasHeight + valueG
            )
            self.Drawing.SetDrawColor(0.1, 0.1, 1.0)
            self.Drawing.FillBox(
                lower, upper, 1 * self.CanvasHeight, 1 * self.CanvasHeight + valueB
            )

        # draw opacity maps
        vrange = self.OpacityTransferFunction.GetRange()
        size = self.OpacityTransferFunction.GetSize()

        for i in range(size):
            lower = int(
                (self.OpacityData[i][0] - vrange[0])
                / (vrange[1] - vrange[0])
                * (self.CanvasWidth - 1)
            )
            upper = int(
                self.CanvasWidth
                if i == size - 1
                else (self.OpacityData[i + 1][0] - vrange[0])
                / (vrange[1] - vrange[0])
                * (self.CanvasWidth - 1)
            )
            valueO = int(self.OpacityData[i][1] * self.CanvasHeight)

            self.Drawing.SetDrawColor(0.3, 0.3, 0.3)
            self.Drawing.FillBox(
                lower, upper, 0 * self.CanvasHeight, 0 * self.CanvasHeight + valueO
            )
