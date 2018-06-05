import bpy

from .enums import *


###############################
## Material
###############################

class WowM2MaterialPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
    bl_label = "M2 Material"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label('Flags:')
        col.prop(context.material.WowM2Material, "Flags")
        col.separator()
        col.label('Render Flags:')
        col.prop(context.material.WowM2Material, "RenderFlags")
        col.separator()
        col.prop(context.material.WowM2Material, "BlendingMode")
        col.prop(context.material.WowM2Material, "Shader")

    @classmethod
    def poll(cls, context):
        return(context.scene is not None
               and context.scene.WowScene.Type == 'M2'
               and context.material is not None)


class WowM2MaterialPropertyGroup(bpy.types.PropertyGroup):

    Flags = bpy.props.EnumProperty(
        name="Material flags",
        description="WoW  M2 material flags",
        items=TEX_UNIT_FLAGS,
        options={"ENUM_FLAG"}
        )

    RenderFlags = bpy.props.EnumProperty(
        name="Render flags",
        description="WoW  M2 render flags",
        items=RENDER_FLAGS,
        options={"ENUM_FLAG"}
        )

    Shader = bpy.props.EnumProperty(
        items=SHADERS,
        name="Shader",
        description="WoW shader assigned to this material"
        )

    BlendingMode = bpy.props.EnumProperty(
        items=BLENDING_MODES,
        name="Blending",
        description="WoW material blending mode"
        )


def register_wow_m2_material_properties():
    bpy.types.Material.WowM2Material = bpy.props.PointerProperty(type=WowM2MaterialPropertyGroup)


def unregister_wow_m2_material_properties():
    bpy.types.Material.WowM2Material = None


###############################
## Geoset
###############################

class M2GeosetPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_label = "M2 Geoset"

    def draw(self, context):
        self.layout.prop(context.object.WowM2Geoset, "CollisionMesh")

        if not context.object.WowM2Geoset.CollisionMesh:
            self.layout.prop(context.object.WowM2Geoset, "MeshPartGroup")
            self.layout.prop(context.object.WowM2Geoset, "MeshPartID")

            row = self.layout.row(align=True)
            row.prop(context.object.WowM2Geoset, "UVTransform")
            row.operator("scene.wow_m2_geoset_add_texture_transform", text='', icon='RNA_ADD')

            row = self.layout.row()
            row.enabled = context.object.WowM2Geoset.UseColor
            row.prop(context.object.WowM2Geoset, "Color")

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.WowScene.Type == 'M2'
                and context.object is not None
                and context.object.data is not None
                and isinstance(context.object.data, bpy.types.Mesh))


def update_geoset_uv_transform(self, context):
    c_obj = context.object.WowM2Geoset.UVTransform

    uv_transform = context.object.modifiers.get('M2TexTransform')

    if c_obj:
        if not c_obj.WowM2TextureTransform.Enabled:
            context.object.WowM2Geoset.UVTransform = None

        if not uv_transform:
            bpy.ops.object.modifier_add(type='UV_WARP')
            uv_transform = context.object.modifiers[-1]
            uv_transform.name = 'M2TexTransform'
            uv_transform.object_from = context.object
            uv_transform.object_to = c_obj
            uv_transform.uv_layer = 'UVMap'
        else:
            uv_transform.object_to = c_obj

    elif uv_transform:
        context.object.modifiers.remove(uv_transform)


class WowM2GeosetPropertyGroup(bpy.types.PropertyGroup):
    CollisionMesh = bpy.props.BoolProperty(
        name='Collision mesh',
        default=False
    )

    MeshPartGroup = bpy.props.EnumProperty(
        name="Geoset group",
        description="Group of this geoset",
        items=MESH_PART_TYPES
    )

    MeshPartID = bpy.props.EnumProperty(
        name="Geoset ID",
        description="Mesh part ID of this geoset",
        items=mesh_part_id_menu
    )

    UVTransform = bpy.props.PointerProperty(
        name="UV Transform",
        type=bpy.types.Object,
        poll=lambda self, obj: obj.WowM2TextureTransform.Enabled,
        update=update_geoset_uv_transform
    )

    UseColor = bpy.props.BoolProperty(
        name='Use color',
        description='Use coloring on this model'
    )

    Color = bpy.props.FloatVectorProperty(
        name="Emissive Color",
        description='Coloring used on this M2 object. Can be animated, alpha defines visibility and is multiplied with global transparency',
        subtype='COLOR',
        default=(1, 1, 1, 1),
        size=4,
        min=0.0,
        max=1.0
    )


