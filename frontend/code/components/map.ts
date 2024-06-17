import { ComponentBase, ComponentState } from './componentBase';

type LatLngTuple = [number, number];

type MarkerData = {
    position: LatLngTuple;
    popup: string;
};

type MapState = ComponentState & {
    _type_: 'Map-builtin';
    center: LatLngTuple;
    zoom: number;
    markers: MarkerData[];
    corner_radius?: [number, number, number, number];
    base_layer: 'ROADMAP' | 'SATELLITE' | 'TERRAIN';
};

let fetchLeafletPromise: Promise<void> | null = null;

function withLeaflet(callback: () => void): void {
    if (typeof window['L'] !== 'undefined') {
        callback();
        return;
    }

    if (fetchLeafletPromise !== null) {
        fetchLeafletPromise.then(callback);
        return;
    }

    console.debug('Fetching leaflet.js and leaflet.css');
    let script = document.createElement('script');
    script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
    script.integrity = 'sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=';
    script.crossOrigin = '';
    script.async = true;

    let link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
    link.integrity = 'sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=';
    link.crossOrigin = '';

    fetchLeafletPromise = new Promise((resolve) => {
        script.onload = () => {
            resolve(null);
        };
        document.head.appendChild(script);
        document.head.appendChild(link);
    }).then(callback);
}

export class MapComponent extends ComponentBase {
    state: Required<MapState>;
    map: L.Map | null = null;
    currentBaseLayer: L.TileLayer | null = null;

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.id = 'map'; // Set the ID for the map element
        element.classList.add('rio-map');
        return element;
    }

    updateElement(
        deltaState: MapState,
        latentComponents: Set<ComponentBase>
    ): void {
        if (
            deltaState.center !== undefined &&
            deltaState.zoom !== undefined &&
            deltaState.base_layer !== undefined
        ) {
            const { center, zoom, markers, base_layer } = deltaState;

            withLeaflet(() => {
                this.renderMap(center, zoom, markers, base_layer);
            });
        }
        if (deltaState.corner_radius !== undefined) {
            let [topLeft, topRight, bottomRight, bottomLeft] =
                deltaState.corner_radius;

            this.element.style.borderRadius = `${topLeft}rem ${topRight}rem ${bottomRight}rem ${bottomLeft}rem`;
        }
    }

    renderMap(
        center: LatLngTuple,
        zoom: number,
        markers: MarkerData[],
        base_layer: 'ROADMAP' | 'SATELLITE' | 'TERRAIN'
    ): void {
        console.log('Rendering map...');
        const baseLayers: { [key: string]: string } = {
            ROADMAP:
                'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
            SATELLITE:
                'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            TERRAIN:
                'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
        };

        const baseLayerAttributions: { [key: string]: string } = {
            ROADMAP:
                '&copy; <a href="https://www.esri.com/en-us/home">Esri</a>',
            SATELLITE:
                '&copy; <a href="https://www.esri.com/en-us/home">Esri</a>',
            TERRAIN:
                '&copy; <a href="https://www.esri.com/en-us/home">Esri</a>',
        };

        if (!this.map) {
            console.log('Initializing new map...');
            this.map = L.map(this.element, {
                center: center,
                zoom: zoom,
                layers: [],
            });

            // Ensure map container is interactive
            this.map.getContainer().style.pointerEvents = 'auto';
        } else {
            console.log('Updating existing map...');
            this.map.setView(center, zoom);
        }

        // Update base layer
        if (this.currentBaseLayer) {
            this.map.removeLayer(this.currentBaseLayer);
        }
        this.currentBaseLayer = L.tileLayer(baseLayers[base_layer], {
            attribution: baseLayerAttributions[base_layer],
        }).addTo(this.map);

        // Clear existing markers
        this.map.eachLayer((layer) => {
            if (layer instanceof L.Marker) {
                this.map!.removeLayer(layer);
            }
        });

        // Add markers
        markers.forEach((marker) => {
            const { position, popup } = marker;
            L.marker(position).addTo(this.map!).bindPopup(popup);
        });

        // Trigger map resize
        this.updateMapLayout();
    }

    updateMapLayout(): void {
        if (this.map) {
            this.map.invalidateSize();
        }
    }
}
