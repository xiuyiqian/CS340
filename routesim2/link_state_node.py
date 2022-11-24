import json
import heapq
import math
from simulator.node import Node

class djNode:
    # prev is a list
    def __init__(self, id, cost, prev=list()):
        self.id = id
        self.totalCost = cost
        self.prev = prev
    def __lt__(self, other):
        return self.totalCost < other.totalCost

    def __str__(self):
        if self.prev is not None:
            return "{ " + str(self.id) + " previous: " + " ".join(map(str,self.prev)) + " current Cost: " + str(self.totalCost) + "}"
        else:
            return "{ " + str(self.id) +  " current Cost: " + str(
                self.totalCost) + "}"
    def addPrev(self,id):
        self.prev.append(id)
        return self.prev
    def setLatency(self,l):
        self.totalCost += l
class message():
    def __init__(self,source,dest,seq,prev,latency):
        self.source = source
        self.dest = dest
        self.seq = seq
        self.prev = prev
        self.latency = latency


class Link_State_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        # key is edge (id,neighbor), {value: latency, seq}
        self.info = dict()
    # Return a string
    def __str__(self):
        return "Rewrite this function to define your node dump printout"

    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        # latency = -1 if delete a link
        k = frozenset((self.id, neighbor))
        if neighbor in self.neighbors:
            if latency == -1:
                self.neighbors.remove(neighbor)

            self.info[k]["latency"] = latency
            self.info[k]["seq"] += 1
            # cannot drop the dict as it needs to be passed to other neighbors
        else:
            # not in neighbor
            self.neighbors.append(neighbor)
            self.info[k] = {
                "latency": latency,
                "seq": 1
            }
        # message sender is different from source. source is the edge information not necessarily equal to message sender
        allMsg = list()
        for nodePair, msg in self.info.items():
            source,target = nodePair
            l = msg["latency"]
            time = msg["seq"]

            m = {
                "messageSender": self.id,
                "source":source,
                "dest": target,
                "latency":l,
                "seq":time
            }
            allMsg.append(m)
            self.send_to_neighbors(json.dumps({"information":allMsg}))

    # Fill in this function
    def process_incoming_routing_message(self, m):
        messages = json.loads(m)["information"]
        #print(len(messages))
        for msg in messages:
        #print(msg)
            sender = msg["messageSender"]
            # updated Edge source
            source = msg["source"]
            # updated Edge dest
            target = msg["dest"]
            # cost
            cost = msg["latency"]
            # sequence number
            seq = msg["seq"]

            k = frozenset((source, target))

            if self.id == source or self.id == target:
                continue
            if self.id == sender:
                continue

            if k in self.info.keys():
                # ignore older message for the same edge
                if self.info[k]["seq"] >= seq:
                    continue
                else:
                    ## "latency": latency, "seq": 1
                    self.info[k]["latency"] = cost
                    self.info[k]["seq"] = seq
                    m = [{
                        "messageSender": self.id,
                        "source": source,
                        "dest": target,
                        "latency": cost,
                        "seq": seq
                    }]
                    # cannot send to the sender
                    for n in self.neighbors:
                        if n != sender:
                            self.send_to_neighbor(n,json.dumps({"information":m}))
            else:
                # insert it into info table
                    self.info[k] = {
                        "latency": cost,
                        "seq": seq
                    }
                    # send to other neighbor
                    m = [{
                        "messageSender": self.id,
                        "source": source,
                        "dest": target,
                        "latency": cost,
                        "seq": seq
                    }]
                    # no need to concern
                    for n in self.neighbors:
                        if n != sender:
                            self.send_to_neighbor(n, json.dumps({"information": m}))

    def Dijkstra(self,goal):
        import pdb
        dist = {}
        q = list()
        prev = list()
        # construct the graphs
        dist[self.id] = 0
        #     def __init__(self, id, latency, prev=list()):
        tmpNode = djNode(self.id,0,list())

        heapq.heappush(q,tmpNode)

        while len(q) > 0:
            oneNode = heapq.heappop(q)
            currentID = oneNode.id
            if currentID == goal:
                return oneNode.prev[0]

            prev = oneNode.prev

            for nodePair, msg in self.info.items():
                first,second = nodePair
                #pdb.set_trace()
                if msg["latency"] == -1:
                    # deleted link
                    continue
                # only need neighbor information
                if currentID!=first and currentID!=second:
                    #pdb.set_trace()
                    #print("none of source or target " + str(currentID))
                    continue
                else:
                    t1 = None # the other end
                    if currentID == first:
                        t1 = second
                    else:
                        t1 = first

                    currentCost = msg["latency"] + oneNode.totalCost
                    #pdb.set_trace()
                    if t1 not in dist.keys() or dist[t1] > currentCost:
                        dist[t1] = currentCost
                        tmpNode = djNode(t1, currentCost, prev + [t1])
                        heapq.heappush(q,tmpNode)
            #pdb.set_trace()

        return None

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        res = self.Dijkstra(destination)
        #print(res)
        if not res:
            return -1
        else:
            return res
