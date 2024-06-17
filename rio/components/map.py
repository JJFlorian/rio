from __future__ import annotations

from typing import Literal, final

from uniserde import JsonDoc

from .fundamental_component import FundamentalComponent

__all__ = ["Map"]

BaseLayer = Literal["ROADMAP", "SATELLITE", "TERRAIN"]


@final
class Map(FundamentalComponent):
    """
    Displays a map with markers.

    ## Attributes

    `base_layer`: The baselayer of the map. Options are 'ROADMAP', 'SATELLITE', 'TERRAIN'.

    `center`: The initial center of the map [latitude, longitude].

    `zoom`: The initial zoom level of the map.

    `markers`: A list of markers to be displayed on the map. Each marker is specified
        by a dictionary containing `position` (latitude and longitude) and `popup` text.

    `corner_radius`: The corner radius of the plot

    ## Examples

    ```python
    class MyComponent(rio.Component):
        def build(self) -> rio.Component:
            markers = [
                {"position": (51.505, -0.09), "popup": "Marker 1"},
                {"position": (51.515, -0.1), "popup": "Marker 2"},
            ]
            return rio.Map(center=(51.505, -0.09), zoom=13, markers=markers)
    ```
    """

    base_layer: BaseLayer
    center: tuple[float, float]
    zoom: int
    markers: list[dict[str, tuple[float, float] | str]]
    corner_radius: float | tuple[float, float, float, float] | None

    def __init__(
        self,
        center: tuple[float, float],
        zoom: int,
        markers: list[dict[str, tuple[float, float] | str]],
        *,
        base_layer: BaseLayer = "TERRAIN",
        corner_radius: float | tuple[float, float, float, float] | None = None,
        key: str | int | None = None,
        margin: float | None = None,
        margin_x: float | None = None,
        margin_y: float | None = None,
        margin_left: float | None = None,
        margin_top: float | None = None,
        margin_right: float | None = None,
        margin_bottom: float | None = None,
        width: Literal["natural", "grow"] | float = "natural",
        height: Literal["natural", "grow"] | float = "natural",
        align_x: float | None = None,
        align_y: float | None = None,
    ):
        super().__init__(
            key=key,
            margin=margin,
            margin_x=margin_x,
            margin_y=margin_y,
            margin_left=margin_left,
            margin_top=margin_top,
            margin_right=margin_right,
            margin_bottom=margin_bottom,
            width=width,
            height=height,
            align_x=align_x,
            align_y=align_y,
        )
        self.base_layer = base_layer
        self.center = center
        self.zoom = zoom
        self.markers = markers

        if corner_radius is None:
            self.corner_radius = self.session.theme.corner_radius_small
        else:
            self.corner_radius = corner_radius

    def _custom_serialize(self) -> JsonDoc:
        # Corner radius
        if isinstance(self.corner_radius, (int, float)):
            corner_radius = (self.corner_radius,) * 4
        else:
            corner_radius = self.corner_radius

        return {
            "base_layer": self.base_layer,
            "center": self.center,
            "zoom": self.zoom,
            "markers": self.markers,
            "corner_radius": corner_radius,
        }


Map._unique_id = "Map-builtin"
