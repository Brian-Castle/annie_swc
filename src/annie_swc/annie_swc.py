############################################################################################
#
# ANNIE_SWC v 0.1 - Astrocyte Neural Network Interface Engine / SWC Converter
#
# by Brian Castle https://briancastle.com https://annie-interface.org
#
# Creates a dashboard for the SWC converter tool.
#
# (c) 1993-2026 BRIAN M CASTLE
#
# Released under the MIT License
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of this 
# software and associated documentation files (the “Software”), to deal in the Software 
# without restriction, including without limitation the rights to use, copy, modify, 
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to 
# permit persons to whom the Software is furnished to do so, subject to the following 
# conditions:
# 
# The above copyright notice and this permission notice shall be included in all copies 
# or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR 
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE 
# FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR 
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER 
# DEALINGS IN THE SOFTWARE.
#
############################################################################################

import annie_swc_config

import numpy as np
import pandas as pd
import panel as pn
import pyvista as pv
import open3d as o3d
import tetgen
import pyacvd
import pymeshfix

from pathlib import Path
import sys

#
# define the debug level for this file
#

DEBUG_CLIENT = 3
TRACE_CLIENT = 4

trace_file_handle = None
debug_file_handle = None

def annie_mesh_trace(level, *args):
	global trace_file_handle
	global TRACE_CLIENT
	if trace_file_handle != None and level <= TRACE_CLIENT:
		print(*args, file=trace_file_handle)

def annie_mesh_debug(level, *args):
	global debug_file_handle
	global DEBUG_CLIENT
	if debug_file_handle != None and level <= DEBUG_CLIENT:
		print(*args, file=debug_file_handle)

#
# we'd like to be notified if anyone kills our session
#

def session_destroyed(session_context):
    print(f'Destroyed a session running at the {session_context.request.uri} endpoint')

pn.state.on_session_destroyed(session_destroyed)

#
# generic counter for top right of screen
#

current_tick = pn.rx(0)

#
# set a default data folder
#

data_folder = annie_swc_config.CLIENT_DATA_DIR

########################################################################
# track files loaded into Annie's mesh tool
########################################################################

#
# define mesh file status
#

FILE_STATUS_NONE = 0
FILE_STATUS_RAW = 1
FILE_STATUS_CYL = 2
FILE_STATUS_TRI = 3
FILE_STATUS_OBJ = 4
FILE_STATUS_OPT = 5
FILE_STATUS_TET = 6
FILE_STATUS_VOX = 7
FILE_STATUS_DONE = 8
FILE_STATUS_CLEARED = 16

def return_mesh_status(s):
	if s == FILE_STATUS_NONE:
		return "None"
	elif s == FILE_STATUS_RAW:
		return "Pandas DataFrame"
	elif s == FILE_STATUS_CYL:
		return "Cylinderized PLY"
	elif s == FILE_STATUS_TRI:
		return "Triangulated OBJ"
	elif s == FILE_STATUS_OBJ:
		return "Cleaned OBJ"
	elif s == FILE_STATUS_OPT:
		return "Optimized OBJ"
	elif s == FILE_STATUS_TET:
		return "Tetrahedralized"
	elif s == FILE_STATUS_VOX:
		return "Voxelized"
	elif s == FILE_STATUS_DONE:
		return "Completely Converted"
	elif s == FILE_STATUS_CLEARED:
		return "Cleared"
	else:
		return"(unknown)"

#
# define mesh file class
#

class meshfile():
	def __init__(self, sourcename):
		self.status = FILE_STATUS_NONE
		self.sourcename = sourcename
		self.basename = None
		self.fullname = None
		self.handle = None		# open file handle if any
		self.swc_elements = 0
		self.cylinders = 0
		self.ply_points = 0
		self.ply_faces = 0
		self.num_triangles = 0		# triangles in initial OBJ file
		self.clean_points = 0
		self.clean_faces = 0
		self.tet_nodes = 0
		self.tet_elems = 0
		self.tet_edges = 0
		self.tet_faces = 0
		self.voxels = 0
		self.pandas_array = None	# csv array from pandas for SWC data
		self.pv_array = None		# array of pv cylinders for obj
	def set_status(self, s):
		self.status = s
	def get_status(self):
		return self.status
	def set_handle(self, h):
		self.handle = h
	def get_handle(self):
		return self.handle
	def set_swc_elements(self, e):
		self.swc_elements = e
	def get_swc_elements(self):
		return self.swc_elements
	def set_cylinders(self, c):
		self.cylinders = c
	def get_cylinders(self):
		return self.cylinders
	def set_pandas_array(self, a):
		self.pandas_array = a
	def get_pandas_array(self):
		return self.pandas_array
	def set_pv_array(self, a):
		self.pv_array = a
	def get_pv_array(self):
		return self.pv_array
	def get_sourcename(self):
		return self.sourcename
	def set_basename(self, b):
		self.basename = b
	def get_basename(self):
		return self.basename
	def set_fullname(self, f):
		self.fullname = f
	def get_fullname(self):
		return self.fullname
	def set_ply_points(self, p):
		self.ply_points = p
	def get_ply_points(self):
		return self.ply_points
	def set_ply_faces(self, f):
		self.ply_faces = f
	def get_ply_faces(self):
		return self.ply_faces
	def set_num_triangles(self, t):
		self.num_triangles = t
	def get_num_triangles(self):
		return self.num_triangles
	def set_clean_points(self, p):
		self.clean_points = p
	def get_clean_points(self):
		return self.clean_points
	def set_clean_faces(self, f):
		self.clean_faces = f
	def get_clean_faces(self):
		return self.clean_faces
	def set_tet_nodes(self, n):
		self.tet_nodes = n
	def get_tet_nodes(self):
		return self.tet_nodes
	def set_tet_elems(self, e):
		self.tet_elems = e
	def get_tet_elems(self):
		return self.tet_elems
	def set_tet_edges(self, e):
		self.tet_edges = e
	def get_tet_edges(self):
		return self.tet_edges
	def set_tet_faces(self, f):
		self.tet_faces = f
	def get_tet_faces(self):
		return self.tet_faces
	def set_voxels(self, v):
		self.voxels = v
	def get_voxels(self):
		return self.voxels

#
# array of loaded mesh files
#

meshfiles = []

def find_mesh_by_name(name):
	l = len(meshfiles)
	for i in range(l):
		m = meshfiles[i]
		if m.get_status() != FILE_STATUS_CLEARED:
			n = m.get_sourcename()
			b = m.get_basename()
			if name == n or name == b:
				return m, i
	return None, -1

#
# current mesh file
#

CurrentMeshFile = None

#
# routine to set the current mesh file
#

def on_mesh_file_select(event):
	global CurrentMeshFile
	print(f'on_mesh_file_select(): You selected: {event.new}')
	mesh, index = find_mesh_by_name(event.new)
	if mesh != None and index >= 0:
		print("found mesh, index =", index)
		CurrentMeshFile = index
		this_mesh_index.value = str(index)
		# this_mesh_index.param.trigger('value')

########################################################################
# begin by defining necessary reactive variables and widgets
########################################################################

#
# these are reactive display variables and buttons for the top central pane
#

# these are hidden widgets that serve as controllers, they help maintain the
# dashboard's idea of "current" objects - these are PER TAB

this_mesh_name = pn.widgets.TextInput(name="this_mesh_name", placeholder="(none)")
this_mesh_index = pn.widgets.TextInput(name="this_mesh_index", placeholder="-1")

this_network_name = pn.widgets.TextInput(name="this_network_name", placeholder="(none)")
this_network_status = pn.widgets.TextInput(name="this_network_status", placeholder="(none)")
this_simulation_name = pn.widgets.TextInput(name="this_simulation_name", placeholder="(none)")
this_simulation_status = pn.widgets.TextInput(name="this_simulation_status", placeholder="(none)")

this_cell_name = pn.widgets.TextInput(name="this_cell_name", placeholder="(none)")
this_cell_status = pn.widgets.TextInput(name="this_cell_status", placeholder="(none)")
this_neuron_name = pn.widgets.TextInput(name="this_neuron_name", placeholder="(none)")
this_neuron_status = pn.widgets.TextInput(name="this_neuron_status", placeholder="(none)")
this_connection_name = pn.widgets.TextInput(name="this_connection_name", placeholder="(none)")
this_connection_status = pn.widgets.TextInput(name="this_connection_status", placeholder="(none)")
this_synapse_name = pn.widgets.TextInput(name="this_synapse_name", placeholder="(none)")
this_synapse_status = pn.widgets.TextInput(name="this_synapse_status", placeholder="(none)")