class WowM2Geoset_AddTextureTransform(bpy.types.Operator):
    bl_idname = 'scene.wow_m2_geoset_add_texture_transform'
    bl_label = 'Add new UV transform controller'
    bl_options = {'REGISTER', 'INTERNAL'}

    anim_index = bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object
        bpy.ops.object.empty_add(type='SINGLE_ARROW', location=(0, 0, 0))
        c_obj = bpy.context.scene.objects.active
        c_obj.name = "TT_Controller"
        c_obj.WowM2TextureTransform.Enabled = True
        c_obj = bpy.context.scene.objects.active
        c_obj.rotation_mode = 'QUATERNION'
        c_obj.empty_draw_size = 0.5
        c_obj.animation_data_create()
        c_obj.animation_data.action_blend_type = 'ADD'

        obj.WowM2Geoset.UVTransform = c_obj
        bpy.context.scene.objects.active = obj

        return {'FINISHED'}


def register_wow_m2_geoset_properties():
    bpy.types.Object.WowM2Geoset = bpy.props.PointerProperty(type=WowM2GeosetPropertyGroup)


def unregister_wow_m2_geoset_properties():
    bpy.types.Object.WowM2Geoset = None


###############################
## Texture
###############################

class WowM2TexturePanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "texture"
    bl_label = "M2 Texture"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(context.texture.WowM2Texture, "Flags")
        col.separator()
        col.prop(context.texture.WowM2Texture, "TextureType")

        if context.texture.WowM2Texture.TextureType == '0':
            col.separator()
            col.prop(context.texture.WowM2Texture, "Path", text='Path')

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.WowScene.Type == 'M2'
                and context.texture is not None)


class WowM2TexturePropertyGroup(bpy.types.PropertyGroup):

    Flags = bpy.props.EnumProperty(
        name="Texture flags",
        description="WoW  M2 texture flags",
        items=TEXTURE_FLAGS,
        options={"ENUM_FLAG"},
        default={'1', '2'}
        )

    TextureType = bpy.props.EnumProperty(
        name="Texture type",
        description="WoW  M2 texture type",
        items=TEXTURE_TYPES
        )

    Path = bpy.props.StringProperty(
        name='Path',
        description='Path to .blp file in wow file system.'
    )


def register_wow_m2_texture_properties():
    bpy.types.ImageTexture.WowM2Texture = bpy.props.PointerProperty(type=WowM2TexturePropertyGroup)


def unregister_wow_m2_texture_properties():
    bpy.types.ImageTexture.WowM2Texture = None


###############################
## Light
###############################

class WowM2LightPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"
    bl_label = "M2 Light"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(context.object.data.WowM2Light, "Type")
        col.prop(context.object.data.WowM2Light, "AmbientColor")
        col.prop(context.object.data.WowM2Light, "AmbientIntensity")
        col.prop(context.object.data.WowM2Light, "DiffuseColor")
        col.prop(context.object.data.WowM2Light, "DiffuseIntensity")
        col.prop(context.object.data.WowM2Light, "AttenuationStart")
        col.prop(context.object.data.WowM2Light, "AttenuationEnd")
        col.prop(context.object.data.WowM2Light, "Enabled")

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.WowScene.Type == 'M2'
                and context.object is not None
                and context.object.type == 'LAMP')


def update_lamp_type(self, context):
    context.object.data.type = 'POINT' if int(context.object.data.WowM2Light.Type) else 'SPOT'


class WowM2LightPropertyGroup(bpy.types.PropertyGroup):
    Type = bpy.props.EnumProperty(
        name="Type",
        description="WoW  M2 light type",
        items=[('0', 'Directional', 'Login screen only'), ('1', 'Point', '')],
        default='1',
        update=update_lamp_type
        )

    AmbientColor = bpy.props.FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        default=(1, 1, 1),
        min=0.0,
        max=1.0
    )

    AmbientIntensity = bpy.props.FloatProperty(
        name="Ambient intensity",
        description="Ambient intensity of the light",
        default=1.0,
        min=0.0,
        max=1.0
    )

    DiffuseColor = bpy.props.FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        default=(1, 1, 1),
        min=0.0,
        max=1.0
    )

    DiffuseIntensity = bpy.props.FloatProperty(
        name="Diffuse intensity",
        description="Diffuse intensity of the light",
        default=1.0,
        min=0.0,
        max=1.0
    )

    AttenuationStart = bpy.props.FloatProperty(
        name="Attenuation start",
        description="Start of attenuation",
        min=0.0    # TODO: max / default?
    )

    AttenuationEnd = bpy.props.FloatProperty(
        name="Attenuation end",
        description="End of attenuation",
        min=0.0  # TODO: max / default?
    )

    Enabled = bpy.props.BoolProperty(
        name='Enabled',
        default=True
    )


