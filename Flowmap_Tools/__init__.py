# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
	"name": "Flowmap Tools",
	"author": "Andreas Wiehn (isathar)",
	"version": (0, 0, 5),
	"blender": (2, 74, 0),
	"location": "View3D > Toolbar",
	"description": "Editing tools for flowmaps",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "https://github.com/isathar/Blender-Flowmap-Tools/issues",
	"category": "Mesh"}


flow_startlocs = []
flow_vindex = []

flow_directions = []
flow_velocities = []
flow_geominf = []

def clear_flowmapdata(context):
	del flow_directions[:]
	del flow_velocities[:]
	del flow_geominf[:]
	del flow_vindex[:]
	del flow_startlocs[:]


import bpy
from mathutils import Vector

#classes = (
#    FooClass,
#    BarClass,
#    BazClass,
#)

# UI Panel
class flowmaps_editor_panel(bpy.types.Panel):
	bl_idname = "FLOWMAPS_PT_EditorPanel"
	bl_label = 'Flowmap Editor'
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Particle Simulation"
	
	@classmethod
	def poll(self, context):
		if context.active_object != None:
			if context.active_object.type == 'MESH':
				return True
		return False
	
	def draw(self, context):
		# Create
		layout = self.layout
		box = layout.box()
		box.row().operator('object.create_vectorfield_2d',text='Create Data')
		
		box2 = layout.box()
		box = box2.box()
		box.row().operator('object.calc_flowmap_dir',text='Calc Direction')
		box.row().prop(context.window_manager, 'flowmap_cache0weight',text='Weight')
		
		box = box2.box()
		box.row().operator('object.calc_flowmap_velocities',text='Calc Forces')
		box.row().prop(context.window_manager, 'flowmap_cache1weight',text='Weight')
		
		box = box2.box()
		box.row().operator('object.calc_flowmap_geometry',text='Calc Geometry')
		box.row().prop(context.window_manager, 'flowmap_cache2weight',text='Weight')
		
		box = layout.box()
		box.row().prop(context.window_manager, 'flowmap_usebchan',text='Blue Channel')
		box.row().operator('object.flowmap_writetocolor',text='Write to Color')
		
		
		


## Init ####################################################

def get_nearest_vindex(tempverts, checkloc):
	lastdist = 8192.0
	curindex = -1
	
	for i in range(len(tempverts)):
		testmag = (tempverts[i] - checkloc).magnitude
		if testmag <= lastdist:
			lastdist = testmag
			curindex = i
	return curindex

# creates particle system in selected object to represent flowmap vectors
class create_vectorfield_2d(bpy.types.Operator):
	bl_idname = 'object.create_vectorfield_2d'
	bl_label = 'Create Flowmap Data'
	bl_description = 'Create flow particles for selected object'
	bl_options = {'REGISTER', 'UNDO'}
	
	@classmethod
	def poll(cls, context):
		return (context.mode == "OBJECT" and context.active_object != None)
	
	def execute(self, context):
		flowmesh = context.active_object
		numverts = len(flowmesh.data.vertices)
		tempvlocs = [(v.co).copy() for v in flowmesh.data.vertices]
		
		bpy.ops.object.particle_system_add()
		psettings = flowmesh.particle_systems[0].settings
		psettings.count = numverts
		psettings.emit_from = 'VERT'
		psettings.normal_factor = 0.0
		psettings.use_emit_random = False
		psettings.frame_end = 1
		psettings.lifetime = 32
		psettings.grid_resolution = 1
		psettings.use_rotations = True
		psettings.use_dynamic_rotation = True
		psettings.effector_weights.gravity = 0.0
		
		flowmesh.particle_systems[0].point_cache.name = 'ForceFlow'
		
		context.area.tag_redraw()
		bpy.context.view_layer.update()
		
		flow_startlocs = [(p.location).copy() for p in flowmesh.particle_systems[0].particles]
		flow_vindex = [get_nearest_vindex(tempvlocs, v) for v in flow_startlocs]
		
		mat = bpy.data.materials.new('flowmat')
		
		#
		mat.use_nodes = True
		
		nodes = mat.node_tree.nodes
		links = mat.node_tree.links
		
		nodes.clear()
		links.clear()
		
		node_output = nodes.new('ShaderNodeOutputMaterial')
		node_diffuse = nodes.new('ShaderNodeBsdfDiffuse')
		node_attr = nodes.new('ShaderNodeAttribute')	
		node_attr.attribute_name = "vertex_color_block_flow"
		
		link_diffuse_to_output = links.new(node_diffuse.outputs['BSDF'], node_output.inputs['Surface'])
		link_color_to_diffuse = links.new(node_attr.outputs['Color'], node_diffuse.inputs['Color'])
		flowmesh.active_material = mat
		
		del tempvlocs[:]
		
		return {'FINISHED'}



