from struct import pack, unpack
from .wow_common_types import ChunkHeader


###########################
# WMO ROOT
###########################

# contain version of file
class MVER_chunk:
    def __init__(self, header=ChunkHeader(), version=0):
        self.Header = header
        self.Version = version

    def read(self, f):
        # read header
        self.Header.read(f)
        self.Version = unpack("I", f.read(4))[0]

    def write(self, f):
        self.Header.magic = 'REVM'
        self.Header.size = 4
        self.Header.write(f)
        f.write(pack('I', self.Version))

# WMO Root header
class MOHD_chunk:
    def __init__(self):
        self.Header = ChunkHeader()
        self.nMaterials = 0
        self.nGroups = 0
        self.nPortals = 0
        self.nLights = 0
        self.nModels = 0
        self.nDoodads = 0
        self.nSets = 0
        self.AmbientColor = (0, 0, 0, 0)
        self.ID = 0
        self.BoundingBoxCorner1 = (0.0, 0.0, 0.0)
        self.BoundingBoxCorner2 = (0.0, 0.0, 0.0)
        self.Flags = 0

    def read(self, f):
        # read header
        self.Header.read(f)

        self.nMaterials = unpack("I", f.read(4))[0]
        self.nGroups = unpack("I", f.read(4))[0]
        self.nPortals = unpack("I", f.read(4))[0]
        self.nLights = unpack("I", f.read(4))[0]
        self.nModels = unpack("I", f.read(4))[0]
        self.nDoodads = unpack("I", f.read(4))[0]
        self.nSets = unpack("I", f.read(4))[0]
        self.AmbientColor = unpack("BBBB", f.read(4))
        self.ID = unpack("I", f.read(4))[0]
        self.BoundingBoxCorner1 = unpack("fff", f.read(12))
        self.BoundingBoxCorner2 = unpack("fff", f.read(12))
        self.Flags = unpack("I", f.read(4))[0]

    def write(self, f):
        self.Header.magic = 'DHOM'
        self.Header.size = 64

        self.Header.write(f)
        f.write(pack('I', self.nMaterials))
        f.write(pack('I', self.nGroups))
        f.write(pack('I', self.nPortals))
        f.write(pack('I', self.nLights))
        f.write(pack('I', self.nModels))
        f.write(pack('I', self.nDoodads))
        f.write(pack('I', self.nSets))
        f.write(pack('BBBB', *self.AmbientColor))
        f.write(pack('I', self.ID))
        f.write(pack('fff', *self.BoundingBoxCorner1))
        f.write(pack('fff', *self.BoundingBoxCorner2))
        f.write(pack('I', self.Flags))


# Texture names
class MOTX_chunk:
    def __init__(self):
        self.Header = ChunkHeader()
        self.StringTable = bytearray()

    def read(self, f):
        # read header
        self.Header.read(f)
        self.StringTable = f.read(self.Header.size)

    def write(self, f):
        self.Header.magic = 'XTOM'
        self.Header.size = len(self.StringTable)

        self.Header.write(f)
        f.write(self.StringTable)

    def add_string(self, s):
        padding = len(self.StringTable) % 4
        if padding > 0:
            for iPad in range(4 - padding):
                self.StringTable.append(0)

        ofs = len(self.StringTable)
        self.StringTable.extend(s.encode('ascii'))
        self.StringTable.append(0)
        return ofs

    def get_string(self, ofs):
        if ofs >= len(self.StringTable):
            return ''
        start = ofs
        i = ofs
        while self.StringTable[i] != 0:
            i += 1
        return self.StringTable[start:i].decode('ascii')

    def get_all_strings(self):
        strings = []
        cur_str = ""

        for byte in self.StringTable:
            if byte:
                cur_str += chr(byte)
            elif cur_str:
                strings.append(cur_str)
                cur_str = ""

        return strings


