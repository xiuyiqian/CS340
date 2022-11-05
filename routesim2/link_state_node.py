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
    # Return a string
    def __str__(self):
        return "Rewrite this function to define your node dump printout"

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
        return -1
