import vtk

# ----------------------------------------------------------------
# create image button
# ----------------------------------------------------------------
def createImage(image: vtk.vtkImageData, color1: list, color2: list):
    # Specify the size of the image data
    image.SetDimensions(10, 10, 1)
    image.AllocateScalars(vtk.VTK_UNSIGNED_CHAR, 3)
    dims = image.GetDimensions()

    # Fill the image with
    for y in range(dims[1]):
        for x in range(dims[0]):
            color = color1 if x < 5 else color2
            for c in range(3):
                image.SetScalarComponentFromDouble(x, y, 0, c, color[c])

def vtkArray2vtkImageData(vtkArray, origin, dimension, spacing, isScalar=True, isPoint=True):
    """
    Converting extracted vtkArray into vtkImageData.
    Can be either scalar points or vector points.

    Args:
        vtkArray (_type_): _description_
        origin (_type_): _description_
        dimension (_type_): point dimes
        spacing (_type_): cell spacing

    Returns:
        _type_: _description_
    """
    image = vtk.vtkImageData()
    image.SetOrigin(origin)
    image.SetDimensions(dimension)
    image.SetSpacing(spacing)
    if isPoint is True:
        if isScalar is True:
            image.GetPointData().SetScalars(vtkArray)
        else:
            image.GetPointData().SetVectors(vtkArray)
    else:
        raise ValueError(">>> Cannot use for cell data. Please manually convert it to vtkImageData.")
    return image
