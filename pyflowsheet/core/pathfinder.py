from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.dijkstra import DijkstraFinder
from pathfinding.finder.a_star import AStarFinder
from pathfinding.finder.breadth_first import BreadthFirstFinder
from pathfinding.core.heuristic import chebyshev, null, manhattan
from pathfinding.core.util import SQRT2
from math import pow
from pathfinding.core.util import backtrace, bi_backtrace
import heapq


def distance(a, b):
    return pow(a[0] - b[0], 2) + pow(a[1] - b[1], 2)


def compressPath(path):
    if len(path) < 2:
        return path
    deltaPath = []
    newPath = []

    newPath.append(path[0])

    for i, n in enumerate(path[1:]):
        deltaPath.append((n[0] - path[i][0], n[1] - path[i][1]))

    for i, delta in enumerate(deltaPath[1:]):
        lastDelta = deltaPath[i]
        if delta[0] != lastDelta[0] or delta[1] != lastDelta[1]:
            newPath.append(path[i + 1])
    newPath.append(path[-1])
    return newPath


def rectifyPath(path, grid, end):
    if len(path) < 2:
        return path

    newPath = []
    deltaPath = []
    last = path[0]
    goal = (end.x, end.y)

    containsBends = True

    while containsBends:
        i = 0
        containsBends = False
        while i < len(path) - 2:
            if (
                path[i][0] == path[i + 1][0]
                and path[i][1] > path[i + 2][1]
                and path[i + 1][0] > path[i + 2][0]
            ):
                print("Up/Left-Bend detected")
                containsBends = True

                newNode = (path[i + 2][0], path[i][1])
                path.remove(path[i])
                path.remove(path[i])
                path.remove(path[i])
                path.insert(i, newNode)

            i += 1
    for n in path:
        newPath.append(n)
    return newPath


class Pathfinder(AStarFinder):
    def __init__(self, turnPenalty=150):
        super(Pathfinder, self).__init__(
            diagonal_movement=DiagonalMovement.never,
            weight=1,
            heuristic=null
        )
        self.turnPenalty = turnPenalty

    def find_path(self, start, end, grid):
        """
        Find a path from start to end node on grid using the A* algorithm
        :param start: start node
        :param end: end node
        :param grid: grid that stores all possible steps/tiles
        :return: path as list of nodes
        """
        self.start_time = 0
        self.runs = 0
        start.g = 0
        start.f = 0
        start.h = 0
        start.opened = True
        start.closed = False
        start.parent = None

        open_list = []
        heapq.heappush(open_list, start)

        while len(open_list) > 0:
            current = heapq.heappop(open_list)
            current.closed = True

            if current == end:
                return backtrace(end), len(open_list)

            neighbors = grid.neighbors(current, self.diagonal_movement)
            for neighbor in neighbors:
                if neighbor.closed:
                    continue

                # get the distance between current node and the neighbor
                ng = self.calc_cost(current, neighbor)

                # check if the neighbor has not been inspected yet, or
                # can be reached with smaller cost from the current node
                if not neighbor.opened or ng < neighbor.g:
                    neighbor.g = ng
                    neighbor.h = neighbor.h or self.apply_heuristic(neighbor, end) * self.weight
                    neighbor.f = neighbor.g + neighbor.h
                    neighbor.parent = current

                    # add neighbor to open list
                    if not neighbor.opened:
                        heapq.heappush(open_list, neighbor)
                        neighbor.opened = True
                    else:
                        # the neighbor can be reached with smaller cost.
                        # Since its f value has been updated, we have to
                        # update its position in the open list
                        open_list.remove(neighbor)
                        heapq.heappush(open_list, neighbor)

        # failed to find path
        return [], len(open_list)

    def calc_cost(self, node_a, node_b):
        """
        get the distance between current node and the neighbor (cost)
        """
        if node_b.x - node_a.x == 0 or node_b.y - node_a.y == 0:
            # direct neighbor - distance is 1
            ng = node_a.g + 1
        else:
            # not a direct neighbor - diagonal movement
            ng = node_a.g + SQRT2

        # add turn penalty if direction changes
        if node_a.parent:
            last_dir = (node_a.x - node_a.parent.x, node_a.y - node_a.parent.y)
            curr_dir = (node_b.x - node_a.x, node_b.y - node_a.y)
            if last_dir != curr_dir:
                ng += self.turnPenalty

        return ng
