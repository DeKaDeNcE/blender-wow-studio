from struct import pack, unpack
from .wow_common_types import ChunkHeader


###########################
# WMO GROUP
###########################

class MOGP_FLAG:
    HasCollision = 0x1
    HasVertexColor = 0x4
    Outdoor = 0x8
    DoNotUseLocalLighting = 0x40
    HasLight = 0x200
    HasDoodads = 0x800
    HasWater = 0x1000
    Indoor = 0x2000
    AlwaysDraw = 0x10000
    HasSkybox = 0x40000
    IsNotOcean = 0x80000
    IsMountAllowed = 0x200000
    HasTwoMOCV = 0x1000000
    HasTwoMOTV = 0x2000000


# contain WMO group header
class MOGP_chunk:
    def __init__(self):
        self.Header = ChunkHeader()
        self.GroupNameOfs = 0
        self.DescGroupNameOfs = 0
        self.Flags = 0
        self.BoundingBoxCorner1 = (0, 0, 0)
        self.BoundingBoxCorner2 = (0, 0, 0)
        self.PortalStart = 0
        self.PortalCount = 0
        self.nBatchesA = 0
        self.nBatchesB = 0
        self.nBatchesC = 0
        self.nBatchesD = 0
        self.FogIndices = (0, 0, 0, 0)
        self.LiquidType = 0
        self.GroupID = 0
        self.Unknown1 = 0
        self.Unknown2 = 0

    def read(self, f):
        # read header
        self.Header.read(f)

        self.GroupNameOfs = unpack("I", f.read(4))[0]
        self.DescGroupNameOfs = unpack("I", f.read(4))[0]
        self.Flags = unpack("I", f.read(4))[0]
        self.BoundingBoxCorner1 = unpack("fff", f.read(12))
        self.BoundingBoxCorner2 = unpack("fff", f.read(12))
        self.PortalStart = unpack("H", f.read(2))[0]
        self.PortalCount = unpack("H", f.read(2))[0]
        self.nBatchesA = unpack("H", f.read(2))[0]
        self.nBatchesB = unpack("H", f.read(2))[0]
        self.nBatchesC = unpack("H", f.read(2))[0]
        self.nBatchesD = unpack("H", f.read(2))[0]
        self.FogIndices = unpack("BBBB", f.read(4))
        self.LiquidType = unpack("I", f.read(4))[0]
        self.GroupID = unpack("I", f.read(4))[0]
        self.Unknown1 = unpack("I", f.read(4))[0]
        self.Unknown2 = unpack("I", f.read(4))[0]

    def write(self, f):
        self.Header.Magic = 'PGOM'

        self.Header.write(f)
        f.write(pack('I', self.GroupNameOfs))
        f.write(pack('I', self.DescGroupNameOfs))
        f.write(pack('I', self.Flags))
        f.write(pack('fff', *self.BoundingBoxCorner1))
        f.write(pack('fff', *self.BoundingBoxCorner2))
        f.write(pack('H', self.PortalStart))
        f.write(pack('H', self.PortalCount))
        f.write(pack('H', self.nBatchesA))
        f.write(pack('H', self.nBatchesB))
        f.write(pack('H', self.nBatchesC))
        f.write(pack('H', self.nBatchesD))
        f.write(pack('BBBB', *self.FogIndices))
        f.write(pack('I', self.LiquidType))
        f.write(pack('I', self.GroupID))
        f.write(pack('I', self.Unknown1))
        f.write(pack('I', self.Unknown2))

# Material information
class TriangleMaterial:
    def __init__(self):
        self.Flags = 0
        self.MaterialID = 0

    def read(self, f):
        self.Flags = unpack("B", f.read(1))[0]
        self.MaterialID = unpack("B", f.read(1))[0]

    def write(self, f):
        f.write(pack('B', self.Flags))
        f.write(pack('B', self.MaterialID))

