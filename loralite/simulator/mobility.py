from __future__ import annotations
import math
from random import randint
from typing import TYPE_CHECKING, Tuple, Sequence
import numpy as np
import matplotlib.pyplot as plt
plt.switch_backend('agg')
from matplotlib.patches import Ellipse
from sortedcontainers import SortedDict
import loralite.simulator.globals as coglobs
from loralite.simulator.utils import round2

if TYPE_CHECKING:
    from loralite.simulator.definitions import DeviceType

Coordinates = list[int]

DISTANCE_TABLE: np.ndarray = np.full((0, 0), -1)
MIN_DISTANCE = 50


def get_distance(node1: DeviceType, node2: DeviceType) -> float:
    global DISTANCE_TABLE
    try:
        # distance = float(DISTANCE_TABLE[node1.id][node2.id])
        distance = DISTANCE_TABLE.item(node1.id, node2.id)
        if distance <= 0:
            distance = round2(calculate_distance(node1, node2))
            DISTANCE_TABLE[node1.id][node2.id] = distance
            DISTANCE_TABLE[node2.id][node1.id] = distance

        return float(distance)
    except IndexError:
        d_size = coglobs.LIST_OF_NODES.peekitem(-1)[0] + 1
        if len(DISTANCE_TABLE) == 0:
            DISTANCE_TABLE = np.full((d_size, d_size), -1)
        else:
            current_shape = DISTANCE_TABLE.shape
            pad_size = d_size - current_shape[0]
            DISTANCE_TABLE = np.lib.pad(DISTANCE_TABLE, ((0, pad_size), (0, pad_size)), 'constant', constant_values=(-1))
            # DISTANCE_TABLE.resize((d_size, d_size), refcheck=False)
        dist = round2(calculate_distance(node1, node2))
        DISTANCE_TABLE[node1.id][node2.id] = dist
        DISTANCE_TABLE[node2.id][node1.id] = dist

        return float(DISTANCE_TABLE.item(node1.id, node2.id))

def calculate_distance_simple(xy1: Tuple[int, int, int], xy2: Tuple[int, int, int]) -> float:
    return math.sqrt(sum([(o2 - o1) ** 2 for o2, o1 in zip(xy1, xy2)]))


def calculate_distance(node1: DeviceType, node2: DeviceType) -> float:
    return math.sqrt(
        sum([(o2 - o1) ** 2 for o2, o1 in zip(node1.position, node2.position)])
    )


def calculate_distance_matrix(nodes: SortedDict) -> None:
    # pylint: disable=global-statement
    global DISTANCE_TABLE
    if len(nodes) <= 1:
        raise RuntimeError("You need to have at least two units to run the simulation!")

    d_size = nodes.peekitem(-1)[0] + 1
    # DISTANCE_TABLE = np.zeros((nodes.peekitem(-1)[0], nodes.peekitem(-1)[0]))
    DISTANCE_TABLE = np.full((d_size, d_size), -1)

    for id1 in nodes:
        node1 = nodes[id1]
        # DISTANCE_TABLE.append([])
        for id2 in nodes:
            node2 = nodes[id2]
            if node1 != node2:
                dist = round2(calculate_distance(node1, node2))
                DISTANCE_TABLE[node1.id][node2.id] = dist
            else:
                DISTANCE_TABLE[node1.id][node1.id] = 0


def generate_coordinates(
    x_c: int,
    y_c: int,
    radius: int,
    nr_of_nodes: int,
    coordinates_set: list[Coordinates] | None = None,
    min_dist: int = 50,
) -> list[Coordinates]:

    coordinates = [] if coordinates_set is None else coordinates_set
    created_co = 0 if coordinates_set is None else len(coordinates_set)

    while created_co < nr_of_nodes:
        x_e = randint(x_c - radius, x_c + radius)
        y_e = randint(y_c - radius, y_c + radius)
        if (x_e - x_c) ** 2 + (y_e - y_c) ** 2 <= radius**2:
            co2 = (x_e, y_e, 0)
            if co2 not in coordinates and co2 != (x_c, y_c):
                greater_dist = True
                for co1 in coordinates:
                    dist = calculate_distance_simple((co1[0], co1[1], 0), co2)
                    if dist < min_dist:
                        greater_dist = False
                        break

                if greater_dist:
                    # coordinates.append(co2)
                    coordinates.append([co2[0], co2[1], 0])
                    created_co += 1

    return coordinates


