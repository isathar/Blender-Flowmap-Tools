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
	"version": (0, 0, 1),
	"blender": (2, 74, 0),
	"location": "View3D > Toolbar",
	"description": "Editing tools for flowmaps",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "https://github.com/isathar/Blender-Flowmap-Tools/issues",
	"category": "Mesh"}


import bpy
from mathutils import Vector


# UI Panel
class flowmaps_editor_panel(bpy.types.Panel):
	bl_idname = "view3D.flowmaps_editor_panel"
	bl_label = 'Flowmap Editor'
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'TOOLS'
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
		box.row().operator('object.create_flowmap_field',text='Create')
		box.row().operator('object.calc_flowmap_velocicites',text='Calculate')
		box.row().operator('object.blur_flowmap_field',text='Blur')
		
		

# creates particle system on selected plane to represent flowmap vectors
class create_flowmap_field(bpy.types.Operator):
	bl_idname = 'object.create_flowmap_field'
	bl_label = 'Create Flowmap Particles'
	bl_description = 'Turn plane into flowfield'
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return (context.mode == "OBJECT" and context.active_object != None)
	
	def execute(self, context):
		flowmesh = context.active_object
		numverts = len(flowmesh.data.vertices)
		
		bpy.ops.object.particle_system_add()
		psettings = context.active_object.particle_systems[0].settings
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
		
		return {'FINISHED'}


# calculates velocities and saves them to vertex colors
class calc_flowmap_velocicites(bpy.types.Operator):
	bl_idname = 'object.calc_flowmap_velocicites'
	bl_label = 'Calculate Flow'
	bl_description = 'Calculate and save velocities'
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return (context.mode == "OBJECT" and context.active_object != None) and len(context.active_object.data.particle_systems) > 0
	
	def execute(self, context):
		flowmesh = context.active_object

		particleslist = [p.velocity for p in flowmesh.particle_systems[0].particles]

		newlayer = None

		if len(flowmesh.data.vertex_colors) < 1:
			bpy.ops.mesh.vertex_color_add()
			newlayer = flowmesh.data.vertex_colors[len(flowmesh.data.vertex_colors) - 1]
			newlayer.name = 'flow'
		else:
			newlayer = flowmesh.data.vertex_colors['flow']

		finalvlist = [Vector([0.0,0.0,0.0]) for l in flowmesh.data.loops]

		for i in range(len(flowmesh.data.loops)):
			finalvlist[i] = particleslist[flowmesh.data.loops[i].vertex_index]

		if newlayer != None:
			for i in range(len(finalvlist)):
				newlayer.data[i].color = (finalvlist[i] + Vector([1.0,1.0,1.0])) / 2.0

		return {'FINISHED'}


# creates particle system on selected plane to represent flowmap vectors
class blur_flowmap_field(bpy.types.Operator):
	bl_idname = 'object.blur_flowmap_field'
	bl_label = 'Blur Flowmap'
	bl_description = 'Blurs the directions of the flowmap by averaging surrounding velocities'
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return (context.mode == "OBJECT" and context.active_object != None)
	
	def execute(self, context):
		flowmesh = context.active_object
		
		maxradius = 1.0
		intensity = 0.5
		
		vindex = [v.vertex_index for v in flowmesh.data.loops]
		vlist = [v.co for v in flowmesh.data.vertices]
		
		particleslist_unproc = [p.velocity.copy() for p in flowmesh.particle_systems[0].particles]
		particleslist_proc = [p.velocity.copy() for p in flowmesh.particle_systems[0].particles]
		
		curavglist = []
		tempv = Vector([0.0,0.0,0.0])
		
		for j in range(len(vindex)):
			v1 = vlist[vindex[j]]
			
			for i in range(len(vlist)):
				curdistv = v1 - vlist[i]
				curdist = curdistv.magnitude
				if curdist <= maxradius:
					curavglist.append(particleslist_unproc[i])
			
			if len(curavglist) > 0:
				for v in curavglist:
					tempv = tempv + v
				tempv = tempv / float(len(curavglist))
				particleslist_proc[vindex[j]] = tempv.copy()
			
			curavglist.clear()
			tempv.zero()
			
		newlayer = flowmesh.data.vertex_colors['flow']
		if newlayer != None:
			for i in range(len(newlayer.data)):
				newlayer.data[i].color = (particleslist_proc[vindex[i]] + Vector([1.0,1.0,1.0])) / 2.0
		
		return {'FINISHED'}



def register():
	bpy.utils.register_class(flowmaps_editor_panel)
	
	bpy.utils.register_class(create_flowmap_field)
	bpy.utils.register_class(calc_flowmap_velocicites)
	bpy.utils.register_class(blur_flowmap_field)
	
	#initdefaults()

def unregister():
	bpy.utils.unregister_class(flowmaps_editor_panel)
	
	bpy.utils.unregister_class(create_flowmap_field)
	bpy.utils.unregister_class(calc_flowmap_velocicites)
	bpy.utils.unregister_class(blur_flowmap_field)
	
	#clearvars(bpy)


#def initdefaults(bpy):
#	#  


#def clearvars(bpy):
#	#  



if __name__ == '__main__':
	register()