class WMO_Material:
    def __init__(self):
        self.Flags = 0
        self.Shader = 0
        self.BlendMode = 0
        self.Texture1Ofs = 0
        self.EmissiveColor = (0, 0, 0, 0)
        self.SidnEmissiveColor = (0, 0, 0, 0)
        self.Texture2Ofs = 0
        self.DiffColor = (0, 0, 0, 0)
        self.TerrainType = 0
        self.Texture3Ofs = 0
        self.Color3 = (0, 0, 0, 0)
        self.Tex3Flags = 0
        self.RunTimeData = (0, 0, 0, 0)

    def read(self, f):
        self.Flags = unpack("I", f.read(4))[0]
        self.Shader = unpack("I", f.read(4))[0]
        self.BlendMode = unpack("I", f.read(4))[0]
        self.Texture1Ofs = unpack("I", f.read(4))[0]
        self.EmissiveColor = unpack("BBBB", f.read(4))
        self.SidnEmissiveColor = unpack("BBBB", f.read(4))
        self.Texture2Ofs = unpack("I", f.read(4))[0]
        self.DiffColor = unpack("BBBB", f.read(4))
        self.TerrainType = unpack("I", f.read(4))[0]
        self.Texture3Ofs = unpack("I", f.read(4))[0]
        self.Color3 = unpack("BBBB", f.read(4))
        self.Tex3Flags = unpack("I", f.read(4))[0]
        self.RunTimeData = unpack("IIII", f.read(16))[0]

    def write(self, f):
        f.write(pack('I', self.Flags))
        f.write(pack('I', self.Shader))
        f.write(pack('I', self.BlendMode))
        f.write(pack('I', self.Texture1Ofs))
        f.write(pack('BBBB', *self.EmissiveColor))
        f.write(pack('BBBB', *self.SidnEmissiveColor))
        f.write(pack('I', self.Texture2Ofs))
        f.write(pack('BBBB', *self.DiffColor))
        f.write(pack('I', self.TerrainType))
        f.write(pack('I', self.Texture3Ofs))
        f.write(pack('BBBB', *self.Color3))
        f.write(pack('I', self.Tex3Flags))
        f.write(pack('IIII', *self.RunTimeData))

