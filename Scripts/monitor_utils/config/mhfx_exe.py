'''
For Menhir FX
author:
Angele Sionneau - asionneau@artfx.fr
'''

maya_exe =  ['maya.exe',]
houdini_exe = ['houdini.exe', 'houdinicore.exe', 'houdinifx.exe',]
photoshop_exe =  ['Photoshop.exe',]
substance_p_exe = ['Adobe Substance 3D Painter.exe',]
substance_d_exe = ['Adobe Substance 3D Designer.exe',]
after_exe = ['AfterFX.exe',]
premier_exe = ['Adobe Premiere Pro.exe',]
nuke_exe = ['Nuke13.2.exe', 'Nuke14.0.exe', ]
blender_exe = ['blender.exe',]
unreal_exe = ['UnrealEditor.exe',]

executables = {
    '.ma': maya_exe,
    '.mb': maya_exe,
    '.hip': houdini_exe,
    '.hiplc': houdini_exe,
    '.psd' : photoshop_exe,
    '.spp': substance_p_exe,
    '.aep': after_exe,
    '.prproj': premier_exe,
    '.nk': nuke_exe,
    '.blend' : blender_exe,
    '.uproject': unreal_exe,
    '.sbs': substance_d_exe

} # association file extension -> executable