def generate_coordinates_min_max(
    x_c: int,
    y_c: int,
    radius: int,
    nr_of_nodes: int,
    coordinates_set: list[Coordinates] | None = None,
    min_dist: int = 50,
) -> list[Coordinates]:

    coordinates = [] if coordinates_set is None else coordinates_set
    created_co = 0 if coordinates_set is None else len(coordinates_set)

    while created_co < nr_of_nodes:
        x_e = randint(x_c - radius, x_c + radius)
        y_e = randint(y_c - radius, y_c + radius)
        if (x_e - x_c) ** 2 + (y_e - y_c) ** 2 <= radius**2:
            co2 = (x_e, y_e, 0)
            if co2 not in coordinates and co2 != (x_c, y_c):
                greater_dist = True
                for co1 in coordinates:
                    dist = calculate_distance_simple((co1[0], co1[1], 0), co2)
                    if dist < min_dist:
                        greater_dist = False
                        break

                if greater_dist:
                    # coordinates.append(co2)
                    coordinates.append([co2[0], co2[1], 0])
                    created_co += 1

    return coordinates


def plot_coordinates(
    x_c: int,
    y_c: int,
    radius: int,
    coordnates: list[Coordinates],
    dir_path: str,
    selected_radius: int | None = None,
    show_figure: bool = False,
) -> None:
    max_radius = radius

    if selected_radius is not None:
        max_radius = radius if radius > selected_radius else selected_radius
    arr = np.zeros((x_c + max_radius + 1, y_c + max_radius + 1))

    # number_of_coords = len(coordnates)
    for point in coordnates:
        arr[point] = 1

    if selected_radius is not None:
        selected_range = Ellipse(
            xy=(x_c, y_c),
            width=2 * selected_radius,
            height=2 * selected_radius,
            angle=0.0,
        )
    lora_range = Ellipse(xy=(x_c, y_c), width=2 * radius, height=2 * radius, angle=0.0)

    _, axes = plt.subplots()
    axes.set_aspect("equal")
    # ax  = fig.add_subplot(111, aspect='equal')
    if selected_radius is not None:
        axes.add_artist(selected_range)
        selected_range.set_clip_box(axes.bbox)
        selected_range.set_alpha(0.3)
        selected_range.set_facecolor("gray")
    axes.add_artist(lora_range)
    lora_range.set_clip_box(axes.bbox)
    lora_range.set_alpha(0.3)
    lora_range.set_facecolor("green")

    axes.set_xlim(x_c - max_radius - 1, x_c + max_radius + 1)
    axes.set_ylim(y_c - max_radius - 1, y_c + max_radius + 1)

    point_size = 0.5
    annotations = []
    parent = plt.scatter(*zip(*coordnates), s=point_size, color="red")
    children = plt.scatter(*zip(*[(x_c, y_c)]), s=point_size, color="blue")
    # parent = plt.scatter(*zip(*coordnates), color='red')
    # children = plt.scatter(*zip(*[(xc, yc)]), color='blue')

    figure = plt.gcf()
    figure.set_size_inches(19, 10)

    plt.savefig(f"{dir_path}/coordinates.png", dpi=300)

    ann = axes.annotate("0", (x_c, y_c), fontsize=5)
    annotations.append(ann)
    for i in enumerate(coordnates):
        ann = axes.annotate(str(i[0] + 1), i[1], fontsize=5)
        annotations.append(ann)

    plt.savefig(f"{dir_path}/coordinates_with_ids.png", dpi=300)
    for ann in annotations:
        ann.set_fontsize(10)

    parent.set_sizes(parent.get_sizes() * 8)
    children.set_sizes(children.get_sizes() * 8)

    if show_figure:
        plt.show()


