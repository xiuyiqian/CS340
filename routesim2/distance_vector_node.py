from simulator.node import Node
import json
import copy
import math
class pathCost:
    def __init__(self, p=list(), c=0):
        # list of nodes it has passed
        self.path = p
        # current cost so far
        self.cost = c

class Distance_Vector_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        # neighbour, sequence number

        self.times = dict()
        # dict(int, path)
        self.dv = {}
        # dict(int, dict(int, path))
        self.neighborsDV = dict()
        self.neighborCost = {}
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
        if latency >= 0:
            self.neighborCost[neighbor]=latency
        else:
            if neighbor in self.neighborCost:
                self.neighborCost.pop(neighbor)
                self.neighborsDV.pop(neighbor)
            # else: do nothing

        change = False  # if anything changes

        for neighbor, cost in self.neighborCost.items():
            if not neighbor in self.dv:
                self.dv[neighbor] = pathCost()
            if self.dv[neighbor].cost > cost:
                self.dv[neighbor].cost = cost

        for neighbor, targetDict in self.neighborsDV.items():
            costToTarget = self.neighborCost[neighbor]
            for target in targetDict:
                if self.id == target:
                    continue
                nowTarget = self.dv.get(target)
                if nowTarget is not None:
                    if self.neighborsDV[nowTarget]+costToTarget < self.DV[target].cost:
                        self.DV[target].cost = self.neighborsDV[target].cost + costToTarget
                        newPath = self.DV[target].path.copy()
                        self.DV[target].path = newPath
                        change = True
                    else:
                        continue

        if change:
            for i in self.neighborCost:
                times = self.times.get(i,0)
                self.send_to_neighbors(i,json.dumps(self.id,times+1,self.dv))


        # Fill in this function
    def process_incoming_routing_message(self, m):
        source, times,neighbourDv = json.loads(m)
        if self.times[source]<int(times):
            dv = copy.copy(neighbourDv)
            self.neighbors_dv[source] = neighbourDv
            self.update_dv()


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