# Materials
class MOMT_chunk:
    def __init__(self):
        self.Header = ChunkHeader()
        self.Materials = []

    def read(self, f):
        # read header
        self.Header.read(f)

        self.Materials = []
        for i in range(self.Header.size // 64):
            mat = WMO_Material()
            mat.read(f)
            self.Materials.append(mat)

    def write(self, f):
        self.Header.magic = 'TMOM'
        self.Header.size = len(self.Materials) * 64

        self.Header.write(f)
        for mat in self.Materials:
            mat.write(f)

# group names
class MOGN_chunk:
    def __init__(self):
        self.Header = ChunkHeader()
        self.StringTable = bytearray(b'\x00\x00')

    def read(self, f):
        # read header
        self.Header.read(f)
        self.StringTable = f.read(self.Header.size)

    def write(self, f):
        self.Header.magic = 'NGOM'

        # padd 4 bytes after
        padding = len(self.StringTable) % 4
        if(padding > 0):
            for iPad in range(4 - padding):
                self.StringTable.append(0)

        self.Header.size = len(self.StringTable)

        self.Header.write(f)
        f.write(self.StringTable)

    def add_string(self, s):
        ofs = len(self.StringTable)
        self.StringTable.extend(s.encode('ascii'))
        self.StringTable.append(0)
        return ofs

    def get_string(self, ofs):
        if ofs >= len(self.StringTable):
            return ''
        start = ofs
        i = ofs
        while self.StringTable[i] != 0:
            i += 1
        return self.StringTable[start:i].decode('ascii')

class GroupInfo:
    def __init__(self):
        self.Flags = 0
        self.BoundingBoxCorner1 = (0, 0, 0)
        self.BoundingBoxCorner2 = (0, 0, 0)
        self.NameOfs = 0

    def read(self, f):
        self.Flags = unpack("I", f.read(4))[0]
        self.BoundingBoxCorner1 = unpack("fff", f.read(12))
        self.BoundingBoxCorner2 = unpack("fff", f.read(12))
        self.NameOfs = unpack("I", f.read(4))[0]

    def write(self, f):
        f.write(pack('I', self.Flags))
        f.write(pack('fff', *self.BoundingBoxCorner1))
        f.write(pack('fff', *self.BoundingBoxCorner2))
        f.write(pack('I', self.NameOfs))


# group informations
class MOGI_chunk:
    def __init__(self):
        self.Header = ChunkHeader()
        self.Infos = []

    def read(self, f):
        # read header
        self.Header.read(f)

        count = self.Header.size // 32

        self.Infos = []
        for i in range(count):
            info = GroupInfo()
            info.read(f)
            self.Infos.append(info)

    def write(self, f):
        self.Header.magic = 'IGOM'
        self.Header.size = len(self.Infos) * 32

        self.Header.write(f)
        for info in self.Infos:
            info.write(f)

# skybox
class MOSB_chunk:
    def __init__(self):
        self.Header = ChunkHeader()
        self.Skybox = ''

    def read(self, f):
        # read header
        self.Header.read(f)
        self.Skybox = f.read(self.Header.size).decode('ascii')

    def write(self, f):
        self.Header.magic = 'BSOM'

        if not self.Skybox:
            self.Skybox = '\x00\x00\x00'

        self.Header.size = len(self.Skybox) + 1

        self.Header.write(f)
        f.write(self.Skybox.encode('ascii') + b'\x00')

# portal vertices
class MOPV_chunk:
    def __init__(self):
        self.Header = ChunkHeader()

        self.PortalVertices = []
        #self.Portals = []

    def read(self, f):
        # read header
        self.Header.read(f)

        count = self.Header.size // 12
        self.PortalVertices = []
        #self.Portals = []

        # 12 = sizeof(float) * 3
        for i in range(count):
            #self.PortalVertices = []
            #for j in range(4):
            self.PortalVertices.append(unpack("fff", f.read(12)))
                #print(self.mopt.Infos[i].nVertices)
            #self.Portals.append(self.PortalVertices)

    def write(self, f):
        self.Header.magic = 'VPOM'
        self.Header.size = len(self.PortalVertices) * 12

        self.Header.write(f)
        for v in self.PortalVertices:
            f.write(pack('fff', *v))

class PortalInfo:
    def __init__(self):
        self.StartVertex = 0
        self.nVertices = 0
        self.Normal = (0, 0, 0)
        self.Unknown = 0

    def read(self, f):
        self.StartVertex = unpack("H", f.read(2))[0]
        self.nVertices = unpack("H", f.read(2))[0]
        self.Normal = unpack("fff", f.read(12))
        self.Unknown = unpack("f", f.read(4))[0]

    def write(self, f):
        f.write(pack('H', self.StartVertex))
        f.write(pack('H', self.nVertices))
        f.write(pack('fff', *self.Normal))
        f.write(pack('f', self.Unknown))


# portal infos
class MOPT_chunk:
    def __init__(self):
        self.Header = ChunkHeader()
        self.Infos = []

    def read(self, f):
        # read header
        self.Header.read(f)

        self.Infos = []

        # 20 = sizeof(PortalInfo)
        for i in range(self.Header.size // 20):
            info = PortalInfo()
            info.read(f)
            self.Infos.append(info)

    def write(self, f):
        self.Header.magic = 'TPOM'
        self.Header.size = len(self.Infos) * 20

        self.Header.write(f)
        for info in self.Infos:
            info.write(f)

class PortalRelationship:
    def __init__(self):
        self.PortalIndex = 0
        self.GroupIndex = 0
        self.Side = 0
        self.Padding = 0

    def read(self, f):
        self.PortalIndex = unpack("H", f.read(2))[0]
        self.GroupIndex = unpack("H", f.read(2))[0]
        self.Side = unpack("h", f.read(2))[0]
        self.Padding = unpack("H", f.read(2))[0]

    def write(self, f):
        f.write(pack('H', self.PortalIndex))
        f.write(pack('H', self.GroupIndex))
        f.write(pack('h', self.Side))
        f.write(pack('H', self.Padding))

# portal link 2 groups
class MOPR_chunk:
    def __init__(self):
        self.Header = ChunkHeader()
        self.Relationships = []

    def read(self, f):
        # read header
        self.Header.read(f)

        self.Relationships = []

        for i in range(self.Header.size // 8):
            relationship = PortalRelationship()
            relationship.read(f)
            self.Relationships.append(relationship)

    def write(self, f):
        self.Header.magic = 'RPOM'
        self.Header.size = len(self.Relationships) * 8

        self.Header.write(f)

        for rel in self.Relationships:
            rel.write(f)


# visible vertices
class MOVV_chunk:
    def __init__(self):
        self.Header = ChunkHeader()
        self.VisibleVertices = []

    def read(self, f):
        # read header
        self.Header.read(f)

        self.VisibleVertices = []

        for i in range(self.Header.size // 12):
            self.VisibleVertices.append(unpack("fff", f.read(12)))

    def write(self, f):
        self.Header.magic = 'VVOM'
        self.Header.size = len(self.VisibleVertices) * 12

        self.Header.write(f)

        for v in self.VisibleVertices:
            f.write(pack('fff', *v))

class VisibleBatch:
    def __init__(self):
        self.StartVertex = 0
        self.nVertices = 0

    def read(self, f):
        self.StartVertex = unpack("H", f.read(2))[0]
        self.nVertices = unpack("H", f.read(2))[0]

    def write(self, f):
        f.write(pack('H', self.StartVertex))
        f.write(pack('H', self.nVertices))

# visible batches
class MOVB_chunk:
    def __init__(self):
        self.Header = ChunkHeader()
        self.Batches = []

    def read(self, f):
        # read header
        self.Header.read(f)

        count = self.Header.size // 4

        self.Batches = []

        for i in range(count):
            batch = VisibleBatch()
            batch.read(f)
            self.Batches.append(batch)

    def write(self, f):
        self.Header.magic = 'BVOM'
        self.Header.size = len(self.Batches) * 4

        self.Header.write(f)
        for batch in self.Batches:
            batch.write(f)

class Light:
    def __init__(self):
        self.LightType = 0
        self.Type = 1
        self.UseAttenuation = 1
        self.Padding = 1
        self.Color = (0, 0, 0, 0)
        self.Position = (0, 0, 0)
        self.Intensity = 0
        self.AttenuationStart = 0
        self.AttenuationEnd = 0
        self.Unknown1 = 0
        self.Unknown2 = 0
        self.Unknown3 = 0
        self.Unknown4 = 0

    def read(self, f):
        self.LightType = unpack("B", f.read(1))[0]
        self.Type = unpack("B", f.read(1))[0]
        self.UseAttenuation = unpack("B", f.read(1))[0]
        self.Padding = unpack("B", f.read(1))[0]
        self.Color = unpack("BBBB", f.read(4))
        self.Position = unpack("fff", f.read(12))
        self.Intensity = unpack("f", f.read(4))[0]
        self.AttenuationStart = unpack("f", f.read(4))[0]
        self.AttenuationEnd = unpack("f", f.read(4))[0]
        self.Unknown1 = unpack("f", f.read(4))[0]
        self.Unknown2 = unpack("f", f.read(4))[0]
        self.Unknown3 = unpack("f", f.read(4))[0]
        self.Unknown4 = unpack("f", f.read(4))[0]

    def write(self, f):
        f.write(pack('B', self.LightType))
        f.write(pack('B', self.Type))
        f.write(pack('B', self.UseAttenuation))
        f.write(pack('B', self.Padding))
        f.write(pack('BBBB', *self.Color))
        f.write(pack('fff', *self.Position))
        f.write(pack('f', self.Intensity))
        f.write(pack('f', self.AttenuationStart))
        f.write(pack('f', self.AttenuationEnd))
        f.write(pack('f', self.Unknown1))
        f.write(pack('f', self.Unknown2))
        f.write(pack('f', self.Unknown3))
        f.write(pack('f', self.Unknown4))


# lights
class MOLT_chunk:
    def __init__(self):
        self.Header = ChunkHeader()
        self.Lights = []

    def read(self, f):
        # read header
        self.Header.read(f)

        # 48 = sizeof(Light)
        count = self.Header.size // 48

        self.Lights = []
        for i in range(count):
            light = Light()
            light.read(f)
            self.Lights.append(light)

    def write(self, f):
        self.Header.magic = 'TLOM'
        self.Header.size = len(self.Lights) * 48

        self.Header.write(f)
        for light in self.Lights:
            light.write(f)

class DoodadSet:
    def __init__(self):
        self.Name = ''
        self.StartDoodad = 0
        self.nDoodads = 0
        self.Padding = 0

    def read(self, f):
        self.Name = f.read(20).decode("ascii")
        self.StartDoodad = unpack("I", f.read(4))[0]
        self.nDoodads = unpack("I", f.read(4))[0]
        self.Padding = unpack("I", f.read(4))[0]

    def write(self, f):
        f.write(self.Name.ljust(20, '\0').encode('ascii'))
        f.write(pack('I', self.StartDoodad))
        f.write(pack('I', self.nDoodads))
        f.write(pack('I', self.Padding))

# doodad sets
class MODS_chunk:
    def __init__(self):
        self.Header = ChunkHeader()
        self.Sets = []

    def read(self, f):
        # read header
        self.Header.read(f)

        count = self.Header.size // 32

        self.Sets = []

        for i in range(count):
            set = DoodadSet()
            set.read(f)
            self.Sets.append(set)

    def write(self, f):
        self.Header.magic = 'SDOM'
        self.Header.size = len(self.Sets) * 32

        self.Header.write(f)
        for set in self.Sets:
            set.write(f)


# doodad names
class MODN_chunk:
    def __init__(self):
        self.Header = ChunkHeader()
        self.StringTable = bytearray()

    def read(self, f):
        # read header
        self.Header.read(f)
        self.StringTable = f.read(self.Header.size)

    def write(self, f):
        self.Header.magic = 'NDOM'
        self.Header.size = len(self.StringTable)

        self.Header.write(f)
        f.write(self.StringTable)

    def AddString(self, s):
        padding = len(self.StringTable) % 4
        if padding > 0:
            for iPad in range(4 - padding):
                self.StringTable.append(0)

        ofs = len(self.StringTable)
        self.StringTable.extend(s.encode('ascii'))
        self.StringTable.append(0)
        return ofs

    def get_string(self, ofs):
        if ofs >= len(self.StringTable):
            return ''
        start = ofs
        i = ofs
        while self.StringTable[i] != 0:
            i += 1
        return self.StringTable[start:i].decode('ascii')

class DoodadDefinition:
    def __init__(self):
        self.NameOfs = 0
        self.Flags = 0
        self.Position = (0, 0, 0)
        self.Rotation = [0, 0, 0, 0]
        self.Scale = 0
        self.Color = [0, 0, 0, 0]

    def read(self, f):
        weirdThing = unpack("I", f.read(4))[0]
        self.NameOfs = weirdThing & 0xFFFFFF
        self.Flags = (weirdThing >> 24) & 0xFF
        self.Position = unpack("fff", f.read(12))
        self.Rotation = unpack("ffff", f.read(16))
        self.Scale = unpack("f", f.read(4))[0]
        self.Color = unpack("BBBB", f.read(4))

    def write(self, f):
        weirdThing = ((self.Flags & 0xFF) << 24) | (self.NameOfs & 0xFFFFFF)
        f.write(pack('I', weirdThing))
        f.write(pack('fff', *self.Position))
        f.write(pack('ffff', *self.Rotation))
        f.write(pack('f', self.Scale))
        f.write(pack('BBBB', *self.Color))

# doodad definition
class MODD_chunk:
    def __init__(self):
        self.Header = ChunkHeader()
        self.Definitions = []

    def read(self, f):
        # read header
        self.Header.read(f)

        count = self.Header.size // 40

        self.Definitions = []
        for i in range(count):
            defi = DoodadDefinition()
            defi.read(f)
            self.Definitions.append(defi)

    def write(self, f):
        self.Header.magic = 'DDOM'
        self.Header.size = len(self.Definitions) * 40

        self.Header.write(f)
        for defi in self.Definitions:
            defi.write(f)

# fog
class Fog:
    def __init__(self):
        self.Flags = 0
        self.Position = (0, 0, 0)
        self.SmallRadius = 0
        self.BigRadius = 0
        self.EndDist = 0
        self.StartFactor = 0
        self.Color1 = (0, 0, 0, 0)
        self.EndDist2 = 0
        self.StartFactor2 = 0
        self.Color2 = (0, 0, 0, 0)

    def read(self, f):
        self.Flags = unpack("I", f.read(4))[0]
        self.Position = unpack("fff", f.read(12))
        self.SmallRadius = unpack("f", f.read(4))[0]
        self.BigRadius = unpack("f", f.read(4))[0]
        self.EndDist = unpack("f", f.read(4))[0]
        self.StartFactor = unpack("f", f.read(4))[0]
        self.Color1 = unpack("BBBB", f.read(4))
        self.EndDist2 = unpack("f", f.read(4))[0]
        self.StartFactor2 = unpack("f", f.read(4))[0]
        self.Color2 = unpack("BBBB", f.read(4))

    def write(self, f):
        f.write(pack('I', self.Flags))
        f.write(pack('fff', *self.Position))
        f.write(pack('f', self.SmallRadius))
        f.write(pack('f', self.BigRadius))
        f.write(pack('f', self.EndDist))
        f.write(pack('f', self.StartFactor))
        f.write(pack('BBBB', *self.Color1))
        f.write(pack('f', self.EndDist2))
        f.write(pack('f', self.StartFactor2))
        f.write(pack('BBBB', *self.Color2))

class MFOG_chunk:
    def __init__(self):
        self.Header = ChunkHeader()
        self.Fogs = []

    def read(self, f):
        # read header
        self.Header.read(f)

        count = self.Header.size // 48

        self.Fogs = []
        for i in range(count):
            fog = Fog()
            fog.read(f)
            self.Fogs.append(fog)

    def write(self, f):
        self.Header.magic = 'GOFM'
        self.Header.size = len(self.Fogs) * 48

        self.Header.write(f)
        for fog in self.Fogs:
            fog.write(f)

# Convex volume plane, used only for transport objects
class MCVP_chunk:
    def __init__(self):
        self.Header = ChunkHeader()
        self.convex_volume_planes = []

    def read(self, f):
        self.Header.read(f)

        count = self.Header.size // 16

        for i in range(0, count):
            self.convex_volume_planes.append(unpack('ffff', f.read(16)))

    def write(self, f):
        self.Header.magic = 'PVCM'
        self.Header.size = len(self.convex_volume_planes) * 16

        self.Header.write(f)
        for i in self.convex_volume_planes:
            f.write(pack('ffff', self.convex_volume_planes[i]))