this_probe_name = pn.widgets.TextInput(name="this_probe_name", placeholder="(none)")
this_probe_status = pn.widgets.TextInput(name="this_probe_status", placeholder="(none)")
this_template_name = pn.widgets.TextInput(name="this_template_name", placeholder="(none)")
this_template_status = pn.widgets.TextInput(name="this_template_status", placeholder="(none)")
this_apply_name = pn.widgets.TextInput(name="this_apply_name", placeholder="(none)")
this_apply_status = pn.widgets.TextInput(name="this_apply_status", placeholder="(none)")
this_vtk_name = pn.widgets.TextInput(name="this_vtk_name", placeholder="(none)")
this_vtk_status = pn.widgets.TextInput(name="this_vtk_status", placeholder="(none)")
this_results_name = pn.widgets.TextInput(name="this_results_name", placeholder="(none)")
this_results_status = pn.widgets.TextInput(name="this_results_status", placeholder="(none)")
this_rerender_name = pn.widgets.TextInput(name="this_results_name", placeholder="(none)")
this_rerender_status = pn.widgets.TextInput(name="this_results_status", placeholder="(none)")

#
# this is a widget to hold the server response
#

server_response_widget = pn.widgets.TextInput(name="this_network_name", placeholder="(none)")

#
# these are special controllers for the tabs, to force them to redraw
#

network_tab_controller = pn.widgets.TextInput(name="network_tab_controller", placeholder="(none)")		# SWC
cell_tab_controller = pn.widgets.TextInput(name="cell_tab_controller", placeholder="(none)")			# Cylinders
connection_tab_controller = pn.widgets.TextInput(name="connection_tab_controller", placeholder="(none)")	# Surface
synapse_tab_controller = pn.widgets.TextInput(name="synapse_tab_controller", placeholder="(none)")		# Volume
probe_tab_controller = pn.widgets.TextInput(name="probe_tab_controller", placeholder="(none)")			# Voxels
template_tab_controller = pn.widgets.TextInput(name="template_tab_controller", placeholder="(none)")		# Statistics
vtk_tab_controller = pn.widgets.TextInput(name="vtk_tab_controller", placeholder="(none)")
results_tab_controller = pn.widgets.TextInput(name="results_tab_controller", placeholder="(none)")
rerender_tab_controller = pn.widgets.TextInput(name="rerender_tab_controller", placeholder="(none)")

#
# define a generic spacer
#

spacer = "<br>"

#############################################################################
# define the left sidebar
#############################################################################

# 
# define the group of file related buttons in the left sidebar
#

button_open_swc = pn.widgets.Button(name="Open SWC File", button_type="primary", width=300)
button_open_obj = pn.widgets.Button(name="Open OBJ file", button_type="primary", width=300)
file_group = pn.Column(spacer, button_open_swc, button_open_obj, spacer)

def update_inputs(event):
	global meshfiles
	global CurrentMeshFile
	current_mesh_name = ""
	if CurrentMeshFile != None and CurrentMeshFile >= 0:
		mesh = meshfiles[CurrentMeshFile]
		current_mesh_name = mesh.get_sourcename()
		print("update_input(): CurrentMeshFile =", CurrentMeshFile, "name =", current_mesh_name)
	selected_input = event.new
	print("update_input(): selected_input =", selected_input)
	options = available_inputs.value
	s = selected_input
	input_selector.param.update(options=dict(zip(options,options)),value=dict(zip(s,s)))
	if current_mesh_name != "":
		input_selector.value = current_mesh_name

def update_outputs(event):
	selected_output = event.new
	options = available_outputs.value
	s = selected_output
	output_selector.param.update(options=dict(zip(options,options)),value=dict(zip(s,s)))

#
# define the left sidebar
#

available_inputs = pn.widgets.ArrayInput(name='Available_Inputs', placeholder="(none)", value=[])
available_outputs = pn.widgets.ArrayInput(name='Available_Outputs', placeholder="(none)", value=[])

available_inputs.param.watch(update_inputs, 'value')
available_outputs.param.watch(update_outputs, 'value')

input_selector = pn.widgets.Select(name="Input File", options=[], width=300)
input_selector.param.watch(on_mesh_file_select, 'value')
button_verify = pn.widgets.Button(name="Verify Surface", button_type="primary", width=300)
button_deskeletonize = pn.widgets.Button(name="De-Skeletonize", button_type="primary", width=300)
button_triangulate = pn.widgets.Button(name="Triangulate", button_type="primary", width=300)
button_cleanmesh = pn.widgets.Button(name="Optimize & Clean", button_type="primary", width=300)
button_tetrahedralize = pn.widgets.Button(name="Tetrahedralize", button_type="primary", width=300)
button_voxelize = pn.widgets.Button(name="Voxelize", button_type="primary", width=300)
input_group = pn.Column(input_selector, button_verify, button_deskeletonize, button_triangulate, button_cleanmesh, button_tetrahedralize, button_voxelize)

output_selector = pn.widgets.Select(name="Output File Placeholder", options=[], width=300)
button_savehdf5 = pn.widgets.Button(name="Save As HDF5", button_type="primary", width=300)
output_group = pn.Column(output_selector, button_savehdf5)

left_sidebar = pn.Column(file_group,spacer,input_group,spacer,spacer,output_group,width=320)

#
# define the modal dialog box for Change Data Folder
#

change_data_folder_ok = pn.widgets.Button(name='OK')
change_data_folder_cancel = pn.widgets.Button(name='Cancel')
change_data_folder_buttons = pn.Row(change_data_folder_cancel, change_data_folder_ok)
change_data_folder_name = pn.widgets.TextInput(name='Folder Path:')
change_data_folder_column = pn.Column('<center><font color="mediumblue"><b> => CHANGE DATA FOLDER <= </b></font>&nbsp;</center><br>', change_data_folder_name, '<br>')
change_data_folder_modal = pn.Modal(change_data_folder_column, change_data_folder_buttons, name='Change Data Folder Modal', show_close_button = False, background_close = False, margin=20)

def close_change_data_folder_modal_with_okay(event):
	global data_folder
	annie_mesh_debug(1, "ANNIE_CLIENT: change data folder: close_change_data_folder_modal_with_okay(): OK")
	# make sure we have a name
	requested_name = change_data_folder_name.value
	if requested_name == None or requested_name == "":
		server_response_widget.value = '<font color="red">LOCAL ERROR</font>: FOLDER NAME NOT GIVEN'
		change_data_folder_modal.hide()
		return

	# make sure the folder exists - FIXME FIXME

	data_folder = requested_name

	# done - set status
	change_data_folder_modal.hide()
	server_response_status = "DATA FOLDER CHANGED"
	annie_mesh_debug(1, "")
	server_response_widget.value = server_response_status

def close_change_data_folder_modal_with_cancel(event):
	annie_mesh_debug(1, "Change Data Folder Modal: Cancel")
	change_data_folder_name.value = ""
	change_data_folder_modal.hide()

pn.bind(close_change_data_folder_modal_with_okay, change_data_folder_ok, watch=True)
pn.bind(close_change_data_folder_modal_with_cancel, change_data_folder_cancel, watch=True)

#############################################################################################
# define modal dialogs for left sidebar
#############################################################################################

#
# define the modal dialog box for open SWC file
#

open_swc_name = pn.widgets.FileSelector(directory=data_folder, file_pattern="*.swc", root_directory=annie_swc_config.CLIENT_ROOT_DIR)
open_swc_ok = pn.widgets.Button(name='OK')
open_swc_cancel = pn.widgets.Button(name='Cancel')
open_swc_buttons = pn.Row(open_swc_cancel, open_swc_ok)
open_swc_modal = pn.Modal(open_swc_name, open_swc_buttons, name='Open SWC Modal', margin=20, show_close_button=False, background_close = False)

