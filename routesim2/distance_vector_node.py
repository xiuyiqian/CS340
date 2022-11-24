from typing import Dict, List, NamedTuple, Tuple
import copy
import json

from simulator.node import Node


class djNode:
    def __init__(self, cost=0, prev=list(), seq=0):
        self.cost = cost
        self.prev = prev
        self.seq = seq

    def addStop(self, n):
        self.prev.append(n)

    def addCost(self, n):
        self.cost += n


class Distance_Vector_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        # neighborID: cost
        self.neighborsCost = {}
        # self DV table
        self.dv = {}
        # neighbors and their DV table
        # neighbor(int):DVTable{}
        self.neighborsDv = {}
        # neighbors

    # Return a string
    def __str__(self):
        return f"<ID: {self.id}\n " \
               f"neighbors: {self.neighbors}\n" \
               f"DV table={self.dv}\n", \
               f"Neighbor Cost = {self.neighborsCost}\n", \
               f"Neighbors DV Tbale = {self.neighborsDv}\n>"

    def updateDv(self):
        tmpDV = dict()
        # check if there is anything from neighbor DV that can be used to update its own DV table
        # ndv is the type of djNode
        for neighborID, ndv in self.neighborsDv.items():
            edgeCost = self.neighborsCost[neighborID]
            for reach, dj in ndv.items():
                # dj is djNode type
                cost = dj.cost  # cost to current Node
                prev = dj.prev
                target = tmpDV.get(reach)

                targetCost = cost + edgeCost

                # avoid cycle/checked visited
                if self.id in prev or neighborID in prev:
                    continue
                # target is djNode Type
                if target is not None and targetCost >= target.cost:
                    # only update if the cost is smaller than targetCost
                    continue
                else:
                    # add new Node to the table
                    newPrev = prev.copy()
                    newDj = djNode(targetCost, newPrev)
                    newDj.addStop(neighborID)
                    tmpDV[reach] = newDj

        # add neighbor to the DV if not exist
        for neighborID, cost in self.neighborsCost.items():
            if neighborID not in tmpDV or tmpDV[neighborID].cost > cost:
                tmpDV[neighborID] = djNode(cost, [neighborID], self.get_time())

        #Object of type 'djNode' is not JSON serializable

        sendInfo = dict()
        # if there is change
        if self.change(tmpDV):
            self.dv = tmpDV
            sendInfo["info"] = {
                "id": self.id,
                "seq": self.get_time(),
                "dv": self.dv
            }
            self.send_to_neighbors(sendInfo)

    def link_has_been_updated(self, neighbor, latency):
        if latency != -1:
            # update cost to neighbor
            self.neighborsCost[neighbor] = latency
        else:
            if neighbor in self.neighborsCost:
                self.neighborsCost.pop(neighbor)
                self.neighbors.remove(neighbor)
                self.neighborsDv.pop(neighbor)
            else:
                # there is no this neighbor
                return
        self.updateDv()

    # Fill in this function
    def process_incoming_routing_message(self, m):

        info = m["info"]
        id = info["id"]
        seq = info["seq"]
        dv = info["dv"]

        if id not in self.neighbors:
            return

        if id in self.neighborsDv.keys() and self.neighborsDv[id].seq >= seq:
            return

        #dv = {int(nid): djNode(*node) for nid, node in dv.items()}
        self.neighborsDv[id] = dv.copy()
        self.updateDv()

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        if destination in self.dv:
            return self.dv[destination].prev[-1]
        else:
            return -1

    def change(self, dv):
        for reach, dj in dv.items():
            cost = dj.cost
            prev = dj.prev
            node = self.dv.get(reach)
            if node and node.cost == cost and node.prev == prev:
                continue
            else:
                return True

        return False
