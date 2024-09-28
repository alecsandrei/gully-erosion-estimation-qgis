from __future__ import annotations

import typing as t
import itertools

from qgis.PyQt.QtCore import Qt
from qgis.core import (
    QgsVectorLayer,
    QgsGeometry,
    QgsLineString
)
from qgis.gui import QgsRubberBand
from qgis.analysis import (
    QgsVectorLayerDirector,
    QgsNetworkStrategy,
    QgsGraphAnalyzer,
    QgsGraphBuilder
)
from qgis.utils import iface

from gully_erosion_estimation_qgis.geometry import endpoints_gen
from gully_erosion_estimation_qgis.utils import geometries_to_layer

if t.TYPE_CHECKING:
    from qgis.core import QgsPointXY


def build_graph(
    start_points: list[QgsGeometry],
    lines: QgsVectorLayer,
    destination_points: list[QgsGeometry]
):
    director = QgsVectorLayerDirector(
        lines, -1, '', '', '', QgsVectorLayerDirector.Direction.DirectionBoth
    )
    builder = QgsGraphBuilder(lines.crs())

    start_points_as_xy = map(QgsGeometry.asPoint, start_points)
    destination_points_as_xy = map(QgsGeometry.asPoint, destination_points)
    tied_points = director.makeGraph(
        builder, itertools.chain(start_points_as_xy, destination_points_as_xy)
    )
    tied_start_points = tied_points[:len(start_points)]
    tied_end_points = tied_points[len(start_points):]
    routes = []
    for tied_start_point in tied_start_points:
        print(tied_start_point)
        graph = builder.graph()
        start_idx = graph.findVertex(tied_start_point)
        shortest_route = None
        for tied_end_point in tied_end_points:
            end_idx = graph.findVertex(tied_end_point)
            tree, _ = QgsGraphAnalyzer.dijkstra(graph, start_idx, 0)
            graph = builder.graph()
            route = [graph.vertex(end_idx).point()]

            replace = True
            while end_idx != start_idx:
                if tree[end_idx] == -1:
                    print('No route?')
                    replace = False
                    break
                end_idx = graph.edge(tree[end_idx]).fromVertex()
                route.insert(0, graph.vertex(end_idx).point())
                if (
                    shortest_route is not None
                    and len(route) >= len(shortest_route)
                ):
                    replace = False
                    break

            if replace:
                shortest_route = route

        if shortest_route:
            routes.append(shortest_route)

    for route in routes:
        yield QgsGeometry.fromPolylineXY(route)
