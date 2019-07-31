import bpy
from ..handlers import DepsgraphLock

def update_doodad_pointer(self, context):
    if self.pointer and self.name != self.pointer.name:
        self.name = self.pointer.name


def update_current_object(self, context, col_name, cur_item_name):

    col = getattr(self, col_name)
    cur_idx = getattr(self, cur_item_name)

    if len(col) < cur_idx:
        return

    slot = col[cur_idx]

    if bpy.context.view_layer.objects.active == slot.pointer:
        return

    if slot.pointer and not slot.pointer.hide_get():
        with DepsgraphLock():
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = slot.pointer
            slot.pointer.select_set(True)


class WMO_UL_root_elements_template_list(bpy.types.UIList):

    icon = 'OBJECT_DATA'

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):

        if self.layout_type in {'DEFAULT', 'COMPACT'}:

            # handle material icons
            if self.icon == 'MATERIAL_DYNAMIC':
                texture = item.pointer.wow_wmo_material.diff_texture_1
                self.icon = layout.icon(texture) if texture else 'MATERIAL'

            row = layout.row()
            col = row.column()
            col.scale_x = 0.5

            if isinstance(self.icon, int):
                col.label(text="#{} ".format(index), icon_value=self.icon)

            elif isinstance(self.icon, str):
                col.label(text="#{} ".format(index), icon=self.icon)

            col = row.column()
            s_row = col.row(align=True)
            s_row.prop(item, 'pointer', emboss=True, text='')

            if not active_data.is_update_critical and active_propname == 'cur_group':
                s_row.prop(item, 'export', emboss=False, text='',
                           icon='CHECKBOX_HLT' if item.export else 'CHECKBOX_DEHLT')

        elif self.layout_type in {'GRID'}:
            pass

    def filter_items(self, context, data, propname):

        col = getattr(data, propname)
        filter_name = self.filter_name.lower()

        flt_flags = [self.bitflag_filter_item
                     if any(filter_name in filter_set for filter_set in (str(i), (item.pointer.name if item.pointer else 'Empty slot').lower()))
                     else 0 for i, item in enumerate(col, 1)
                     ]

        if self.use_filter_sort_alpha:
            flt_neworder = [x[1] for x in sorted(
                zip(
                    [x[0] for x in sorted(enumerate(col),
                                          key=lambda x: x[1].name.split()[1] + x[1].name.split()[2])], range(len(col))
                )
            )
            ]
        else:
            flt_neworder = []

        return flt_flags, flt_neworder