def close_open_swc_with_okay(event):
	global meshfiles
	global CurrentMeshFile
	global data_folder

	error_occurred = 0
	emsg = ""

	annie_mesh_debug(1, "close_open_swc_with_okay(): OK")

	# the user can select more than one name
	# the LAST file processed will become the
	# current network
	sfnames = open_swc_name.value
	sfl = len(sfnames)
	annie_mesh_debug(1, sfl, "files selected")
	annie_mesh_debug(1, sfnames)
	open_swc_modal.hide()
	server_response_status = "(unknown)"
	if sfl > 1:
		t = "<font color=\"red\">Please select one file only</font>"
		server_response_widget.value = t
		return "1"
	if sfl <= 0:
		t = "<font color=\"red\">Please select an input file</font>"
		server_response_widget.value = t
		return "1"
	if sfl > 0:

		#
		# clear any existing data
		#

		nfiles = len(meshfiles)
		for i in range(nfiles):
			# locate the file in the list of known files
			mfile = meshfiles[i]
			if mfile == None:
				continue

			# mark the file as deleted
			mfile.set_status(FILE_STATUS_CLEARED)

			# remove the file from the list of available files
			### FIXME FIXME

		# tickle the list display
		available_inputs.value = []

		button_verify.disabled = True
		button_deskeletonize.disabled = True
		button_triangulate.disabled = True
		button_cleanmesh.disabled = True
		button_tetrahedralize.disabled = True
		button_voxelize.disabled = True

		#
		# iterate through the requested list
		#

		for k in range(sfl):

			#
			# is the network already known to us? if it is, 
			# we might have to clean it up - FIXME FIXME
			#

			fname = sfnames[k]

			#
			# we have to fix the file name, in Windows
			# it comes back mangled
			#

			fname2 = fname.replace("\\", "/")

			#
			# try to open the file
			#

			bad = 1
			file = None
			try:
				file = open(fname2, "r")
				if file != None:
					bad = 0
			except:
				pass
			if bad > 0 or file == None:
				if emsg == "":
					emsg = "File " + fname2 + " not found"
				error_occurred = 1
				continue

			print("filename =", fname2)

			#
			# parse the file name to extract the extension
			#

			this_path = Path(fname2)
			whole_name = this_path.name
			base_name = this_path.stem
			print("whole_name =", whole_name)
			print("base_name =", base_name)
			output_name = data_folder + base_name + ".csv"
			print("CSV output name =", output_name)

			#
			# is the name or the basename already in the list?
			#

			### FIXME FIXME

			#
			# try to open the output file
			#

			bad = 1
			out = None
			try:
				out = open(output_name, "w")
				if out != None:
					bad = 0
			except:
				pass

			if bad > 0 or out == None:
				if emsg == "":
					emsg = "Unable to open output file " + output_name
				error_occurred = 1
				continue

			#
			# allocate an entry in the meshfile list
			#

			mesh = meshfile(whole_name)

			#
			# READ THE SWC FILE INTO A PANDAS ARRAY
			#

			print("reading SWC")

			count = 0
			with file:
				line = file.readline()
				while line:
					fields = line.split()
					id = int(fields[0])
					x = float(fields[2])
					y = float(fields[3])
					z = float(fields[4])
					radius = float(fields[5])
					parent = int(fields[6])
					# print(count, x, y, z, radius, parent, file=out)
					print(id, x, y, z, radius, parent, file=out)
					line = file.readline()
					count = count + 1
				file.close()
			out.close()

			# read back as pandas array
			skel = pd.read_csv(output_name, sep = ' ', header=None)
			skel = skel.set_axis(['id', 'x', 'y', 'z', 'radius', 'parent'], axis=1)
			print(skel)
			# print(skel[0])
			mesh.set_pandas_array(skel)
			mesh.set_status(FILE_STATUS_RAW)
			mesh.set_basename(base_name)
			mesh.set_fullname(fname2)
			mesh.set_swc_elements(count)

			# append mesh to mesh list
			print("appending to mesh list")
			l = len(meshfiles)
			meshfiles.append(mesh)

			# set current mesh file
			print("setting current mesh file")
			CurrentMeshFile = l

			# append file to available inputs
			print("appending to available inputs")
			available_inputs.value.append(whole_name)
			available_inputs.param.trigger('value')

			# set mesh name and index for header display
			print("setting mesh name and index")

			if l == 0:
				this_mesh_index.value = "0"
			else:
				this_mesh_index.value = str(l)

			# end per-file

		# emit status
		if error_occurred == 0:
			if sfl == 1:
				server_response_status = f"<font color=\"green\">{sfl} file converted to Pandas array with {count} elements</font>"
				button_verify.disabled = False
			else:
				server_response_status = f"<font color=\"green\">{sfl} files converted to Pandas arrays</font>"
		else:
			server_response_status = f"<font color=\"red\">Error occurred: {emsg} </font>"

		# tickle update of the SWC ("network") tab
		network_tab_controller.param.trigger('value')
	else:
		# no names selected
		server_response_status = "LOCAL MESSAGE: (no names selected), load_swc"

	server_response_widget.value = server_response_status

def close_open_swc_with_cancel(event):
	annie_mesh_debug(1, "close_open_swc_with_cancel(): Cancel")
	open_swc_name.value = []
	annie_mesh_debug(1, open_swc_name.value)
	open_swc_modal.hide()

pn.bind(close_open_swc_with_okay, open_swc_ok, watch=True)
pn.bind(close_open_swc_with_cancel, open_swc_cancel, watch=True)

#
# define the modal dialog box for open OBJ
#

open_obj_name = pn.widgets.FileSelector(directory=data_folder, file_pattern="*.obj", root_directory=annie_swc_config.CLIENT_ROOT_DIR)
open_obj_ok = pn.widgets.Button(name='OK')
open_obj_cancel = pn.widgets.Button(name='Cancel')
open_obj_buttons = pn.Row(open_obj_cancel, open_obj_ok)
open_obj_modal = pn.Modal(open_obj_name, open_obj_buttons, name='Open OBJ Modal', margin=20, show_close_button=False, background_close = False)

def close_open_obj_with_okay(event):

	global meshfiles
	global CurrentMeshFile

	error_occurred = 0
	emsg = ""

	annie_mesh_debug(1, "close_open_obj_with_okay(): OK")

	# the user can select more than one name
	# the LAST file processed will become the
	# current network
	sfnames = open_obj_name.value
	sfl = len(sfnames)
	annie_mesh_debug(1, sfl, "files selected")
	annie_mesh_debug(1, sfnames)
	open_obj_modal.hide()
	server_response_status = "(unknown)"
	if sfl > 0:

		#
		# iterate through the list
		#

		for k in range(sfl):

			#
			# is the network already known to us? if it is, 
			# we might have to clean it up - FIXME FIXME
			#

			fname = sfnames[k]

			#
			# we have to fix the file name, in Windows
			# it comes back mangled
			#

			fname2 = fname.replace("\\", "/")

			#
			# try to open the file
			#

			bad = 1
			file = None
			try:
				file = open(fname2, "r")
				if file != None:
					bad = 0
			except:
				pass
			if bad > 0 or file == None:
				# ERROR
				print("ERROR!!! file not found")
				continue

			#
			# parse the file name to extract the extension
			#

			this_path = Path(fname2)
			whole_name = this_path.name
			base_name = this_path.stem

			#
			# is the name or the basename already in the list?
			#

			### FIXME FIXME

			#
			# allocate an entry in the meshfile list
			#

			mesh = meshfile(whole_name)

			#
			# add to meshfiles list
			# read in OBJ file
			# do stats/quality
			# pass to cleanmesh
			#

			mesh.set_status(FILE_STATUS_TRI)
			mesh.set_basename(base_name)
			mesh.set_fullname(fname2)

			# append mesh to mesh list
			print("appending to mesh list")
			l = len(meshfiles)
			meshfiles.append(mesh)
			# set current mesh file
			print("setting current mesh file")
			CurrentMeshFile = l

#
# should read file here, and set vertices, faces, and triangles FIXME FIXME
#
			file.close()

			tmpmesh = pv.read(fname2)
			mesh.set_ply_points(tmpmesh.n_points)
			mesh.set_ply_faces(tmpmesh.n_faces)
			mesh.set_num_triangles(tmpmesh.n_faces)

			# append file to available inputs
			print("appending to available inputs")
			available_inputs.value.append(whole_name)
			available_inputs.param.trigger('value')

			# set mesh name and index for header display
			print("setting mesh name and index")

			if l == 0:
				this_mesh_index.value = "0"
			else:
				this_mesh_index.value = str(l)

			# end per-file

		# emit status
		if error_occurred == 0:
			if sfl == 1:
				server_response_status = f"<font color=\"green\">{sfl} OBJ file ready to process</font>"
			else:
				server_response_status = f"<font color=\"green\">{sfl} OBJ files ready to process</font>"
		else:
			server_response_status = f"<font color=\"red\">Error occurred: {emsg} </font>"
		# tickle update of various tabs
	else:
		# no names selected
		server_response_status = "LOCAL MESSAGE: (no names selected), load_obj"

	server_response_widget.value = server_response_status

def close_open_obj_with_cancel(event):
	annie_mesh_debug(1, "Open OBJ: Cancel")
	open_obj_name.value = []
	open_obj_modal.hide()

pn.bind(close_open_obj_with_okay, open_obj_ok, watch=True)
pn.bind(close_open_obj_with_cancel, open_obj_cancel, watch=True)

####################################################################################
# define the main center page
####################################################################################

#
# routine to render the network with matplotlib
# (shows up in the cells tab)
#

def render_current_network():
	net = None
	annie_mesh_debug(1, "render_current_network(): entry")
	new_pane = pn.pane.Markdown("# Network2")
	return new_pane

###########################################################################
# define the tabs on the main screen
###########################################################################

#
# Cylinders tab (cell tab)
#

def draw_cell_tab(cell_name, cell_status, tab_condition):
	global meshfiles
	global CurrentMeshFile

	annie_mesh_debug(1, "draw_cell_tab(): entry")

	res = ""

	if CurrentMeshFile != None and CurrentMeshFile >= 0:
		print("CurrentMeshFile =", CurrentMeshFile)
		mesh = meshfiles[CurrentMeshFile]
		stat = mesh.get_status()
		if stat >= FILE_STATUS_CYL and stat < FILE_STATUS_CLEARED:
			cyls = mesh.get_cylinders()
			len_cyls = cyls
			pts = mesh.get_ply_points()
			len_pts = pts
			faces = mesh.get_ply_faces()
			len_faces = faces
			res = "# <br>" + str(len_cyls) + " Cylinders<br>" + str(len_pts) + " Points " + str(len_faces) + " Faces " + "<br>"
		else:
			res = "# <br>(mesh file not ready)"
	else:
		res = "# <br>(no cylinders available)"

	new_pane2 = pn.pane.Markdown(res)
	return new_pane2

tab_cells = pn.pane.Markdown("(no cylinders)")

#
# Surface tab (connections tab)
#