def register_wow_m2_light_properties():
    bpy.types.Lamp.WowM2Light = bpy.props.PointerProperty(type=WowM2LightPropertyGroup)


def unregister_wow_m2_light_properties():
    bpy.types.Lamp.WowM2Light = None
    
    
###############################
## Bone
###############################

class WowM2BonePanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "bone"
    bl_label = "M2 Bone"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(context.edit_bone.WowM2Bone, "KeyBoneID")
        col.separator()
        col.prop(context.edit_bone.WowM2Bone, "Flags")

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.WowScene.Type == 'M2'
                and context.edit_bone is not None)


class WowM2BonePropertyGroup(bpy.types.PropertyGroup):
    KeyBoneID = bpy.props.EnumProperty(
        name="Keybone",
        description="WoW bone keybone ID",
        items=get_keybone_ids
    )

    Flags = bpy.props.EnumProperty(
        name="Bone flags",
        description="WoW bone flags",
        items=BONE_FLAGS,
        options={"ENUM_FLAG"}
        )
    

def register_wow_m2_bone_properties():
    bpy.types.EditBone.WowM2Bone = bpy.props.PointerProperty(type=WowM2BonePropertyGroup)


def unregister_wow_m2_bone_properties():
    bpy.types.EditBone.WowM2Bone = None


###############################
## Attachments
###############################


class WowM2AttachmentPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_label = "M2 Attachment"

    def draw_header(self, context):
        self.layout.prop(context.object.WowM2Attachment, "Enabled", text="")

    def draw(self, context):
        layout = self.layout
        layout.enabled = context.object.WowM2Attachment.Enabled

        col = layout.column()
        col.prop(context.object.WowM2Attachment, 'Type', text="Type")
        col.prop(context.object.WowM2Attachment, 'Animate', text="Animate")

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.WowScene.Type == 'M2'
                and context.object is not None
                and context.object.type == 'EMPTY'
                and not (context.object.WowM2Event.Enabled or context.object.WowM2TextureTransform.Enabled)
        )


class WowM2AttachmentPropertyGroup(bpy.types.PropertyGroup):

    Enabled = bpy.props.BoolProperty(
        name='Enabled',
        description='Enabled this object to be a WoW M2 attachment point',
        default=False
    )

    Type = bpy.props.EnumProperty(
        name="Type",
        description="WoW Attachment Type",
        items=get_attachment_types
    )

    Animate = bpy.props.BoolProperty(
        name='Animate',
        description='Animate attached object at this keyframe',
        default=True
    )


def register_wow_m2_attachment_properties():
    bpy.types.Object.WowM2Attachment = bpy.props.PointerProperty(type=WowM2AttachmentPropertyGroup)


def unregister_wow_m2_attachment_properties():
    bpy.types.Object.WowM2Attachment = None


###############################
## Partciles
###############################

class WowM2ParticlePanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "particle"
    bl_label = "M2 Particle"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(context.object.particle_systems.active.settings.WowM2Particle, 'Type')

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.WowScene.Type == 'M2'
                and context.object is not None
                and context.object.particle_systems.active)


class WowM2ParticlePropertyGroup(bpy.types.PropertyGroup):
    Type = bpy.props.IntProperty()


def register_wow_m2_particle_properties():
    bpy.types.ParticleSettings.WowM2Particle = bpy.props.PointerProperty(type=WowM2ParticlePropertyGroup)


def unregister_wow_m2_particle_properties():
    bpy.types.ParticleSettings.WowM2Particle = None


###############################
## Event
###############################

class WowM2EventPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_label = "M2 Event"

    def draw_header(self, context):
        self.layout.prop(context.object.WowM2Event, "Enabled", text="")

    def draw(self, context):
        layout = self.layout
        layout.enabled = context.object.WowM2Event.Enabled

        col = layout.column()
        col.prop(context.object.WowM2Event, 'Token')
        col.prop(context.object.WowM2Event, 'Enabled')

        event_name = M2EventTokens.get_event_name(context.object.WowM2Event.Token)
        if event_name in ('PlayEmoteSound', 'DoodadSoundUnknown', 'DoodadSoundOneShot', 'GOPlaySoundKitCustom'):
            col.label(text='SoundEntryID')
            col.prop(context.object.WowM2Event, 'Data')
        elif event_name == 'GOAddShake':
            col.label(text='SpellEffectCameraShakesID')
            col.prop(context.object.WowM2Event, 'Data')

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.WowScene.Type == 'M2'
                and context.object is not None
                and context.object.type == 'EMPTY'
                and not (context.object.WowM2Attachment.Enabled or context.object.WowM2TextureTransform.Enabled)
        )