# contain list of triangle materials. One for each triangle
class MOPY_chunk:
    def __init__(self):
        self.Header = ChunkHeader()
        self.TriangleMaterials = []

    def read(self, f):
        # read header
        self.Header.read(f)

        count = self.Header.Size // 2

        self.TriangleMaterials = []

        for i in range(count):
            tri = TriangleMaterial()
            tri.read(f)
            self.TriangleMaterials.append(tri)

    def write(self, f):
        self.Header.Magic = 'YPOM'
        self.Header.Size = len(self.TriangleMaterials) * 2

        self.Header.write(f)
        for tri in self.TriangleMaterials:
            tri.write(f)

# Indices
class MOVI_chunk:
    def __init__(self):
        self.Header = ChunkHeader()
        self.Indices = []

    def read(self, f):
        # read header
        self.Header.read(f)

        # 2 = sizeof(unsigned short)
        count = self.Header.Size // 2

        self.Indices = []

        for i in range(count):
            self.Indices.append(unpack("H", f.read(2))[0])

    def write(self, f):
        self.Header.Magic = 'IVOM'
        self.Header.Size = len(self.Indices) * 2

        self.Header.write(f)
        for i in self.Indices:
            f.write(pack('H', i))

# Vertices
class MOVT_chunk:
    def __init__(self):
        self.Header = ChunkHeader()
        self.Vertices = []

    def read(self, f):
        # read header
        self.Header.read(f)

        # 4 * 3 = sizeof(float) * 3
        count = self.Header.Size // (4 * 3)

        self.Vertices = []

        for i in range(count):
            self.Vertices.append(unpack("fff", f.read(12)))

    def write(self, f):
        self.Header.Magic = 'TVOM'
        self.Header.Size = len(self.Vertices) * 12

        self.Header.write(f)
        for v in self.Vertices:
            f.write(pack('fff', *v))

# Normals
class MONR_chunk:
    def __init__(self):
        self.Header = ChunkHeader()
        self.Normals = []

    def read(self, f):
        # read header
        self.Header.read(f)

        # 4 * 3 = sizeof(float) * 3
        count = self.Header.Size // (4 * 3)

        self.Normals = []

        for i in range(count):
            self.Normals.append(unpack("fff", f.read(12)))

    def write(self, f):
        self.Header.Magic = 'RNOM'
        self.Header.Size = len(self.Normals) * 12

        self.Header.write(f)
        for n in self.Normals:
            f.write(pack('fff', *n))

# Texture coordinates
class MOTV_chunk:
    def __init__(self):
        self.Header = ChunkHeader()
        self.TexCoords = []

    def read(self, f):
        # read header
        self.Header.read(f)

        # 4 * 2 = sizeof(float) * 2
        count = self.Header.Size // (4 * 2)

        self.TexCoords = []

        for i in range(count):
            self.TexCoords.append(unpack("ff", f.read(8)))

    def write(self, f):
        self.Header.Magic = 'VTOM'
        self.Header.Size = len(self.TexCoords) * 8

        self.Header.write(f)
        for tc in self.TexCoords:
            f.write(pack('ff', *tc))

# batch
class Batch:
    def __init__(self):
        self.BoundingBox = (0, 0, 0, 0, 0, 0)
        self.StartTriangle = 0
        self.nTriangle = 0
        self.StartVertex = 0
        self.LastVertex = 0
        self.Unknown = 0
        self.MaterialID = 0

    def read(self, f):
        #not sure
        self.BoundingBox = unpack("hhhhhh", f.read(12))
        self.StartTriangle = unpack("I", f.read(4))[0]
        self.nTriangle = unpack("H", f.read(2))[0]
        self.StartVertex = unpack("H", f.read(2))[0]
        self.LastVertex = unpack("H", f.read(2))[0]
        self.Unknown = unpack("B", f.read(1))[0]
        self.MaterialID = unpack("B", f.read(1))[0]

    def write(self, f):
        f.write(pack('hhhhhh', *self.BoundingBox))
        f.write(pack('I', self.StartTriangle))
        f.write(pack('H', self.nTriangle))
        f.write(pack('H', self.StartVertex))
        f.write(pack('H', self.LastVertex))
        f.write(pack('B', self.Unknown))
        f.write(pack('B', self.MaterialID))