def draw_connections_tab(connection_name, connection_status, tab_condition):
	global meshfiles
	global CurrentMeshFile

	res = ""

	if CurrentMeshFile != None and CurrentMeshFile >= 0:
		mesh = meshfiles[CurrentMeshFile]
		stat = mesh.get_status()
		clean_points = mesh.get_clean_points()
		clean_faces = mesh.get_clean_faces()
		if stat >= FILE_STATUS_OPT and stat < FILE_STATUS_CLEARED:
			res = "# <br>" + str(clean_points) + " Points " + str(clean_faces) + " Faces "
		else:
			res = "# <br> (mesh file not ready) <br>"
	else:
		res = "# <br> (mesh file not selected) <br>"

	annie_mesh_debug(1, "drawing Surface tab")

	col = pn.Column(res)
	return col

tab_connections = pn.pane.Markdown("# (no surfaces)")

#
# Volume tab (Synapses Tab)
#

def draw_synapses_tab(synapse_name, synapse_status, tab_condition):
	global meshfiles
	global CurrentMeshFile

	res = ""

	if CurrentMeshFile != None and CurrentMeshFile >= 0:
		mesh = meshfiles[CurrentMeshFile]
		stat = mesh.get_status()
		if stat >= FILE_STATUS_TET and stat < FILE_STATUS_CLEARED:
			tet_nodes = mesh.get_tet_nodes()
			tet_faces = mesh.get_tet_faces()
			res = "# <br>" + str(tet_nodes) + " Points " + str(tet_faces) + " Faces "
		else:
			res = "# <br>(mesh file not ready) <br>"
	else:
		res = "# <br>(mesh file not selected) <br>"

	annie_mesh_debug(1, "drawing Volume tab")

	col = pn.Column(res)
	return col

tab_synapses = pn.pane.Markdown("# (no volumes)")

#
# probes tab (Voxels tab)
#

def draw_probes_tab(probe_name, probe_status, tab_condition):
	global meshfiles
	global CurrentMeshFile

	res = "(voxels not available)"

	if CurrentMeshFile != None and CurrentMeshFile >= 0:
		mesh = meshfiles[CurrentMeshFile]
		stat = mesh.get_status()
		if stat >= FILE_STATUS_VOX and stat < FILE_STATUS_CLEARED:
			voxels = mesh.get_voxels()
			res = "# <br>" + str(voxels) + " Voxels "
		else:
			res = "# <br>(mesh file not ready) <br>"
	else:
		annie_mesh_trace(1, "CurrentMeshFile =", CurrentMeshFile)
		res = "# <br>(mesh file not selected) <br>"

	annie_mesh_debug(1, "drawing Voxels tab")

	col = pn.Column(res)
	return col

res = "# &nbsp;(no voxels)<br><br>"
tab_probes = pn.pane.Markdown(res)

#
# templates tab ("Statistics tab")
#

def draw_templates_tab(template_name, template_status, tab_condition):
	global meshfiles
	global CurrentMeshFile

	res = "(statistics not available)"

	if CurrentMeshFile != None and CurrentMeshFile >= 0:
		mesh = meshfiles[CurrentMeshFile]
		stat = mesh.get_status()
		if stat >= FILE_STATUS_DONE and stat < FILE_STATUS_CLEARED:

			clean_points = mesh.get_clean_points()
			clean_faces = mesh.get_clean_faces()
			res = "# <br>Triangular: " + str(clean_points) + " Points " + str(clean_faces) + " Faces "

			tet_nodes = mesh.get_tet_nodes()
			tet_faces = mesh.get_tet_faces()
			res = res + "<br>Tetrahedral: " + str(tet_nodes) + " Points " + str(tet_faces) + " Faces "

			voxels = mesh.get_voxels()
			res = res + "<br>" + str(voxels) + " Voxels "
		else:
			res = "# <br>(mesh file not ready) <br>"
	else:
		print("CurrentMeshFile =", CurrentMeshFile)
		annie_mesh_trace(1, "CurrentMeshFile =", CurrentMeshFile)
		res = "# <br>(mesh file not selected) <br>"

	print("drawing statistics tab")
	annie_mesh_debug(1, "drawing Statistics tab")

	col = pn.Column(res)
	return col

res = "# &nbsp;Statistics<br><br>"
tab_templates = pn.pane.Markdown(res)

#
# VTK tab
#

def draw_vtk_tab(vtk_name, vtk_status, tab_condition):
	retval = "# VTK"
	res = ""
	annie_mesh_debug(1, "draw_vtk_tab(): entry")
	# sys.exit()

	geom_pane = pn.pane.Markdown("# Pane 1")
	geom_pane2 = pn.pane.Markdown("# Pane 2")

	retstr = pn.Row(
		geom_pane,
		geom_pane2
	)

	return retstr

res = "# &nbsp;VTK<br><br>"
tab_vtk = pn.pane.Markdown(res)


results_tab_counter = 0

def draw_results_tab(results_name, results_status, tab_condition):
	global results_tab_counter
	res = "# Simulation"
	annie_mesh_debug(1, "draw_simulation/results_tab(): entry")
	return res

res = "# &nbsp;Simulation<br><br>"
tab_results = pn.pane.Markdown(res)

def rerender_function(event):
	global jj

	annie_mesh_debug(1, "re-rendering: synchronizing - rerender_function : ENTRY")

	point_cloud = jj.get_point_cloud()
	point_cloud.clearPoints()

	render_window = jj.get_render_window()
	renderer = jj.get_renderer()

	cel = annie_lib.cells.get_cell_by_name(c, "RODS6")
	if cel != None:
		annie_mesh_debug(1, "rerender(): GOT CELL")
		initialized = jj.get_initialized()
		neur_list = cel.get_neuron_list()
		l = len(neur_list)
		annie_mesh_debug(1, l, "neurons")
		for i in range(l):
			neur = neur_list[i]
			loc = neur.get_location()
			x = loc.get_x()
			y = loc.get_y()
			z = loc.get_z()
			v = neur.get_input_level()
			level = neur.get_level()
			if level != 0.0:
				annie_mesh_debug(1, "Level:", level)
			neur_type = neur.get_type()
			if neur_type == annie_lib.neurons.NS_NTYPE_BINARY:
				level = 10 * level
			point = (x,y,level)
			point_cloud.addPoint(point)

	point_cloud.vtkActor.GetProperty().SetPointSize(10)  # Size in pixels
	render_window.Render()
	mypane = jj.get_pane()
	mypane.synchronize()

this_rerender_status.param.watch(rerender_function, 'value')

###################################################################################
# define the tabs on the main screen
###################################################################################

#
# routine to draw the network tab
# 
# this has a special controller, we can use it to
# re-draw the network tab when it's showing a VTK frame
#

def draw_network_tab(sim_name, net_name, sim_status, net_status, tab_condition):
	global meshfiles
	global CurrentMeshFile

	res = ""

	if CurrentMeshFile != None and CurrentMeshFile >= 0:
		mesh = meshfiles[CurrentMeshFile]
		elements = mesh.get_swc_elements()
		data = mesh.get_pandas_array()
		if data.empty == True:
			if elements > 0:
				# we had data but it got lost
				res = res + "# No Bones, data got lost <br>"
			else:
				# we never had data in the first place
				res = res + "# No Bones, never had them <br>"
			# see if we can find the file and read them back in
		else:
			# we have valid data - show it
			l = len(data)
			# res = res + str(l) + " Bones in Skeleton"
			print("l =", l, "data.head =", data.head(5))
			res = pn.widgets.Tabulator(data, max_height=500, show_index=True)
	else:
		print("CurrentMeshFile =", CurrentMeshFile)
		res = "# (mesh file not selected) <br>"

	annie_mesh_debug(1, "drawing SWC tab")

	col = pn.Column(res)
	return col

tab_network_bind = pn.bind(draw_network_tab, sim_name=this_simulation_name, net_name=this_network_name, sim_status=this_simulation_status, net_status=this_network_status, tab_condition=network_tab_controller)
tab_network_network = pn.Row(tab_network_bind, name="SWC")

tab_cells_bind = pn.bind(draw_cell_tab, cell_name=this_cell_name, cell_status=this_cell_status, tab_condition=cell_tab_controller)
tab_cells_cells = pn.Row(tab_cells_bind, name="Cylinders")

tab_connections_bind = pn.bind(draw_connections_tab, connection_name=this_connection_name, connection_status=this_connection_status, tab_condition=connection_tab_controller)
tab_connections_connections = pn.Row(tab_connections_bind, name="Surface")

tab_synapses_bind = pn.bind(draw_synapses_tab, synapse_name=this_synapse_name, synapse_status=this_synapse_status, tab_condition=synapse_tab_controller)
tab_synapses_synapses = pn.Row(tab_synapses_bind, name="Volume")

tab_probes_bind = pn.bind(draw_probes_tab, probe_name=this_probe_name, probe_status=this_probe_status, tab_condition=probe_tab_controller)
tab_probes_probes = pn.Row(tab_probes_bind, name="Voxels")

tab_templates_bind = pn.bind(draw_templates_tab, template_name=this_template_name, template_status=this_template_status, tab_condition=template_tab_controller)
tab_templates_templates = pn.Row(tab_templates_bind, name="Statistics")

