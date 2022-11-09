from simulator.node import Node


class Edge:
    # {{{ Edge Class
    edge_id = 0

    def __init__(self, source, target, weight=1):
        # both source and target are Node objects ID
        self.source = source
        self.target = target
        if type(weight) == int:
            self.weight = weight
        else:
            self.weight = 1  # default

        self.id = (source, target)

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
        self.nodes = dict()
        self.edges = dict()
        # dict:list of neighbours
        self.neighbours: dict[int, list] = dict()

        if type(nodes) == list:
            for i in nodes:
                self.nodes[i.id] = i

        if type(edges) == list:
            for i in edges:
                self.edges[i.id] = i
            reverse = []
            # both directions are needed
            for edge in edges:
                reverse.append(self.edges[edge].reverse())

            for i in reverse:
                self.edges[i.id] = i

    def getNodes(self):
        return self.nodes

    def hasNode(self, node):
        return node in self.nodes

    # node is node
    def addNode(self, node):
        if self.hasNode(node.id):
            print("{} is already in the graph".format(node))
        else:
            self.nodes[node.id] = node

    def addNodes(self, nodes):
        for node in nodes:
            self.addNode(node)

    # n: is the id
    def removeNode(self, n):
        # also remove edges that include the node
        if self.hasNode(n):
            self.nodes.pop(n)
            remove = []
            for e in self.edges:
                source = self.edges[e].getSource()
                target = self.edges[e].getTarget()
                if source.id == n or target.id == n:
                    remove.append(e)
            for edge in remove:
                self.edges.pop(edge)

        else:
            print("{} is not in this graph!".format(n))

    def removeNodes(self, nodes):
        for node in nodes:
            self.removeNode(node)

    def getEdges(self):
        return self.edges

    def hasEdge(self, edge):
        return edge in self.edges

    # edge:edge
    def addEdge(self, edge):
        if self.hasEdge(edge.id):
            print("{} is already in this graph".format(edge))
            return
        source = self.edges[edge.id].getSource()
        target = self.edges[edge.id].getTarget()

        self.neighbours[source].append(target)
        self.neighbours[target].append(source)

        if source.id in self.nodes and target.id in self.nodes:
            self.edges[(source.id, target.id)] = edge
            self.edges[(target.id, source.id)] = edge.reverse()
        else:
            print("source or target node of this edge is not eligible!")

    def addEdges(self, edges):
        for edge in edges:
            self.addEdge(edge)

    # edge: id
    def removeEdge(self, edge):
        if edge not in self.edges:
            print("the edge does not exist")
            return
        else:
            source = self.edges[edge].getSource()
            target = self.edges[edge].getTarget()
        if self.hasEdge(edge) and self.hasEdge((target.id, source.id)):
            self.edges.pop(edge)
            self.edges.pop((target.id, source.id))
            if target not in self.neighbours[source]:
                print("{} not in {} neighbours".format(target, source))
            else:
                self.neighbours[source].remove(target)

            if target not in self.neighbours[source]:
                print("{} not in {} neighbours".format(source, target))
            else:
                self.neighbours[target].remove(source)

        else:
            print("{} is not in this graph!".format(edge))

    def removeEdges(self, edges):
        for edge in edges:
            self.removeEdge(edge)

    def __repr__(self):
        return self.__str__()
