import math

from simulator.node import Node
from graph import Graph, Edge
import json

class Link_State_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.graph = Graph()
        self.reach = {}   # dest, cost
        # for most recent routing msg for each edge
        self.routing_msgs = {}
        self.sequence_number = 0
    # Return a string
    def __str__(self):
        return "Rewrite this function to define your node dump printout"

    def find_min_dist_u(self):
        # u := vertex in Q with minimum dist[u]
        min_dist = math.inf
        closet_node = None
        for edge in self.graph.getEdges():
            if edge.get_source() == self.id and edge.get_target() != self.id:
                if edge.get_weight() < min_dist:
                    closet_node = edge.get_target()
        return closet_node, min_dist

    def Dijkstra(self):
        vertexes = self.graph.getNodes()
        dist = {}
        prev = {}
        Q = {}
        # construct the graphs
        for vex in vertexes:
            dist[vex] = math.inf
            prev[vex] = None
            Q[vex] = 0
        dist[self.id] = 0

        while len(Q) > 0:
            # u := vertex in Q with minimum dist[u]
            u, min_dist = self.find_min_dist_u()
            if min_dist == math.inf:
                print("no neighbors for node", self.id)
                break
            dist[u] = min_dist
            Q.pop(u)
            # try using u to make shorter path
            for edge in self.graph.getEdges():
                if edge.get_source() == u.id:
                    # find neighbors of u
                    v = edge.get_target()
                    if min_dist + edge.get_weight() < dist[v]:
                        dist[v] = min_dist + edge.get_weight()
                        prev[v] = u

        return dist, prev

    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        # latency =  -1 if delete a link
        if latency < 0:
            self.graph.removeEdge((self.id,neighbor))
        else:
            if self.graph.hasEdge((self.id,neighbor)):
                self.graph.edges[(self.id,neighbor)].set_weight(latency)
                self.graph.edges[(neighbor, self.id)].set_weight(latency)
            else:

                if neighbor not in self.graph.nodes:
                    newNeighbor = Node(neighbor)
                    newNeighbor.neighbors.append(self.id)
                    self.graph.nodes[neighbor]=newNeighbor
                else:
                    newNeighbor = self.graph.nodes[neighbor]
                newEdge = Edge(self.graph.nodes[self.id],newNeighbor,latency)
                self.graph.addEdge(newEdge)

                for i, old in self.routing_msgs.items():
                    self.send_to_neighbor(neighbor, json.dumps(old))

    # Fill in this function
    def process_incoming_routing_message(self, m):
        pass

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        self.reach, prev = self.Dijkstra()
        for key, val in prev:
            if key == destination:
                tmp_hop = key
                while prev[tmp_hop] != self.id:
                    tmp_hop = prev[tmp_hop]
                return tmp_hop
        return -1