def plot_coordinates_for_scenarios(max_dist: float, dir_path: str, ts: int, show_figure: bool = False) -> None:
    nodes = coglobs.LIST_OF_NODES
    coordinates = {}
    min_x, min_y, max_x, max_y = [999999, 999999, -999999, -999999]
    for node_id in nodes:
        pos = nodes[node_id].position

        if pos[0] < min_x:
            min_x = pos[0]

        if pos[0] > max_x:
            max_x = pos[0]

        if pos[1] < min_y:
            min_y = pos[1]

        if pos[1] > max_y:
            max_y = pos[1]

        coordinates[node_id] = pos

    dist1 = calculate_distance_simple((0, 0, 0), (min_x, min_y, 0))
    dist2 = calculate_distance_simple((0, 0, 0), (max_x, max_y, 0))
    dist3 = calculate_distance_simple((min_x, min_y, 0), (max_x, max_y, 0))

    dist = dist1 if dist1 > dist2 else dist2
    dist = dist if dist > dist3 else dist3

    colors = ['black', 'seagreen', 'firebrick', 'darkorange', 'lightgrey', 'deepskyblue', 'goldenrod', 'olive', 'yellowgreen', 'darkolivegreen',
        'mediumturquoise', 'teal', 'steelblue', 'indigo', 'purple', 'crimson', 'indigo', 'yellow', 'lawngreen'
    ]

    arr = np.zeros((0 + math.ceil(dist) + 1, 0 + math.ceil(dist) + 1))

    # number_of_coords = len(coordnates)
    for node_id in coordinates:
        arr[coordinates[node_id]] = 1

    # if selected_radius is not None:
    #     selected_range = Ellipse(
    #         xy=(x_c, y_c),
    #         width=2 * selected_radius,
    #         height=2 * selected_radius,
    #         angle=0.0,
    #     )
    _, axes = plt.subplots()
    axes.set_aspect("equal")
    for node_id in coordinates:
        coords = coordinates[node_id]
        lora_range = Ellipse(xy=(coords[0], coords[1]), width=2 * max_dist, height=2 * max_dist, angle=0.0)
        axes.add_artist(lora_range)
        lora_range.set_clip_box(axes.bbox)
        lora_range.set_alpha(0.1)
        lora_range.set_facecolor(colors[node_id])
        lora_range.set_edgecolor(colors[node_id])

    # # ax  = fig.add_subplot(111, aspect='equal')
    # if selected_radius is not None:
    #     axes.add_artist(selected_range)
    #     selected_range.set_clip_box(axes.bbox)
    #     selected_range.set_alpha(0.3)
    #     selected_range.set_facecolor("gray")
    # axes.add_artist(lora_range)
    # lora_range.set_clip_box(axes.bbox)
    # lora_range.set_alpha(0.3)
    # lora_range.set_facecolor("green")

    axes.set_xlim(min_x - max_dist - 1, max_x + max_dist + 1)
    axes.set_ylim(min_y - max_dist - 1, max_y + max_dist + 1)

    point_size = 0.5
    annotations = []
    node_points = {}
    for node_id in coordinates:
        node_points[node_id] = plt.scatter(*zip(*[(coordinates[node_id][0], coordinates[node_id][1]) for node_id in coordinates]), s=point_size, color=colors[node_id])
    # children = plt.scatter(*zip(*[(x_c, y_c)]), s=point_size, color="blue")
    # # parent = plt.scatter(*zip(*coordnates), color='red')
    # # children = plt.scatter(*zip(*[(xc, yc)]), color='blue')

    figure = plt.gcf()
    figure.set_size_inches(19, 10)

    plt.savefig(f"{dir_path}/{ts}_coordinates.png", dpi=300)

    # ann = axes.annotate("0", (x_c, y_c), fontsize=5)
    # annotations.append(ann)
    for node_id in coordinates:
        ann = axes.annotate(str(node_id), (coordinates[node_id][0], coordinates[node_id][1]), fontsize=9, color=colors[node_id])
        annotations.append(ann)

    plt.savefig(f"{dir_path}/{ts}_coordinates_with_ids.png", dpi=300)
    for ann in annotations:
        ann.set_fontsize(10)

    # parent.set_sizes(parent.get_sizes() * 8)
    for node_id in node_points:
        node_points[node_id].set_sizes(node_points[node_id].get_sizes() * 8)

    if show_figure:
        plt.show()