class WowM2EventPropertyGroup(bpy.types.PropertyGroup):

    Enabled = bpy.props.BoolProperty(
        name='Enabled',
        description='Enabled this object to be a WoW M2 event',
        default=False
    )

    Token = bpy.props.EnumProperty(
        name='Token',
        description='This token defines the purpose of the event',
        items=get_event_names
    )

    Data = bpy.props.IntProperty(
        name='Data',
        description='Data passed when this event is fired',
        min=0
    )

    Fire = bpy.props.BoolProperty(
        name='Enabled',
        description='Enable this event in this specific animation keyframe',
        default=False
    )


def register_wow_m2_event_properties():
    bpy.types.Object.WowM2Event = bpy.props.PointerProperty(type=WowM2EventPropertyGroup)


def unregister_wow_m2_event_properties():
    bpy.types.Object.WowM2Event = None


###############################
## Animation
###############################

class WowM2AnimationsPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_label = "M2 Animations"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.template_list("AnimationEditor_AnimationList", "", context.scene, "WowM2Animations", context.scene,
                          "WowM2CurAnimIndex")

        try:
            cur_anim_track = context.scene.WowM2Animations[context.scene.WowM2CurAnimIndex]

            row = col.row()
            row_split = row.split().row(align=True)
            row_split.prop(cur_anim_track, "PlaybackSpeed", text='Speed')

            if context.scene.sync_mode == 'AUDIO_SYNC' and context.user_preferences.system.audio_device == 'JACK':
                sub = row_split.row(align=True)
                sub.scale_x = 2.0
                sub.operator("screen.animation_play", text="", icon='PLAY')

            row = row_split.row(align=True)
            if not context.screen.is_animation_playing:
                if context.scene.sync_mode == 'AUDIO_SYNC' and context.user_preferences.system.audio_device == 'JACK':
                    sub = row.row(align=True)
                    sub.scale_x = 2.0
                    sub.operator("screen.animation_play", text="", icon='PLAY')
                else:
                    row.operator("screen.animation_play", text="", icon='PLAY_REVERSE').reverse = True
                    row.operator("screen.animation_play", text="", icon='PLAY')
            else:
                sub = row.row(align=True)
                sub.scale_x = 2.0
                sub.operator("screen.animation_play", text="", icon='PAUSE')

            row = row_split.row(align=True)
            row.operator("scene.wow_m2_animation_editor_seq_deselect", text='', icon='ARMATURE_DATA')

            col.separator()

        except IndexError:
            pass

        col.operator('scene.wow_animation_editor_toggle', text='Edit animations', icon='CLIP')

    @classmethod
    def poll(cls, context):
        return context.scene is not None and context.scene.WowScene.Type == 'M2'


###############################
## Texture Transform Controller
###############################

class WowM2TextureTransformControllerPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_label = "M2 Texture Transform"

    def draw_header(self, context):
        self.layout.prop(context.object.WowM2TextureTransform, "Enabled", text="")

    def draw(self, context):
        pass

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.WowScene.Type == 'M2'
                and context.object is not None
                and context.object.type == 'EMPTY'
                and not (context.object.WowM2Event.Enabled or context.object.WowM2Attachment.Enabled)
        )


class WowM2TextureTransformControllerPropertyGroup(bpy.types.PropertyGroup):

    Enabled = bpy.props.BoolProperty(
        name='Enabled',
        description='Enable this object to be WoW M2 texture transform controller',
        default=False
    )


def register_wow_m2_texture_transform_controller_properties():
    bpy.types.Object.WowM2TextureTransform = bpy.props.PointerProperty(type=WowM2TextureTransformControllerPropertyGroup)


def unregister_wow_m2_texture_transform_controller_properties():
    bpy.types.Object.WowM2TextureTransform = None


def register():
    register_wow_m2_material_properties()
    register_wow_m2_geoset_properties()
    register_wow_m2_texture_properties()
    register_wow_m2_light_properties()
    register_wow_m2_bone_properties()
    register_wow_m2_attachment_properties()
    register_wow_m2_particle_properties()
    register_wow_m2_event_properties()
    register_wow_m2_texture_transform_controller_properties()


def unregister():
    unregister_wow_m2_material_properties()
    unregister_wow_m2_geoset_properties()
    unregister_wow_m2_texture_properties()
    unregister_wow_m2_light_properties()
    unregister_wow_m2_bone_properties()
    unregister_wow_m2_attachment_properties()
    unregister_wow_m2_particle_properties()
    unregister_wow_m2_event_properties()
    unregister_wow_m2_texture_transform_controller_properties()


