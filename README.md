# Blender-Flowmap-Tools
A very WIP flowmap creator/editor for Blender.  (up to v.2.79 - needs to be updated for 2.8)
 
 
Initial testing release - more features and instructions coming soon.
 
------------------------------------------------------------------
 
*Installation:* 
 
- extract to your Blender addons directory  
 
---------------------------------------------------------------
 
*Basic Usage:* 
 
The UI panel is in the Particle Simulation tab. 
 
- Duplicate the mesh you want to create a flowmap for (or a basic plane for tiling water textures)
  - Note: the mesh needs UVs to be able to bake the flowmap to texture
- Subdivide the copy a few times for more particles in the flow simulation
- Click *Create Data* in the UI panel with the new mesh selected. This creates the particle system.
  
- Add any force fields you want to influence the flow simulation
  - ex. any places that the flow will be diverted at, low-range wind forces at the edges to simulate a shore, etc
- select the frame of the simulation you want to get velocities from  
  
- To calculate the velocities for the flowmap:
  - Click Calc Direction to use the amount by which each particle moved between frame 0 and the current frame
  - (or) Calc Forces to use each particle's actual velocity in this frame
  - (Calc Geometry does nothing for now)
  - This will create a new vertex color layer called "flow"  
  
- Use Blender's Bake feature to bake the vertex colors to a texture 
- Save the image from UV view.  
 
 
- The resulting flowmap is packed in the same way a normal map would be, so the values will have to be converted in the engine you're using.
  - UDK and Unreal Engine 4 - using Unpack Min setting if -1.0 (rgb) works. 
  
------------------------------------------------------------------------

*Changelog:* 
 
v0.0.1 Current: 
  - initial release
 