tab_vtk_bind = pn.bind(draw_vtk_tab, vtk_name=this_vtk_name, vtk_status=this_vtk_status, tab_condition=vtk_tab_controller)
tab_vtk_vtk = pn.Row(tab_vtk_bind, name="Graphics")

tab_results_bind = pn.bind(draw_results_tab, results_name=this_results_name, results_status=this_results_status, tab_condition=results_tab_controller)
tab_results_results = pn.Row(tab_results_bind, name="Simulation")

#
# put the tabs together with their functions
#

tabs = pn.Tabs(tab_network_network, tab_cells_cells, tab_connections_connections, tab_synapses_synapses, tab_probes_probes, tab_templates_templates, tab_vtk_vtk, tab_results_results) # , dynamic=True, )

#####################################################################################
# define the right sidebar
#####################################################################################

##############################################
# define modal dialog boxes for right sidebar
##############################################

#
# dispatch routine to change the data folder
#

button_change_data_folder = pn.widgets.Button(name="Change Data Folder", button_type="primary", width=300)

def change_data_folder(clicked):
	global data_folder
	if clicked:
		annie_mesh_debug(1, "change data folder")
		if change_data_folder_modal != None:
			change_data_folder_name.value = data_folder
			change_data_folder_modal.show()
	return "0"

rchangedatafolder = pn.pane.Markdown(pn.bind(change_data_folder, button_change_data_folder))

############################
# DEFINE THE RIGHT SIDEBAR
############################

right_sidebar = pn.Column(spacer, spacer, button_change_data_folder, spacer)

############################
# DEFINE THE TOP HEADER
############################

#
# define the header row across the top of the page
#

def draw_top_central_pane(mesh_index):
	global meshfiles
	global CurrentMeshFile

	print("draw_top_central_pane(): mesh_index =", mesh_index)

	sim_contents = '## Current Mesh: '
	if mesh_index != '' and int(mesh_index) >= 0:
		index = int(mesh_index)
		mesh = meshfiles[index]
		name = mesh.get_basename()
		sim_contents = sim_contents + "<font color=\"magenta\">" + name + "</font><br>"
		elements = mesh.get_swc_elements()
		sim_contents = sim_contents + "&nbsp; &nbsp; &nbsp; <font color=\"green\">" + str(elements) + " SWC Nodes</font><br>"
		stat = return_mesh_status(mesh.get_status())
		sim_contents = sim_contents + "&nbsp; &nbsp; &nbsp; <font color=\"green\">Mesh Status: </font><font color=\"blue\">" + stat + "</font><br>"
		stat = mesh.get_status()
		if stat > FILE_STATUS_CYL and stat < FILE_STATUS_TRI:
			# after cylinderalization, before triangulation
			verts = str(mesh.get_ply_points())
			faces = str(mesh.get_ply_faces())
			sim_contents = sim_contents + "&nbsp; &nbsp; &nbsp; <font color=\"green\">Vertices: </font><font color=\"blue\">" + verts + "</font> <font color=\"green\">Faces: </font><font color=\"blue\">" + faces + "</font><br>"
		elif stat >= FILE_STATUS_TRI and stat < FILE_STATUS_OBJ:
			# after initial triangulation
			tris = str(mesh.get_num_triangles())
			sim_contents = sim_contents + "&nbsp; &nbsp; &nbsp; <font color=\"green\">Triangles: </font><font color=\"blue\">" + tris + "</font><br>"
		elif stat >= FILE_STATUS_OBJ and stat < FILE_STATUS_OPT:
			verts = str(mesh.get_ply_points())
			faces = str(mesh.get_ply_faces())
			sim_contents = sim_contents + "&nbsp; &nbsp; &nbsp; <font color=\"green\">Vertices: </font><font color=\"blue\">" + verts + "</font> <font color=\"green\">Faces: </font><font color=\"blue\">" + faces + "</font><br>"
		elif stat >= FILE_STATUS_OPT and stat < FILE_STATUS_TET:
			verts = str(mesh.get_clean_points())
			faces = str(mesh.get_clean_faces())
			sim_contents = sim_contents + "&nbsp; &nbsp; &nbsp; <font color=\"green\">Vertices: </font><font color=\"blue\">" + verts + "</font> <font color=\"green\">Faces: </font><font color=\"blue\">" + faces + "</font><br>"
		elif stat >= FILE_STATUS_TET and stat < FILE_STATUS_VOX:
			nodes = str(mesh.get_tet_nodes())
			elems = str(mesh.get_tet_elems())
			edges = str(mesh.get_tet_edges())
			faces = str(mesh.get_tet_faces())
			sim_contents = sim_contents + "&nbsp; &nbsp; &nbsp; <font color=\"green\">Nodes: </font><font color=\"blue\">" + nodes + "</font> <font color=\"green\">Elems: </font><font color=\"blue\">" + elems + "</font><br>"
			sim_contents = sim_contents + "&nbsp; &nbsp; &nbsp; <font color=\"green\">Edges: </font><font color=\"blue\">" + edges + "</font> <font color=\"green\">Faces: </font><font color=\"blue\">" + faces + "</font><br>"
		elif stat >= FILE_STATUS_VOX and stat < FILE_STATUS_DONE:
			voxs = str(mesh.get_voxels())
			sim_contents = sim_contents + "&nbsp; &nbsp; &nbsp; <font color=\"green\">Voxels: </font><font color=\"blue\">" + voxs + "</font><br>"
		elif stat == FILE_STATUS_DONE:
			nodes = str(mesh.get_tet_nodes())
			elems = str(mesh.get_tet_elems())
			edges = str(mesh.get_tet_edges())
			faces = str(mesh.get_tet_faces())
			sim_contents = sim_contents + "&nbsp; &nbsp; &nbsp; <font color=\"green\">Nodes: </font><font color=\"blue\">" + nodes + "</font> <font color=\"green\">Elems: </font><font color=\"blue\">" + elems + "</font><br>"
			sim_contents = sim_contents + "&nbsp; &nbsp; &nbsp; <font color=\"green\">Edges: </font><font color=\"blue\">" + edges + "</font> <font color=\"green\">Faces: </font><font color=\"blue\">" + faces + "</font><br>"
			voxs = str(mesh.get_voxels())
			sim_contents = sim_contents + "&nbsp; &nbsp; &nbsp; <font color=\"green\">Voxels: </font><font color=\"blue\">" + voxs + "</font><br>"

	else:
		sim_contents = sim_contents + "(none)"

	sim_row = pn.Row(sim_contents)
	return pn.Column(sim_row)

top_central_string = pn.bind(draw_top_central_pane, mesh_index=this_mesh_index)
header = pn.Row(top_central_string, width=1200)

#
# define the server status bar at the bottom of the page
#

def draw_server_status_pane(event):

	output_string = "## Status: "
	status_string = server_response_widget.value
	if status_string != None and status_string != "":
		output_string = output_string + status_string
	return output_string

server_status_string = pn.bind(draw_server_status_pane, server_response_widget)
trailer = pn.Row(server_status_string, width=1200)

#
# define the tick viewer on the top right
#

tick_view = pn.indicators.Number(
    name="Nodes",
    value=current_tick,
    width=300,
    format="{value}",
    colors=[(0, "green"), (1000000, "green")],
)

#
# the top row contains the header plus the tick viewer
#

header_row = pn.Row(header, tick_view)

#
# define the copyright row at the bottom of every tab
#

copyright = pn.pane.Markdown("(c) 2026 Indie Heaven LLC - Licensed for Personal Use by a Single User")

#
# define the main window
#

left_modals1 = pn.Row(change_data_folder_modal)
left_modals2 = pn.Row(open_swc_modal, open_obj_modal)

aggregate_modals = pn.Column(left_modals1, left_modals2)

left_main = pn.Column(tabs, copyright, trailer, aggregate_modals, width=1200)

right_main = pn.Column(right_sidebar, width=300)
mains = pn.Row(left_main, right_main)

main_box = pn.Column(header_row, mains)

####################################################################################################
# LEFT SIDEBAR
####################################################################################################

#
# dispatch routine to open a network (invoked by left sidebar button)
#

def file_open_swc(clicked):
	if clicked:
		annie_mesh_debug(1, "open swc")
		if open_swc_modal != None:
			open_swc_modal.show()
	return "0"

rfileopenswc = pn.pane.Markdown(pn.bind(file_open_swc, button_open_swc))

#
# dispatch routine to open a simulation (invoked by left sidebar button)
#

def file_open_obj(clicked):
	if clicked:
		if open_obj_modal != None:
			open_obj_modal.show()
	annie_mesh_debug(1, "open OBJ file")
	return "0"

rfileopensimulation = pn.pane.Markdown(pn.bind(file_open_obj, button_open_obj))

#
# routine to verify an SWC (invoked by left sidebar button)
#

