import math

from simulator.node import Node
from graph import Graph, Edge
import json
import time

actions = ["add edge", "delete edge", "update weight"]

class Link_State_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        # every node need to know the other nodes and edge information so create graph for each node
        self.graph = Graph()
        self.reach = {}   # dest, cost
        # for most recent routing msg for each edge
        self.routing_msgs = {}
        self.times = dict()
        self.sequence_number = 0
        self.Node = None
        if id in self.graph.nodes:
            self.Node = self.graph.nodes[id]
        else:
            self.Node = Node(id)
            self.graph.addNode(self.Node)
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
        # number of access to the edge
        update = None

        if not self.times.get((self.id,neighbor)):
            self.times[(self.id,neighbor)] = 1
        else:
            self.times[(self.id, neighbor)] += 1
        if latency < 0:
            self.graph.removeEdge((self.id,neighbor))
            update = "delete edge"
        else:
            if self.graph.hasEdge((self.id,neighbor)):
                self.graph.edges[(self.id,neighbor)].set_weight(latency)
                self.graph.edges[(neighbor, self.id)].set_weight(latency)
                update = "update weight"
            else:
                if neighbor not in self.graph.nodes:
                    newNeighbor = Node(neighbor)
                    newNeighbor.neighbors.append(self.Node)
                    self.graph.nodes[neighbor]=newNeighbor
                    self.graph.nodes[self.id].neighbors.append(newNeighbor)

                else:
                    newNeighbor = self.graph.nodes[neighbor]
                update = "add edge"
                newEdge = Edge(self.graph.nodes[self.id],newNeighbor,latency)
                self.graph.addEdge(newEdge)

                # if the edge does not exist need to tell its neighbor
            for i, old in self.routing_msgs.items():
                self.send_to_neighbor(neighbor, json.dumps(old))

        msg = {
            "source": self.id,
            "n1": self.id,
            "n2": neighbor,
            "weight": latency,
            "times":self.times[(self.id, neighbor)],
            "action":update
        }
        # store recent routing message
        self.routing_msgs[(self.id,neighbor)] = msg
        dist, prev = self.Dijkstra()

        #broadcast new message
        for i in self.graph.neighbours[self.id]:
            if i!=neighbor:
                self.send_to_neighbor(i,json.dumps(msg))


    # Fill in this function
    def process_incoming_routing_message(self, m):
        # load json message
        msg = json.loads(m)
        source = msg["source"]
        target = msg["n2"]
        weight = msg["weight"]
        times = msg["times"]
        old_msg = self.routing_msgs.get((source,target))
        if not old_msg:
            self.times[(source, target)] = 1
            if weight!=0:
                if target not in self.graph.nodes:
                    targetNode = Node(target)
                    self.graph.nodes[target]=targetNode

                if source not in self.graph.nodes:
                    sourceNode = Node(source)
                    self.graph.nodes[source]=sourceNode

                self.graph.nodes[target].neighbors.append(source)
                self.graph.nodes[source].neighbors.append(target)

                self.graph.addEdge(Edge(source,target,weight))
            # continue to broadcast to its neighbour
            for i in self.graph.neighbours[self.id]:
                if i!=source:
                    self.send_to_neighbor(i,json.dumps(msg))
        else:
            self.times[(source, target)] += 1
            if self.times[(source,target)] < times:
            # new message
                if weight<0:
                    self.graph.removeEdge((source,target))
                else:
                    # because it is the old messge the edge does exist so only need to update
                    self.graph.edges[(source,target)].set_weight(weight)
                    self.graph.edges[(source,target)].set_weight(weight)
                    for i in self.graph.neighbours[self.id]:
                        if i != source:
                            self.send_to_neighbor(i, json.dumps(msg))
            else:
            # old message
            # do not need to go further to end recursion
                self.send_to_neighbor(source,json.dumps(old_msg))


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
