import bpy


class NodeTreeBuilder:

    def __init__( self
                 , node_tree : bpy.types.NodeTree
                 , x : float = -200
                 , y : float = -200
                 , delimeter : float = 300
                ):
        self._x = x
        self._y = y
        self.tree = node_tree
        self.delimeter = delimeter

        self.purge_tree()

    def purge_tree(self):
        for node in self.tree.nodes:
            self.tree.nodes.remove(node)

    def add_node(  self
                 , node_type : str
                 , node_name : str
                 , column : int
                 , row : int
                 , node_descr : str = ""
                ):

        node = self.tree.nodes.new(node_type)
        node.name = node_name
        node.label = node_descr if node_descr else node_name

        node.location = (self.delimeter * column + self._x, -self.delimeter * row + self._y)

        return node