def verify(clicked):

	global meshfiles
	global CurrentMeshFile
	global data_folder

	error_occurred = 0
	emsg = ""

	annie_mesh_debug(1, "verify()")
	if CurrentMeshFile == None or CurrentMeshFile < 0:
		t = "Mesh File not selected"
		server_response_widget.value = t
		return "1"

	index = int(CurrentMeshFile)
	mesh = meshfiles[index]
	stat = mesh.get_status()
	if stat != FILE_STATUS_RAW:
		t = "Mesh File not in RAW status"
		server_response_widget.value = t
		return "2"

	basename = mesh.get_basename()
	print("basename =", basename)
	swc = data_folder + basename + ".swc"

	#
	# these are ordinary python lists containing numpy components
	# (except for parent which is an integer index)
	#

	xs = []
	ys = []
	zs = []

	radii = []
	parents = []

	count = 0

	annie_mesh_trace(1, "reading swc file", swc, "...")

	current_tick.rx.value = 0

	t = "Checking SWC file..."
	server_response_widget.value = t

	df = pd.read_table(swc, sep=' ', header=None)
	df.columns=['id', 'junk', 'x', 'y', 'z', 'radius', 'parent']
	# get length and print
	l = len(df)
	print('DONE PARSING, df.len =', l)
	annie_mesh_trace(1, 'DONE PARSING, df.len =', l)
	annie_mesh_trace(1, 'df =')
	annie_mesh_trace(1, df)
	# print out each row
	for i in range(l):
		row = df.iloc[i]
		annie_mesh_trace(1, 'row', i, row)

	# check for NaN
	has_nan = df.isna().any().any()
	annie_mesh_trace(1, 'has_nan =', has_nan)
	if has_nan == True:
		print("SWC file has at least one NaN")
		t = "SWC file has at least one NaN"
		server_response_widget.value = t
		return "3"

	# look for anything without a parent
	without_parents = [0] * l
	withouts = []
	for i in range(l):
		row = df.iloc[i]
		if row['parent'] == 0 or row['parent'] == -1:
			without_parents[i] = 1
			withouts.append(i)
		else:
			without_parents[i] = 0
	without = len(withouts)
	annie_mesh_trace(1, 'number of entries without parents =', without)
	annie_mesh_trace(1, 'withouts =', withouts)
	# there should be exactly one entry without a parent (the root)
	if without > 1:
		print('Too many entries without parents. Terminating.')
		annie_mesh_trace(1, 'Too many entries without parents. Terminating.')
		t = "Too many entries without parents"
		server_response_widget.value = t
		return "4"

	# Build children map & trace all paths from root(s)
	# children is a DICTIONARY by entry ID
	t = "Processing children..."
	server_response_widget.value = t
	print("PROCESSING CHILDREN")
	annie_mesh_trace(1, "PROCESSING CHILDREN")
	children = {int(r): [] for r in df['id']}
	for _, row in df.iterrows():
		pid = int(row['parent'])
		if pd.notna(pid) and pid != -1:
			children[pid].append(int(row['id']))

	# anything without children is an end point
	print("DONE WITH CHILDREN")
	annie_mesh_trace(1, "DONE WITH CHILDREN")
	annie_mesh_trace(1, "len(children) = ", len(children))
	annie_mesh_trace(1, "children =")
	lc = len(children)
	for index, (key, value) in enumerate(children.items()):
		annie_mesh_trace(1, f"{index} {key} {value}")
    
	# find the root of the tree
	roots = df[df['parent'] == -1]['id'].astype(int).tolist()
	annie_mesh_trace(1, "roots =", roots)

	t = "Processing segments..."
	server_response_widget.value = t
	print("PROCESSING SEGMENTS")
	annie_mesh_trace(1, "PROCESSING SEGMENTS")

	segments = []

	def trace_path(current_id):
		path = [current_id]
		for child in children[current_id]:
			path.extend(trace_path(child))
		return path

	t = "Processing paths..."
	server_response_widget.value = t
	print("PROCESSING PATHS")
	annie_mesh_trace(1, "PROCESSING PATHS")
	all_paths = []
	for r in roots:
		p = trace_path(r)
		for i in range(len(p)-1):
			n1, n2 = df.loc[df['id']==p[i]].iloc[0], df.loc[df['id']==p[i+1]].iloc[0]
			seg_len = np.linalg.norm(n1[['x','y','z']].values - n2[['x','y','z']].values)
			if seg_len > 1e-6:  # Skip degenerate segments
				segments.append((n1, n2))
			else:
				print("SKIPPING DEGENERATE SEGMENT")

	# print all segments
	annie_mesh_trace(1, "Segments:")
	l = len(segments)
	for i in range(l):
		segment = segments[i]
		annie_mesh_trace(1, segment)

	# reset tick counter
	current_tick.rx.value = 0

	# emit status
	print("SWC FILE VERIFIED")
	annie_mesh_trace(1, "SWC FILE VERIFIED")
	t = "<font color=\"green\">SWC FILE VERIFIED</font>"
	server_response_widget.value = t

	# enable functionality
	button_deskeletonize.disabled = False
	button_verify.disabled = True

	return "0"

rverify = pn.pane.Markdown(pn.bind(verify, button_verify))

#
# routine to deskeletonize an SWC (invoked by left sidebar button)
#

def deskeletonize(clicked):

	global meshfiles
	global CurrentMeshFile
	global data_folder

	error_occurred = 0
	emsg = ""

	annie_mesh_debug(1, "deskeletonize()")
	if CurrentMeshFile == None or CurrentMeshFile < 0:
		return "1"

	index = int(CurrentMeshFile)
	mesh = meshfiles[index]
	stat = mesh.get_status()
	if stat != FILE_STATUS_RAW:
		return "2"

	basename = mesh.get_basename()
	print("basename =", basename)
	csv = data_folder + basename + ".csv"
	print("csv =", csv)

	#
	# these are ordinary python lists containing numpy components
	# (except for parent which is an integer index)
	#

	xs = []
	ys = []
	zs = []

	radii = []
	parents = []

	count = 0

	display_objects = []

	print("reading csv file", csv, "...")

	current_tick.rx.value = 0

	t = "Reading skeleton geometry..."
	server_response_widget.value = t

	file = open(csv, "r")
	with file:
		line = file.readline()
		while line:
			fields = line.split()
			actual_ind = int(fields[0])
			index = count
			if index != count:
				break
			x = np.float64(fields[1])
			y = np.float64(fields[2])
			z = np.float64(fields[3])
			r = np.float64(fields[4])
			parent = int(fields[5])

			annie_mesh_trace(1, "spec", count, "index", actual_ind, "x", x, "y", y, "z", z, "r", r, "parent", parent)

			xs.append(x)
			ys.append(y)
			zs.append(z)
			radii.append(r)
			if parent == -1:	# first entry
				parent = 0
			else:			# all other entries
				parent = parent - 1
			parents.append(parent)

			if index == 0:
				sphere = pv.Sphere(center=(x,y,z),radius=3*r)
				display_objects.append(sphere)
				annie_mesh_trace(TRACE_CLIENT, "got sphere, count =", count)
			else:
				# direction vector
				vec_x = x - xs[parent]
				vec_y = y - ys[parent]
				vec_z = z - zs[parent]
				h = np.sqrt(vec_x*vec_x + vec_y*vec_y + vec_z*vec_z)
				center_x = xs[parent] + vec_x / 2.0
				center_y = ys[parent] + vec_y / 2.0
				center_z = zs[parent] + vec_z / 2.0
				annie_mesh_trace(1, "cylinder", count, "from", xs[parent], ys[parent], zs[parent], "to", x, y, z, "height", h, "radius", r)
				cylinder = pv.Cylinder(center=(center_x,center_y,center_z),direction=(vec_x,vec_y,vec_z),radius=r,height=h,resolution=100,capping=True)
				display_objects.append(cylinder)
			line = file.readline()
			count = count + 1
			if count > 0 and count % 100 == 0:
				current_tick.rx.value = count
		file.close()

	vertex_count = count

	# display_objects[0] is the sphere
	# everything else is a cylinder
	print(len(display_objects), "display objects")
	annie_mesh_trace(1, "len(display_objects) =", len(display_objects))

	t = "Synthesizing cylindrical representation..."
	server_response_widget.value = t

	# now synthesize an OBJ file
	current_tick.rx.value = 0
	print("writing OBJ")
	cylinder_file_name = data_folder + basename + "_cylinders.obj"
	ofile = open(cylinder_file_name, "w")
	with ofile:
		print("# ANNIE v0.1 OBJ File Export", file=ofile)
		print("# https://annie-interface.org", file=ofile)
		print("mtllib loose_parts.mtl", file=ofile)
		l = len(display_objects)
		point_base = 0
		total_face_count = 0
		for i in range(l):
			object = display_objects[i]
			if i % 100 == 0:
				# print("setting current tick")
				current_tick.rx.value = i
			if i == 0:
				continue
				# sphere
				print("o cell_body", file=ofile)
				points = object.points
				normals = object.point_normals
				faces = object.faces
				lpoints = len(points)
				lnormals = len(normals)
				lfaces = len(faces)
				annie_mesh_trace(1, "Sphere: lpoints =", lpoints, "lnormals =", lnormals, "lfaces =", lfaces)
				for j in range(lpoints):
					point = points[j]
					x = point[0]
					y = point[1]
					z = point[2]
					print("v", x, y, z, file=ofile)
				for j in range(lnormals):
					normal = normals[j]
					x = normal[0]
					y = normal[1]
					z = normal[2]
					print("vn", x, y, z, file=ofile)
				f = 0
				while f < lfaces:
					count = faces[f]
					if count != 3:
						print("count != 3")
						break
					f = f + 1
					ff = []
					for k in range(count):
						ff.append(faces[f + k])
					print(f'f {ff[0]+1}//{ff[0]+1} {ff[1]+1}//{ff[1]+1} {ff[2]+1}//{ff[2]+1}', file=ofile)
					f = f + count
				point_base = point_base + lpoints
			else:
				# cylinder
				print(f'o branch_{i}', file=ofile)
				points = object.points
				good = 0
				normals = []
				try:
					normals = object.point_normals
					good = 1
				except:
					normals = []
				better = 0
				faces = []
				try:
					faces = object.faces
					better = 1
				except:
					faces = []
				lpoints = len(points)
				lnormals = len(normals)
				lfaces = len(faces)
				annie_mesh_trace(1, "Cylinder", i, ": lpoints =", lpoints, "lnormals =", lnormals, "lfaces =", lfaces)
				for j in range(lpoints):
					point = points[j]
					x = point[0]
					y = point[1]
					z = point[2]
					print("v", x, y, z, file=ofile)
				for j in range(lnormals):
					normal = normals[j]
					x = normal[0]
					y = normal[1]
					z = normal[2]
					print("vn", x, y, z, file=ofile)
				f = 0
				face_count = 0
				while f < lfaces:
					count = faces[f]
					if count != 4:
						# these could be the cylindrical caps
						print("count != 4, count =", count)
						break
					f = f + 1
					ff = []
					for k in range(count):
						ff.append(faces[f + k])
					u = point_base + 1
					print(f'f {ff[0]+u}/{ff[0]+u}/{ff[0]+u} {ff[1]+u}/{ff[1]+u}/{ff[1]+u} {ff[2]+u}/{ff[2]+u}/{ff[2]+u} {ff[3]+u}/{ff[3]+u}/{ff[3]+u}', file=ofile)
					f = f + count
					face_count = face_count + 1
				total_face_count = total_face_count + face_count
				point_base = point_base + lpoints
		ofile.close()

	# reset tick counter
	current_tick.rx.value = 0

	t = "Merging cylinders..."
	server_response_widget.value = t

	# set number of cylinders
	ldo = len(display_objects)
	mesh.set_cylinders(ldo)
	# merge everything into one gigantic object
	print("merging")
	display_mesh = pv.merge(display_objects)
	# save as ply so open3d can read it
	print("saving ply")
	ply_file_name = data_folder + basename + ".ply"
	display_mesh.save(ply_file_name)
	ply_points = len(display_mesh.points)
	ply_faces = len(display_mesh.faces)
	print("ply_points =", ply_points, "ply_faces =", ply_faces)
	mesh.set_ply_points(ply_points)
	mesh.set_ply_faces(ply_faces)

	# done - set new status
	mesh.set_status(FILE_STATUS_CYL)
	this_mesh_index.param.trigger('value')

	# emit status
	if error_occurred == 0:
		server_response_status = f"<font color=\"green\">File converted to PLY cylinders with {vertex_count} objects and {total_face_count} faces</font>"
		button_triangulate.disabled = False
		button_deskeletonize.disabled = True
		# tickle update of the Cylinders ("cells") tab
		cell_tab_controller.param.trigger('value')
	else:
		server_response_status = f"<font color=\"red\">Error occurred: {emsg} </font>"

	server_response_widget.value = server_response_status

	return "0"

