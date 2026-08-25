# annie_swc

annie_swc is for neuroscientists (and others) who need a reliable way to convert legacy SWC files into newer formats.
There are tens of thousands of valuable SWC tracings on web sites like neuromorpho.org, and they represent a lot of
work, and even though AI does a better job in today's world, we don't want to throw these valuable tracings away! 
Among other things, they're very useful for statistical studies, branching analysis, and generating reasonably 
accurate computational compartments for biophysical simulations. 

annie_swc will take an imperfect SWC tracing, and convert it into a set of watertight meshes. The set includes
an optimized 2-d triangular surface mesh, a tetrahedralized 3d version suitable for organelle insertion, and 
a voxelized 3d version, each having a maximum segmented resolution of approximately 1 nm. (All parts
of the Annie software suite are designed to scale over 9 orders of magnitude - between 1nm and 1m - because 
it uses the GPU when available, and because 128-bit floating point math has yet to reach the desktop). These 
files can be used as starting points for finite element analysis and molecular dynamics simulations. To 
follow shortly is a post-processing stage that starts with one of these perfect meshes, partitions it, 
assigns physical groups to it, and formats .sif files for Elmer and .geo files for MOOSE, as well as 
.msh files that can be read into open source CAD tools like Salome. Additionally there is value in
making the mesh available in different forms (an oriented half-edge mesh is different from a list
of vertices and faces), and in different file formats (finite element tools often prefer a CAD format).

Interoperability is required in today's world, and the sad truth is AI is usually confused about it,
and well trained physics and math informed neural networks are expensive. A good solution at the moment is
to leverage and encapsulate the best of legacy software. Some of it won't even compile anymore, much of
it is no longer maintained and certificates have expired for remote downloads. The good parts of it need
to be saved, and annie_swc is an example. The goal is an end-to-end workflow starting with tracings, 
EM stacks, and synthetic morphology, resulting eventually in a conversion suite for discrete differential 
geometry, FE-DEC, classic FEA, and much more. For neurons specifically, the goal is full spectrum biophysics, 
including charge, mechanics, and fluid dynamics. This becomes especially important for synapses and interactions 
between neurons and astrocytes. These are ambitious goals, but they can be accomplished with a judicious 
application of new and old technology, and adding the resulting information to the AI knowledge base. 

At the moment, annie_swc is more than a convenience, it addresses a gap in the integrity of the early stages 
of the open source workflow. There is no single tool that accomplishes the first part of the workflow on its
own. The problems range from seg faults to undocumented features. annie_swc curates the parts of each
application that actually work, it's been field tested on at least a thousand (random) SWC files, with
a success rate of about 85%. The remaining 15% is some combination of imprecision and human error, for 
example many times a file will mesh perfectly but at the end it will have a self-intersection, because 
the radius in the SWC file was too big. annie_swc will flag and identify these imperfections.

## Processing Sequence

0. Open SWC File - checks existence and builds CSV, status = "Pandas DataFrame"
1. Verify Surface - removes dangling segments from the SWC file, no change in status
2. De-Skeletonize - creates a .ply file from the SWC in three steps, status = "Cylinderized PLY"
3. Triangulate - resamples and converts the mesh to Wavefront OBJ form, status = "Triangulated OBJ"
3. Clean & Optimize - decimates and optimizes the mesh into a new OBJ, status = "Optimized OBJ"
4. Tetrahedralize - tetrahedralizes the mesh and saves VTU and GLTF files, status = "Tetrahedralized"
5. Voxelize - voxelizes the mesh and saves VTK, VTU, and GLTF files, status = "Completely Converted"
6. Analysis - compares the surfaces and volumes and generates statistics

## Configuration

Configuration is defined in the annie_swc_config.py file. There are three settings:

(On Windows, use double backslashes like this "e:\\annie\\annie_swc\\")

CLIENT_HOME_DIR is the location of the config file and the annie_swc executable.
CLIENT_DATA_DIR is the location where data will be read and stored
CLIENT_ROOT_DIR is the top level directory shown in dialogs

## Dependencies

annie_swc runs as a web page under Panel. It is a carefully curated collection of the 
portions of legacy geometry tools that work reliably for large (and small) SWC files.

annie_swc has the following dependencies:

numpy
pandas
panel
pyvista
open3d
tetgen
pyacvd
pymeshfix

Additionally the following standard Python libraries are used:

sys
pathlib

It is highly recommended to create a basic Python 3.12 virtual environment first,
then install the above dependencies manually using 'pip install <package_name>'.
Please see the IMPORTANT and NOTES sections below for installation details.

## Usage

Using annie_swc inside a virtual Python environment is highly recommended, because the
dependencies change from one release to the next. annie_swc currently wants Python 3.12,
which is stable and supports the full spectrum of dependencies.

To start the app, use the following from the shell command line:

panel serve annie_swc.py

Once the Bokeh server has been started, surf to the following web page:

http://localhost:5006/annie_swc

After a moment, you should see the annie_swc dashboard. Many of the buttons have been greyed out for
future enhancements. To use annie_swc, simply press every button on the left hand side
of the dashboard in descending order. The buttons correspond to the processing sequence
above. Output files will be created in the same folder as the source. There is a trace
file called 'annie_swc_trace.txt' and debug output is available in 'annie_swc_debug.txt'.

Complete conversion generates 13 additional files (besides the original SWC). It is often
helpful to keep each file in a separate source directory, this way all related files are
together in the same folder. To navigate to a new data folder, select "Change Data Folder"
on the right hand side of the dashboard. You can do this in the middle of a conversion, 
if you'd like to keep the GLTF files separate from the VTK outputs.

## Known Bugs

In the SWC tab, if you press the 'Last' button, the grid changes shape, and it's unrecoverable.
A bug report has been filed with Panel. Try to avoid pressing the 'Last' button if possible.

## IMPORTANT - Read Before Installing

Many of the Python repositories (including Anaconda) are heavily infested with viruses 
and malware. It is highly recommended to have protective software installed on your machine 
prior to installing any of the dependencies above!

All you need, to run annie_swc, are the files in the src folder (there is one Python script
and one config file). Create a folder of your choice on your machine, download these two files,
and optionally create the Data folder if you wish to use it. Update the config file to point
to the correct paths, and from the command line type 'panel serve annie_swc.py'.

## Notes

When installing dependencies manually, the pymeshfix install may not work the first time.
It complains about a version of setuptools. If you subsequently use pip install --upgrade pymeshfix
it seems to work. Strange behavior like this though, should be a heads-up for malware.
Always use a reliable threat defender!

During the mesh optimization phase you'll see a lot of output from VTK on the screen, just ignore it.
It comes from extra information that open3d adds to the end of an OBJ file. It does nothing, it
just gets ignored. You can turn off the messages if you wish.

This open source software is made available under the MIT license. 

Documentation (including detailed installation instructions) and a description of the Annie 
software suite is here: https://annie-interface.org




