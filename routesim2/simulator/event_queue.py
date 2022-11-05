import heapq


class Event_Queue:
    q = []
    Current_Time = 0

    @staticmethod
    def Post(e):
        heapq.heappush(Event_Queue.q, e)

    @staticmethod
    def Get_Earliest():
        if Event_Queue.q == []:
            return None
        e = heapq.heappop(Event_Queue.q)
        Event_Queue.Current_Time = e.time_stamp
        return e

    @staticmethod
    def Str():
        ans = ""
        for i in Event_Queue.q:
            ans += str(i)
            ans += "\n"
        return ans

    @staticmethod
    def Get_Current_Time():
        return Event_Queue.Current_Time