rdeskeletonize = pn.pane.Markdown(pn.bind(deskeletonize, button_deskeletonize))

#
# routine to triangulate a sampled and reconstructed OBJ
#

def triangulate(clicked):

	global meshfiles
	global CurrentMeshFile
	global data_folder

	error_occurred = 0
	emsg = ""

	annie_mesh_debug(1, "triangulate()")

	if CurrentMeshFile == None or CurrentMeshFile < 0:
		return "1"

	index = int(CurrentMeshFile)
	mesh = meshfiles[index]
	stat = mesh.get_status()
	if stat != FILE_STATUS_CYL:
		return "2"

	basename = mesh.get_basename()
	ply = data_folder + basename + ".ply"

	print("reading mesh")
	pcd = o3d.io.read_triangle_mesh(ply)
	print("sampling poisson disk")
	t = "Sampling Poisson Disk: please be patient, this takes a while..."
	server_response_widget.value = t
	pcd2 = pcd.sample_points_poisson_disk(50000)
	t = "Sampled 50000 points, computing nearest neighbors..."
	server_response_widget.value = t
	print("estimating normals")
	pcd2.estimate_normals()
	print("computing nearest neighbors")
	distances = pcd2.compute_nearest_neighbor_distance()
	avg_dist = sum(distances)/len(distances)
	t = "Generating triangle mesh..."
	server_response_widget.value = t
	print("generating triangle mesh")
	output_mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd2, depth=9)
	t = "Saving OBJ file..."
	server_response_widget.value = t
	print("saving OBJ file")
	output_name = data_folder + basename + ".obj"
	o3d.io.write_triangle_mesh(output_name, output_mesh)

	trilen = len(output_mesh.triangles)
	mesh.set_num_triangles(trilen)
	mesh.set_status(FILE_STATUS_TRI)
	this_mesh_index.param.trigger('value')

	# emit status
	if error_occurred == 0:
		server_response_status = f"<font color=\"green\">File converted to {trilen} triangles in Wavefront OBJ format</font>"
		button_cleanmesh.disabled = False
		button_triangulate.disabled = True
	else:
		server_response_status = f"<font color=\"red\">Error occurred: {emsg} </font>"

	server_response_widget.value = server_response_status

	return "0"

rtriangulate = pn.pane.Markdown(pn.bind(triangulate, button_triangulate))

#
# routine to clean up cylinders, sample mesh, and perform surface reconstruction
#

def cleanmesh(clicked):

	global meshfiles
	global CurrentMeshFile
	global data_folder

	error_occurred = 0
	emsg = ""

	annie_mesh_debug(1, "cleanmesh()")
	if CurrentMeshFile == None or CurrentMeshFile < 0:
		return "1"

	index = int(CurrentMeshFile)
	mesh = meshfiles[index]
	stat = mesh.get_status()
	if stat != FILE_STATUS_TRI:
		return "2"

	basename = mesh.get_basename()
	objfile = data_folder + basename + ".obj"

	t = "Decimating mesh..."
	server_response_widget.value = t

	# 1. read obj into pyvista (many warning will be generated)
	print("reading OBJ file")
	pvmesh = pv.read(objfile)
	pvmesh_points = len(pvmesh.points)
	pvmesh_faces = len(pvmesh.faces)
	print("pvmesh_points =", pvmesh_points, "pvmesh_faces =", pvmesh_faces)
	print("pvmesh.n_points =", pvmesh.n_points, "pvmesh.n_cells =", pvmesh.n_cells)
	print("pvmesh.is_all_triangles =", pvmesh.is_all_triangles, "pvmesh.is_manifold =", pvmesh.is_manifold)
	print("pvmesh.volume =", pvmesh.volume);

	# 2. decimate by 50%
	print("decimating mesh")
	decimated_mesh = pvmesh.decimate(target_reduction=0.5)
	print("saving decimated mesh")
	decname = data_folder + basename + "_decimated.obj"
	decimated_mesh.save(decname)

#### this takes a while

	# 3. import pyacvd, and start from original mesh
	print("remeshing")
	t = "Remeshing: please be patient, this takes a while..."
	server_response_widget.value = t
	remesh = pvmesh.acvd.remesh(100000,subdivide=3)

	# 4. save to obj
	t = "Saving as _remeshed_acvd.obj ..."
	server_response_widget.value = t
	print("saving to OBJ")
	savname = data_folder + basename + "_remeshed_acvd.obj"
	remesh.save(savname)

	mesh.set_status(FILE_STATUS_OBJ)
	this_mesh_index.param.trigger('value')

	# 5. import pymeshfix and clean
	t = "Cleaning and repairing mesh..."
	server_response_widget.value = t
	print("cleaning with PyMeshFix")
	tin = pymeshfix.PyTMesh()
	tin.load_file(savname)
	tin.clean(max_iters=10, inner_loops=3)
	outname = data_folder + basename + "_remeshed_and_cleaned.obj"
	tin.save_file(outname)

	# 6. try the quicker easier way
	t = "Saving as _remeshed_cleaned_meshfixed.obj ..."
	server_response_widget.value = t
	print("repairing and saving")
	tin2 = pv.read(outname)
	tin2_points = len(tin2.points)
	tin2_faces = len(tin2.faces)
	print("tin2_points =", tin2_points, "tin2_faces =", tin2_faces)
	print("tin2.n_points =", tin2.n_points, "tin2.n_faces =", tin2.n_faces)
	print("tin2.is_all_triangles =", tin2.is_all_triangles, "tin2.is_manifold =", tin2.is_manifold)
	print("tin2.volume =", tin2.volume)
	meshfix2 = pymeshfix.MeshFix(tin2)
	meshfix2.repair()
	cleaned_tin2 = meshfix2.mesh
	print("saving cleaned surface mesh")
	fixname = data_folder + basename + "_remeshed_cleaned_meshfixed.obj"
	print("output file name =", fixname)
	cleaned_tin2.save(fixname)
	t = "Previewing surface mesh..."
	server_response_widget.value = t
	cleaned_tin2.plot(show_edges=True)

	# 7. this file is now a very clean OBJ
	points = len(cleaned_tin2.points)
	faces = int(len(cleaned_tin2.faces) / 4)
	print("clean points =", points, "clean_faces =", faces)
	mesh.set_clean_points(points)
	mesh.set_clean_faces(faces)
	mesh.set_status(FILE_STATUS_OPT)
	this_mesh_index.param.trigger('value')

	# emit status
	if error_occurred == 0:
		server_response_status = f"<font color=\"green\">OBJ file cleaned and optimized: {points} vertices, {faces} faces</font>"
		button_tetrahedralize.disabled = False
		button_cleanmesh.disabled = True
		# tickle update of the Surface ("connections") tab
		connection_tab_controller.param.trigger('value')
	else:
		server_response_status = f"<font color=\"red\">Error occurred: {emsg} </font>"

	server_response_widget.value = server_response_status

	return "0"

