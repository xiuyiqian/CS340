import math

from simulator.node import Node
from graph import Graph, Edge


class Distance_Vector_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.neighbours: dict[int, dict()] = dict()
        self.dv = dict()
        self.dv[id] = 0
        self.pred = dict()

        self.graph = Graph()
        if id in self.graph.nodes:
            self.Node = self.graph.nodes[id]
        else:
            self.Node = Node(id)
            self.graph.addNode(self.Node)

    # Return a string
    def __str__(self):

        return "Rewrite this function to define your node dump printout"

    def bellman_ford(self):
        for node in self.graph.getNodes():
            self.dv[node.id] = math.inf
            self.pred[node.id] = None

        for node in self.graph.getNodes():
            for edge in node.neighbours:
                # tempDistance <- distance[M] + edge_weight(M, N)
                tmp_dist = edge.get_weight() + self.dv[edge.get_target()]
                if tmp_dist < self.dv[node.id]:
                    # distance[N] < - tempDistance
                    # previous[N] < - M
                    self.dv[node.id] = tmp_dist
                    self.pred[node.id] = edge.get_target()

        for edge in self.Node.neighbors:
            if self.dv[edge.get_target()] + edge.get_weight() < self.dv[edge.get_source()]:
                print("Negative Cycle Exists")

    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        # latency = -1 if delete a link
        pass

    # Fill in this function
    def process_incoming_routing_message(self, m):

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        self.bellman_ford()
        for key, val in self.pred.items():
            if key == destination:
                tmp_hop = key
                while self.pred[tmp_hop] != self.id:
                    tmp_hop = self.pred[tmp_hop]
                return tmp_hop
        return -1