## Calc ####################################################

# Base (Painted directions)
class calc_flowmap_dir(bpy.types.Operator):
	bl_idname = 'object.calc_flowmap_dir'
	bl_label = 'Base Flow'
	bl_description = 'Get base directional flow'
	bl_options = {'REGISTER', 'UNDO'}
	
	@classmethod
	def poll(cls, context):
		if (context.mode == "OBJECT" and context.active_object != None):
			if context.active_object.particle_systems:
				return len(context.active_object.particle_systems) > 0
		return False
	
	def execute(self, context):
		flowmesh = context.active_object
		pscurlocs = [(p.location).copy() for p in flowmesh.particle_systems[0].particles]
		
		flow_directions = []
		for i in range(len(flow_startlocs)):
			flow_directions.append(pscurlocs[i] - flow_startlocs[i])
		
		return {'FINISHED'}


# Forces (flow velocities influenced by force fields)
class calc_flowmap_velocities(bpy.types.Operator):
	bl_idname = 'object.calc_flowmap_velocities'
	bl_label = 'Force Flow'
	bl_description = 'Get flow influenced by forces'
	bl_options = {'REGISTER', 'UNDO'}
	
	@classmethod
	def poll(cls, context):
		if (context.mode == "OBJECT" and context.active_object != None):
			if context.active_object.particle_systems:
				return len(context.active_object.particle_systems) > 0
		return False
	
	def execute(self, context):
		flowmesh = context.active_object
		flow_velocities = [(p.velocity).copy() for p in flowmesh.particle_systems[0].particles]
		
		return {'FINISHED'}


# Geometry (flow velocities influenced by level geometry)
class calc_flowmap_geometry(bpy.types.Operator):
	bl_idname = 'object.calc_flowmap_geometry'
	bl_label = 'Geometry Flow'
	bl_description = 'Get flow influenced by surrounding geometry'
	bl_options = {'REGISTER', 'UNDO'}
	
	@classmethod
	def poll(cls, context):
		if (context.mode == "OBJECT" and context.active_object != None):
			if context.active_object.particle_systems:
				return len(context.active_object.particle_systems) > 0
		return False
	
	def execute(self, context):
		flowmesh = context.active_object
		
		# 	for each selected mesh
		#		flocnorms = get faces [loc + normal]
		#		for each influenced particle
		#			get faces in influencedistance
		#			average newv and weighted face normal
		
		return {'FINISHED'}



## Write ####################################################