rcleanmesh = pn.pane.Markdown(pn.bind(cleanmesh, button_cleanmesh))

#
# routine to tetrahedralize an OBJ
#

def tetrahedralize(clicked):

	global meshfiles
	global CurrentMeshFile
	global data_folder

	error_occurred = 0
	emsg = ""

	annie_mesh_debug(1, "tetrahedralize()")
	if CurrentMeshFile == None or CurrentMeshFile < 0:
		print("CurrentMeshFile =", CurrentMeshFile)
		return "1"

	index = int(CurrentMeshFile)
	mesh = meshfiles[index]
	stat = mesh.get_status()
	if stat != FILE_STATUS_OPT:
		print("File Status =", stat)
		return "2"

	basename = mesh.get_basename()
	objfile = data_folder + basename + "_remeshed_and_cleaned.obj"

	# 1. tetrahedralize
	t = "Tetrahedralizing ..."
	server_response_widget.value = t
	print("tetrahedralizing")
	new_mesh = pv.read(objfile)
	# new_mesh now contains the FINAL OBJ COUNTS
	new_points = len(new_mesh.points)
	new_faces = len(new_mesh.faces)
	# should be the same as clean_points and clean_faces, but this
	# is now a tet mesh so we have to decipher the faces array
	print("new_points =", new_points, "new_faces =", new_faces)
	print("new_mesh.n_points =", new_mesh.n_points, "new_mesh.n_cells =", new_mesh.n_cells)
	print("new_mesh.is_all_triangles =", new_mesh.is_all_triangles, "new_mesh.is_manifold =", new_mesh.is_manifold)
	print("new_mesh.volume =", new_mesh.volume)
	# generate the TET mesh
	tet = tetgen.TetGen(new_mesh)
	tet.tetrahedralize(order=1, mindihedral=20, minratio=1.5, edgesout=True, facesout=True)
	num_edges = len(tet.edges)
	print("num_edges =", num_edges)
	num_elems = len(tet.elem)
	print("num_elems =", num_elems)
	num_nodes = len(tet.node)
	print("num_nodes =", num_nodes)
	num_faces = len(tet.trifaces)
	print("num_faces =", num_faces)

	mesh.set_tet_nodes(num_nodes)
	mesh.set_tet_elems(num_elems)
	mesh.set_tet_edges(num_edges)
	mesh.set_tet_faces(num_faces)

	mesh.set_status(FILE_STATUS_TET)
	this_mesh_index.param.trigger('value')

	# 2. extract grid
	print("extracting grid")
	grid = tet.grid
	npoints = len(grid.points)
	# nfaces = len(grid.faces)
	print("npoints =", npoints)	# should equal num_nodes

	# 3. save as vtu
	t = "Saving tetrahedral mesh as VTU and GLTF..."
	server_response_widget.value = t
	print("saving to VTU")
	vtuname = data_folder + basename + ".vtu"
	grid.save(vtuname)
	gpoints = len(grid.points)
	print("gpoints =", gpoints)	# should equal num_nodes

	# 4. save the grid from the tet-mesh to GLTF
	print("saving to GLTF")
	plotter = pv.Plotter()
	plotter.add_mesh(grid)
	gltfname = data_folder + basename + ".gltf"
	plotter.export_gltf(gltfname)

	# emit status
	if error_occurred == 0:
		server_response_status = f"<font color=\"green\">Tetrahedral mesh saved in VTU and GLTF formats</font>"
		button_voxelize.disabled = False
		button_tetrahedralize.disabled = True
		# tickle update of the Volume ("synapses") tab
		synapse_tab_controller.param.trigger('value')
	else:
		server_response_status = f"<font color=\"red\">Error occurred: {emsg} </font>"

	server_response_widget.value = server_response_status

	return "0"

rtetrahedralize = pn.pane.Markdown(pn.bind(tetrahedralize, button_tetrahedralize))

#
# routine to voxelize an OBJ
#

def voxelize(clicked):

	global meshfiles
	global CurrentMeshFile
	global data_folder

	error_occurred = 0
	emsg = ""

	annie_mesh_debug(1, "voxelize()")
	if CurrentMeshFile == None or CurrentMeshFile < 0:
		print("CurrentMeshFile =", CurrentMeshFile)
		return "1"

	index = int(CurrentMeshFile)
	mesh = meshfiles[index]
	stat = mesh.get_status()
	if stat != FILE_STATUS_TET:
		print("File Status =", stat)
		return "2"

	basename = mesh.get_basename()
	objfile = data_folder + basename + "_remeshed_and_cleaned.obj"

	# 1. voxelize
	t = "Voxelizing: please be patient, this takes a while..."
	server_response_widget.value = t
	print("voxelizing")
	new_mesh = pv.read(objfile)
	# new_mesh now contains the FINAL OBJ COUNTS
	new_points = len(new_mesh.points)
	new_faces = len(new_mesh.faces)
	# should be the same as clean_points and clean_faces, but this
	# is now a tet mesh so we have to decipher the faces array
	print("new_points =", new_points, "new_faces =", new_faces)
	# generate the voxelized volume
	voxels = new_mesh.voxelize(spacing=0.05)
	voxels.plot(show_edges=True)

	print("voxels.n_cells =", voxels.n_cells)
	mesh.set_voxels(voxels.n_cells)

	# mesh.set_status(FILE_STATUS_VOX)
	# this_mesh_index.param.trigger('value')

	# save as voxelized file
	voxname = data_folder + basename + "_voxels.vtk"
	voxels.save(voxname)
	vouname = data_folder + basename + "_voxels.vtu"
	voxels.save(vouname)

	# 4. save the grid from the tet-mesh to GLTF
	print("saving to GLTF")
	plotter = pv.Plotter()
	plotter.add_mesh(voxels)
	gltfname = data_folder + basename + "_voxels.gltf"
	plotter.export_gltf(gltfname)

	# 5. all done converting this file
	mesh.set_status(FILE_STATUS_DONE)
	this_mesh_index.param.trigger('value')

	# emit status
	if error_occurred == 0:
		server_response_status = f"<font color=\"green\">Voxelized mesh saved in VTU/VTK and GLTF formats</font>"
		button_voxelize.disabled = True
		# tickle update of the Voxels ("probes") tab
		probe_tab_controller.param.trigger('value')
		# tickle update of the Statistics ("templates") tab
		template_tab_controller.param.trigger('value')
	else:
		server_response_status = f"<font color=\"red\">Error occurred: {emsg} </font>"

	server_response_widget.value = server_response_status

	return "0"

rvoxelize = pn.pane.Markdown(pn.bind(voxelize, button_voxelize))

#
# routines for output
#

def output_savehdf5(clicked):
	annie_mesh_debug(1, "output_savehdf5")
	return "0"

rsavehdf5 = pn.pane.Markdown(pn.bind(output_savehdf5, button_savehdf5))

#
# display the template
#

pn.template.MaterialTemplate(site="",title="Annie - SWC Converter", sidebar=[left_sidebar], sidebar_width=330, main=[main_box],).servable()

#
# set up trace and debug files
#

trace_file_handle = open(annie_swc_config.CLIENT_HOME_DIR + "annie_swc_trace.txt", "w")
debug_file_handle = open(annie_swc_config.CLIENT_HOME_DIR + "annie_swc_debug.txt", "w")

annie_mesh_trace(1, "ANNIE SWC v0.1")
annie_mesh_debug(1, "ANNIE SWC v0.1")

server_response_widget.value = '<font color="green">Ready</font>'

button_open_obj.disabled = True
button_savehdf5.disabled = True

button_verify.disabled = True
button_deskeletonize.disabled = True
button_triangulate.disabled = True
button_cleanmesh.disabled = True
button_tetrahedralize.disabled = True
button_voxelize.disabled = True

data_folder = annie_swc_config.CLIENT_DATA_DIR

