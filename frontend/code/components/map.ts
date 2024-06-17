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
};

let fetchLeafletPromise: Promise<void> | null = null;

function withLeaflet(callback: () => void): void {
    // If Leaflet is already loaded just call the callback
    if (typeof window['L'] !== 'undefined') {
        callback();
        return;
    }

    // If Leaflet is currently being fetched, wait for it to finish
    if (fetchLeafletPromise !== null) {
        fetchLeafletPromise.then(callback);
        return;
    }

    // Otherwise fetch Leaflet and call the callback when it's done
    console.debug('Fetching leaflet.js and leaflet.css');
    let script = document.createElement('script');
    script.src = 'https://unpkg.com/leaflet/dist/leaflet.js';
    script.async = true;

    let link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://unpkg.com/leaflet/dist/leaflet.css';

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

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-map');
        return element;
    }

    updateElement(
        deltaState: MapState,
        latentComponents: Set<ComponentBase>
    ): void {
        if (deltaState.center !== undefined && deltaState.zoom !== undefined) {
            const { center, zoom, markers } = deltaState;

            withLeaflet(() => {
                this.renderMap(center, zoom, markers);
            });
        }
        if (deltaState.corner_radius !== undefined) {
            let [topLeft, topRight, bottomRight, bottomLeft] =
                deltaState.corner_radius;

            this.element.style.borderRadius = `${topLeft}rem ${topRight}rem ${bottomRight}rem ${bottomLeft}rem`;
        }
    }

    renderMap(center: LatLngTuple, zoom: number, markers: MarkerData[]): void {
        console.log('Rendering map...');
        if (!this.map) {
            console.log('Initializing new map...');
            this.map = L.map(this.element, {
                center: center,
                zoom: zoom,
                layers: [
                    L.tileLayer(
                        'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
                        {
                            attribution:
                                '&copy; <a href="https://osm.org/copyright">OpenStreetMap</a> contributors',
                        }
                    ),
                ],
            });

            // Ensure map container is interactive
            this.map.getContainer().style.pointerEvents = 'auto';
        } else {
            console.log('Updating existing map...');
            this.map.setView(center, zoom);
        }

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
