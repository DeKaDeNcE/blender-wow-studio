import bpy


class NodeTreeBuilder:

    def __init__(self, node_tree : bpy.types.NodeTree, x : float = -200, y : float = -200):
        self._x = x
        self._y = y
        self.tree = node_tree
        self.row_count = 1
        self.column_count = 1

        self.purge_tree()

    def purge_tree(self):
        for node in self.tree.nodes:
            self.tree.nodes.remove(node)

    def add_row(self):
        self.row_count += 1

    def add_column(self):
        self.column_count += 1

    def add_node(  self
                 , node_type : str
                 , node_name : str
                 , column : int
                 , row : int
                 , node_descr : str = ""
                ):

        if row + 1 < self.row_count:
            raise ValueError("Row {} is not created".format(row))

        if column + 1 < self.column_count:
            raise ValueError("Column {} is not created".format(column))

        node = self.tree.nodes.new(node_type)
        node.name = node_name
        node.label = node_descr if node_descr else node_name

        node.location = (300 * column + self._x, 300 * row + self._y)

        return node








