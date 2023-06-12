# wildfire-simulation
Project for the course Scientific Visualization at ETH in spring 2023.

[Report](report/report.pdf)

## Disclaimer

If you are having trouble with dependencies, try using the provided `conda.yml` file.

## TODO List
- [X] [Yitong] VTK code baseline.
- [X] (**5 points**) [Yitong] Volume rendering on: fire, water vapor, grass.
- [X] [Yitong] Surface rendering on: soil.
- [X] (**5 points**) [Yitong] Compute & visualize velocity field and its streamline. 
- [X] (**5/3 points**) [Yitong] Compute & visualize vorticity. 
- [ ] ~~(**5/3 points**) Compute & visualize lambda2.~~
- [X] (**5/3 points**) [Johannes] Compute & visualize divergence.
- [X] (**5 points**) [Johannes] Isosurface.
- [X] [Yitong] Animation codes.
- [X] (**5 points**) [Stuart, Yitong] Generate animations on 6 datasets.
- [ ] ~~Convert `theta` from cell to point values.~~
- [X] [Yingyan] GUI code pipeline.
- [X] [Stuart, Yingyan] Data preprocessing (in vtk).
- [X] [Stuart, Yingyan] GUI acceleration.
- [X] (**5 points**) [Stuart] Transfer function editing in GUI.
- [X] [Stuart, Yingyan] GUI refinements.
- [X] (**Bonus, <10 points**) [Yitong] Line Integral Convolution, for VLS analysis.
- [X] [Yingyan] GUI demo video.
- [X] Analyzing factors contribute to VLS behavior.
- [X] Final presentation slides.
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

### 5.15 Fully automatic preprocessing
- Fully automatic preprocessing which allows the GUI to run more smoothly

### 5.16 Transfer function editing
- Isosurfaces for the fire-air boundary
- Transfer function editing for vorticity, load default colormaps.