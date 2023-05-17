# wildfire-simulation
Project for the course Scientific Visualization at ETH in spring 2023.

## Disclaimer

If you are having trouble with dependencies, try using the provided `conda.yml` file.

## TODO List
- [X] Load an `.vts` file.
- [X] Resample curvilinear data to image data (for fire and watervapor) as done in Paraview.
- [X] Extract curvilinear subset (for soil and grass) as done in Paraview.
- [X] Define colormap based on Paraview colormap file (transfer function editing).
- [X] (**5 points**) Volume rendering on: fire, water vapor, grass.
- [X] Surface rendering on: soil.
- [X] Set camera intrinsics and extrinsics.
- [X] Build vtk code pipeline.
- [X] Tune colormaps.
- [X] Compositie wind velocity field.
- [X] Compute wind gradient field and vorticity.
- [X] (**5 points**) Visualize velocity streamline. 
- [X] (**5/3 points**) Compute & visualize vorticity. 
- [ ] (**5/3 points**) Compute & visualize lambda2.
- [ ] (**5/3 points**) Compute & visualize divergence.
- [ ] (**5 points**) Isosurface.
- [X] Animation codes.
- [X] (**5 points**) Generate animations on 6 datasets.
- [ ] Convert `theta` from cell to point values.
- [X] GUI code pipeline.
- [X] Data preprocessing (in vtk).
- [X] GUI using preprocessed files.
- [X] (**5 points**) Transfer function editing.
- [ ] GUI refinements (TODO: Buttons to go back and forth 1 frame at a time)
- [ ] GUI demo video.
- [ ] Analyzing factors contribute to VLS behavior.
- [ ] Final presentation slides.
- [ ] (*10 points*) Final report.


## Log
### 4.30 General Code Pipeline
<p align="center">
    <img src="./media/0430.png" alt="" style="width:800px;" />
</p>

### 5.2 Composite Velocity Field + Visualize Streamlines
<p align="center">
    <img src="./media/0502.png" alt="" style="width:800px;" />
</p>

### 5.6 GUI Code Pipeline
<p align="center">
    <img src="./media/0506_streamline.png" alt="" style="width:800px;" />
</p>

### 5.7 Visualized Vorticity
<p align="center">
    <img src="./media/0507.png" alt="" style="width:800px;" />
</p>

### 5.8 Add Naive Animation Codes & Fix Blank Window Bug
- Use `getAnimation.py` to get full animations
- Fix blank window bug

### 5.14 All animation videos uploaded
- All animation videos head/curve 40/80/320 fire/streamlines/vorticity uploaded

### 5.15 Fully automatic preprocessing
- Fully automatic preprocessing which allows the GUI to run more smoothly

### 5.16 Transfer function editing
- Isosurfaces for the fire-air boundary
- Transfer function editing for vorticity (TODO: load default colormaps)