# batches
class MOBA_chunk:
    def __init__(self):
        self.Header = ChunkHeader()
        self.Batches = []

    def read(self, f):
        # read header
        self.Header.read(f)

        count = self.Header.Size // 24

        self.Batches = []

        for i in range(count):
            batch = Batch()
            batch.read(f)
            self.Batches.append(batch)

    def write(self, f):
        self.Header.Magic = 'ABOM'
        self.Header.Size = len(self.Batches) * 24

        self.Header.write(f)
        for b in self.Batches:
            b.write(f)

# lights
class MOLR_chunk:
    def __init__(self):
        self.Header = ChunkHeader()
        self.LightRefs = []

    def read(self, f):
        # read header
        self.Header.read(f)

        # 2 = sizeof(short)
        count = self.Header.Size // 2

        self.LightRefs = []

        for i in range(count):
            self.LightRefs.append(unpack("h", f.read(2))[0])

    def write(self, f):
        self.Header.Magic = 'RLOM'
        self.Header.Size = len(self.LightRefs) * 2

        self.Header.write(f)
        for lr in self.LightRefs:
            f.write(pack('h', lr))

# doodads
class MODR_chunk:
    def __init__(self):
        self.Header = ChunkHeader()
        self.DoodadRefs = []

    def read(self, f):
        # read header
        self.Header.read(f)

        # 2 = sizeof(short)
        count = self.Header.Size // 2

        self.DoodadRefs = []

        for i in range(count):
            self.DoodadRefs.append(unpack("h", f.read(2))[0])

    def write(self, f):
        self.Header.Magic = 'RDOM'
        self.Header.Size = len(self.DoodadRefs) * 2

        self.Header.write(f)
        for dr in self.DoodadRefs:
            f.write(pack('h', dr))

class BSP_PLANE_TYPE:
    YZ_plane = 0
    XZ_plane = 1
    XY_plane = 2
    Leaf = 4 # end node, contains polygons

class BSP_Node:
    def __init__(self):
        self.PlaneType = 0
        self.Children = (0, 0)
        self.NumFaces = 0
        self.FirstFace = 0
        self.Dist = 0

    def read(self, f):
        self.PlaneType = unpack("h", f.read(2))[0]
        self.Children = unpack("hh", f.read(4))
        self.NumFaces = unpack("H", f.read(2))[0]
        self.FirstFace = unpack("I", f.read(4))[0]
        self.Dist = unpack("f", f.read(4))[0]

    def write(self, f):
        f.write(pack('h', self.PlaneType))
        f.write(pack('hh', *self.Children))
        f.write(pack('H', self.NumFaces))
        f.write(pack('I', self.FirstFace))
        f.write(pack('f', self.Dist))

# collision geometry
class MOBN_chunk:
    def __init__(self):
        self.Header = ChunkHeader()
        self.Nodes = []

    def read(self, f):
        # read header
        self.Header.read(f)

        count = self.Header.Size // 0x10

        self.Nodes = []

        for i in range(count):
            node = BSP_Node()
            node.read(f)
            self.Nodes.append(node)

    def write(self, f):
        self.Header.Magic = 'NBOM'
        self.Header.Size = len(self.Nodes) * 0x10

        self.Header.write(f)
        for node in self.Nodes:
            node.write(f)

class MOBR_chunk:
    def __init__(self):
        self.Header = ChunkHeader()
        self.Faces = []

    def read(self, f):
        # read header
        self.Header.read(f)

        count = self.Header.Size // 2

        self.Faces = []

        for i in range(count):
            self.Faces.append(unpack("H", f.read(2))[0])

    def write(self, f):
        self.Header.Magic = 'RBOM'
        self.Header.Size = len(self.Faces) * 2

        self.Header.write(f)
        for face in self.Faces:
            f.write(pack('H', face))

