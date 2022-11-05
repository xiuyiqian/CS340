from simulator.node import Node

def edge_id(v1,v2):  # normalize key v1,v2 to tuple (v_low,v_hi)
    return (v1, v2) if v1 <= v2 else (v2, v1)

class Edge:
    # {{{ Edge Class
    edge_id = 0

    def __init__(self, source, target, weight=1):
        # both source and target are Node objects
        self.source = source
        self.target = target
        if type(weight) == int:
            self.weight = weight
        else:
            self.weight = 1  # default

        self.id = edge_id(source,target)

    def __eq__(self, edge):
        if self.source == edge.source and self.target == edge.target and self.weight == edge.weight:
            return True
        else:
            return False

    def __hash__(self):
        return self.id

    def __str__(self):
        return '({}, {}, {})'.format(self.source, self.target, self.getWeight())

    def __repr__(self):
        return self.__str__()

    def get_id(self):
        return self.id

    def get_source(self):
        return self.source

    def get_target(self):
        return self.target

    def get_weight(self):
        return self.weight

    def set_weight(self, weight):
        if type(weight) == int:
            self.weight = weight
        else:
            print
            "Please enter an integer for weight! (Now set to default value 1)"
            self.weight = 1  # default

    def reverse(self):
        source = self.source
        target = self.target
        weight = self.weight
        return Edge(target, source, weight)

"""
Graph class
"""
# undirected graph
class Graph:
# {{{ Graph Class

    def __init__(self, nodes=[], edges=[]):
    # nodes: list of Node objects;
    # edges: list of Edge objects;

        if type(nodes) == list:
            self.nodes = nodes
        else:
            self.nodes = [nodes]

        if type(edges) == list:
            self.edges = edges
            reverse = []
            # both directions are needed
            for edge in edges:
                reverse.append(edge.reverse())
            self.edges.extend(reverse)
        else:
            self.edges = [edges, edges.reverse()]
            # self.edges = [edges]


    def getNodes(self):
        return self.nodes

    def hasNode(self, node):
        return node in self.nodes

    def addNode(self, node):
        if self.hasNode(node):
            print ("{} is already in the graph".format(node))
        else:
            self.nodes.append(node)

    def addNodes(self, nodes):
        for node in nodes:
            self.addNode(node)

    def removeNode(self, node):
        # also remove edges that include the node
        if self.hasNode(node):
            self.nodes.remove(node)
            remove = []
            for edge in self.edges:
                source = edge.getSource()
                target = edge.getTarget()
                if source == node or target == node:
                    remove.append(edge)
            for edge in remove:
                self.edges.remove(edge)

        else:
            print ("{} is not in this graph!".format(node))

    def removeNodes(self, nodes):
        for node in nodes:
            self.removeNode(node)

    def getEdges(self):
        return self.edges

    def hasEdge(self, edge):
        return edge in self.edges

    def addEdge(self, edge):
        if self.hasEdge(edge):
            print ("{} is already in this graph".format(edge))
            return
        source = edge.getSource()
        target = edge.getTarget()
        if source in self.nodes and target in self.nodes:
            self.edges.extend([edge, edge.reverse()])
        else:
            print ("source or target node of this edge is not eligible!")

    def addEdges(self, edges):
        for edge in edges:
            self.addEdge(edge)

    def removeEdge(self, edge):
        reversedEdge = edge.reverse()
        if self.hasEdge(edge) and self.hasEdge(reversedEdge):
            self.edges.remove(edge)
            self.edges.remove(reversedEdge)
        else:
            print ("{} is not in this graph!".format(edge))

    def removeEdges(self, edges):
        for edge in edges:
            self.removeEdge(edge)



    def __repr__(self):
        return self.__str__()