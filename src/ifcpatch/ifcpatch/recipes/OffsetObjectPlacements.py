# IfcPatch - IFC patching utiliy
# Copyright (C) 2020, 2021 Dion Moult <dion@thinkmoult.com>
#
# This file is part of IfcPatch.
#
# IfcPatch is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# IfcPatch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with IfcPatch.  If not, see <http://www.gnu.org/licenses/>.

import math
import numpy as np
import ifcopenshell
import ifcopenshell.util.placement

class Patcher:
    def __init__(self, src, file, logger, args=None):
        self.src = src
        self.file = file
        self.logger = logger
        self.args = args

    def patch(self):
        absolute_placements = []

        for product in self.file.by_type('IfcProduct'):
            if not product.ObjectPlacement:
                continue
            absolute_placement = self.get_absolute_placement(product.ObjectPlacement)
            if absolute_placement.is_a('IfcLocalPlacement'):
                absolute_placements.append(absolute_placement)
        absolute_placements = set(absolute_placements)

        angle = float(self.args[3])
        transformation = self.z_rotation_matrix(math.radians(angle)) if angle else np.eye(4)
        transformation[0][3] += float(self.args[0])
        transformation[1][3] += float(self.args[1])
        transformation[2][3] += float(self.args[2])

        for placement in absolute_placements:
            placement.RelativePlacement = self.get_relative_placement(
                transformation @ ifcopenshell.util.placement.get_local_placement(placement)
            )

    def get_absolute_placement(self, object_placement):
        if object_placement.PlacementRelTo:
            return self.get_absolute_placement(object_placement.PlacementRelTo)
        return object_placement

    def z_rotation_matrix(self, angle):
        return [
            [math.cos(angle), -math.sin(angle), 0., 0.],
            [math.sin(angle), math.cos(angle), 0., 0.],
            [0., 0., 1., 0.],
            [0., 0., 0., 1.],
        ]

    def get_relative_placement(self, m):
        x = np.array((m[0][0], m[1][0], m[2][0]))
        z = np.array((m[0][2], m[1][2], m[2][2]))
        o = np.array((m[0][3], m[1][3], m[2][3]))
        object_matrix = ifcopenshell.util.placement.a2p(o, z, x)
        return self.create_ifc_axis_2_placement_3d(
            object_matrix[:, 3][0:3],
            object_matrix[:, 2][0:3],
            object_matrix[:, 0][0:3],
        )

    def create_ifc_axis_2_placement_3d(self, point, up, forward):
        return self.file.createIfcAxis2Placement3D(
            self.file.createIfcCartesianPoint(point.tolist()),
            self.file.createIfcDirection(up.tolist()),
            self.file.createIfcDirection(forward.tolist()),
        )