# vertex colors
class MOCV_chunk:
    def __init__(self):
        self.Header = ChunkHeader()
        self.vertColors = []

    def read(self, f):
        # read header
        self.Header.read(f)

        # 4 = sizeof(unsigned char) * 4
        count = self.Header.Size // 4

        self.vertColors = []

        for i in range(count):
            self.vertColors.append(unpack("BBBB", f.read(4)))

    def write(self, f):
        self.Header.Magic = 'VCOM'
        self.Header.Size = len(self.vertColors) * 4

        self.Header.write(f)
        for vc in self.vertColors:
            f.write(pack('BBBB', *vc))

class LiquidVertex:
    def __init__(self):

        self.height = 0

    def read(self, f):
        self.height = unpack("f", f.read(4))


    def write(self, f):
        f.write(pack('f', self.height))

class WaterVertex(LiquidVertex):
    def __init__(self):
        self.flow1 = 0
        self.flow2 = 0
        self.flow1Pct = 0
        self.filler = 0

    def read(self, f):

        self.flow1 = unpack("B", f.read(1))[0]
        self.flow2 = unpack("B", f.read(1))[0]
        self.flow1Pct = unpack("B", f.read(1))[0]
        self.filler = unpack("B", f.read(1))[0]
        LiquidVertex.read(self, f) # Python, wtf?


    def write(self, f):

        f.write(pack('B', self.flow1))
        f.write(pack('B', self.flow2))
        f.write(pack('B', self.flow1Pct))
        f.write(pack('B', self.filler))
        LiquidVertex.write(self, f) # Python, wtf?


class MagmaVertex(LiquidVertex):
    def __init__(self):
        self.u = 0
        self.v = 0

    def read(self, f):
        self.u = unpack("h", f.read(2))[0]
        self.v = unpack("h", f.read(2))[0]
        LiquidVertex.read(self, f)

    def write(self, f):
        f.write(pack('h', self.u))
        f.write(pack('h', self.v))
        LiquidVertex.write(self, f)


class MLIQ_chunk:
    def __init__(self, mat = True):
        self.Header = ChunkHeader()
        self.xVerts = 0
        self.yVerts = 0
        self.xTiles = 0
        self.yTiles = 0
        self.Position = (0, 0, 0)
        self.materialID = 0
        self.VertexMap = []
        self.TileFlags = []
        self.LiquidMaterial = mat

    def read(self, f):
        # read header
        self.Header.read(f)

        self.xVerts = unpack("I", f.read(4))[0]
        self.yVerts = unpack("I", f.read(4))[0]
        self.xTiles = unpack("I", f.read(4))[0]
        self.yTiles = unpack("I", f.read(4))[0]
        self.Position = unpack("fff", f.read(12))
        self.materialID = unpack("H", f.read(2))[0]

        self.VertexMap = []

        for i in range(self.xVerts * self.yVerts):
            vtx = WaterVertex() if self.LiquidMaterial else MagmaVertex()
            vtx.read(f)
            self.VertexMap.append(vtx)

        self.TileFlags = []

        # 0x40 = visible
        # 0x0C = invisible
        # well some other strange things (e.g 0x7F = visible, etc...)

        for i in range(self.xTiles * self.yTiles):
            self.TileFlags.append(unpack("B", f.read(1))[0])


    def write(self, f):
        self.Header.Magic = 'QILM'
        self.Header.Size = 30 + self.xVerts * self.yVerts * 8 + self.xTiles * self.yTiles

        self.Header.write(f)

        f.write(pack('I', self.xVerts))
        f.write(pack('I', self.yVerts))
        f.write(pack('I', self.xTiles))
        f.write(pack('I', self.yTiles))
        f.write(pack('fff', *self.Position))
        f.write(pack('H', self.materialID))

        for vtx in self.VertexMap:
            vtx.write(f)
        for tile_flag in self.TileFlags:
            f.write(pack('B', tile_flag))
