// Fonds de carte communs à la fenêtre du lieu et à l'éditeur d'horizon.
// Photo aérienne et relief LiDAR viennent de la Géoplateforme de l'IGN (données ouvertes, sans clé, France).
import type * as Leaflet from 'leaflet';

const IGN_ATTRIBUTION = '© <a href="https://www.ign.fr/">IGN</a>';
const OSM_ATTRIBUTION = '© <a href="https://www.openstreetmap.org/copyright">contributeurs OpenStreetMap</a>';

export function baseLayers(L: typeof Leaflet) {
	return {
		Plan: L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
			maxZoom: 21,
			maxNativeZoom: 19,
			attribution: OSM_ATTRIBUTION
		}),
		'Photo aérienne': L.tileLayer(
			'https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=ORTHOIMAGERY.ORTHOPHOTOS' +
				'&STYLE=normal&TILEMATRIXSET=PM_0_19&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/jpeg',
			{ maxZoom: 21, maxNativeZoom: 19, attribution: IGN_ATTRIBUTION }
		)
	};
}

// Estompage du relief LiDAR HD (bâtiments, murs, arbres) : se superpose à l'un ou l'autre fond
export function lidarOverlay(L: typeof Leaflet) {
	return L.tileLayer.wms('https://data.geopf.fr/wms-r', {
		layers: 'IGNF_LIDAR-HD_MNS_ELEVATION.ELEVATIONGRIDCOVERAGE.SHADOW',
		format: 'image/png',
		transparent: true,
		opacity: 0.55,
		maxZoom: 21,
		attribution: IGN_ATTRIBUTION
	});
}

// Point situé à une distance (m) et un azimut (°) d'un autre : pour tracer la direction survolée
export function destination(lat: number, lon: number, azimuth: number, metres: number): [number, number] {
	const a = (azimuth * Math.PI) / 180;
	return [lat + (metres * Math.cos(a)) / 111_320, lon + (metres * Math.sin(a)) / (111_320 * Math.cos((lat * Math.PI) / 180))];
}