# combine flow influences + write to vertex color layer
class flowmap_writetocolor(bpy.types.Operator):
	bl_idname = 'object.flowmap_writetocolor'
	bl_label = 'Write VColors'
	bl_description = 'Write flowmap data to vertex color layer'
	bl_options = {'REGISTER', 'UNDO'}
	
	@classmethod
	def poll(cls, context):
		if (context.mode == "OBJECT" and context.active_object != None):
			if context.active_object.particle_systems:
				return len(context.active_object.particle_systems) > 0
		return False
	
	def execute(self, context):
		flowmesh = context.active_object
		flowmeshloops = [f for f in flowmesh.data.loops]
		loopslen = len(flowmeshloops)
		finalvlist = [Vector([0.0,0.0,0.0]) for l in flowmeshloops]
		newlayer = None
		
		c0weight = context.window_manager.flowmap_cache0weight
		c1weight = context.window_manager.flowmap_cache1weight
		c2weight = context.window_manager.flowmap_cache2weight
		
		# direction
		if c0weight > 0.0:
			if len(flow_directions) > 0:
				for i in range(len(flow_vindex)):
					for j in range(len(flowmeshloops)):
						if flowmeshloops[j].vertex_index == flow_vindex[i]:
							finalvlist[j] = flow_directions[i] * c0weight
		
		# forces
		if c1weight > 0.0:
			if len(flow_velocities) > 0:
				for i in range(len(flow_vindex)):
					for j in range(len(flowmeshloops)):
						if flowmeshloops[j].vertex_index == flow_vindex[i]:
							finalvlist[j] = finalvlist[j] + (flow_velocities[i] * c1weight)
		
		# geometry
		if c2weight > 0.0:
			if len(flow_geominf) > 0:
				for i in range(len(flow_vindex)):
					for j in range(len(flowmeshloops)):
						if flowmeshloops[j].vertex_index == flow_vindex[i]:
							finalvlist[j] = finalvlist[j] + (flow_geominf[i] * c2weight)
		
		for v in finalvlist:
			if v.magnitude > 0.0:
				v = v.normalized()
		
		# check if vertex color layer exists, create one if not
		if len(flowmesh.data.vertex_colors) < 1:
			bpy.ops.mesh.vertex_color_add()
			newlayer = flowmesh.data.vertex_colors[len(flowmesh.data.vertex_colors) - 1]
			newlayer.name = 'vertex_color_block_flow'
		else:
			newlayer = flowmesh.data.vertex_colors['vertex_color_block_flow']
		
		# convert + write vertex colors
		if newlayer != None:
			if context.window_manager.flowmap_usebchan:
				for i in range(len(finalvlist)):
					newlayer.data[i].color = (finalvlist[i] + Vector([1.0,1.0,1.0])) / 2.0
			else:
				for i in range(len(finalvlist)):
					newlayer.data[i].color = (finalvlist[i] + Vector([1.0,1.0,0.0])) / 2.0
					newlayer.data[i].color[2] = 0.0
		
		return {'FINISHED'}
		

## PP ######################################################

# blur existing flowmap
class flowmap_pp_blur(bpy.types.Operator):
	bl_idname = 'object.flowmap_pp_blur'
	bl_label = 'Smooth'
	bl_description = 'Blur current velocity lists'
	bl_options = {'REGISTER', 'UNDO'}
	
	@classmethod
	def poll(cls, context):
		if (context.mode == "OBJECT" and context.active_object != None):
			if context.active_object.particle_systems:
				return len(context.active_object.particle_systems) > 0
		return False
	
	def execute(self, context):
		return {'FINISHED'}



#######################################################################

def initdefaults():
	bpy.types.WindowManager.flowmap_usebchan = bpy.props.BoolProperty(
		default=False,description="Use blue channel (height)"
	)
	bpy.types.WindowManager.flowmap_cache0weight = bpy.props.FloatProperty(
		default=0.5,min=0.0,max=1.0,
		description="Weight of directional flow in final calculation"
	)
	bpy.types.WindowManager.flowmap_cache1weight = bpy.props.FloatProperty(
		default=0.25,min=0.0,max=1.0,
		description="Weight of forces in final calculation"
	)
	bpy.types.WindowManager.flowmap_cache2weight = bpy.props.FloatProperty(
		default=0.25,min=0.0,max=1.0,
		description="Weight of geometry influence in final calculation"
	)


def clearvars():
	props = [
		'flowmap_usebchan','flowmap_cache0weight','flowmap_cache1weight','flowmap_cache2weight'
	]
	
	for p in props:
		if bpy.context.window_manager.get(p) != None:
			del bpy.context.window_manager[p]
		try:
			x = getattr(bpy.types.WindowManager, p)
			del x
		except:
			pass
	
	clear_flowmapdata(context)


def register():
	initdefaults()
	
	bpy.utils.register_class(flowmaps_editor_panel)
	
	bpy.utils.register_class(create_vectorfield_2d)
	
	bpy.utils.register_class(calc_flowmap_dir)
	bpy.utils.register_class(calc_flowmap_velocities)
	bpy.utils.register_class(calc_flowmap_geometry)
	
	bpy.utils.register_class(flowmap_writetocolor)
	
	
	
	

def unregister():
	bpy.utils.unregister_class(flowmaps_editor_panel)
	
	bpy.utils.unregister_class(create_vectorfield_2d)
	
	bpy.utils.unregister_class(calc_flowmap_dir)
	bpy.utils.unregister_class(calc_flowmap_velocities)
	bpy.utils.unregister_class(calc_flowmap_geometry)
	
	bpy.utils.unregister_class(flowmap_writetocolor)
	
	clearvars()
	

if __name__ == '__main__':
	register()
