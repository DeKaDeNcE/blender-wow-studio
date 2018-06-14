import bpy


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


def register():
    bpy.types.ParticleSettings.WowM2Particle = bpy.props.PointerProperty(type=WowM2ParticlePropertyGroup)


def unregister():
    del bpy.types.ParticleSettings.WowM2Particle