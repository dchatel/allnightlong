<script lang="ts">
	import { appState, type Horizon } from '$lib/state.svelte';
	import { baseLayers, destination, lidarOverlay } from '$lib/mapLayers';
	import HorizonView from '$lib/components/HorizonView.svelte';
	import { fade } from 'svelte/transition';
	import 'leaflet/dist/leaflet.css';
	import type { Map as LeafletMap, Polyline } from 'leaflet';

	// Éditeur d'horizon en plein écran : dôme et bande liés, carte de l'emplacement avec la direction
	// survolée. On trace en glissant la souris ; « Annuler » revient en arrière tracé par tracé.
	let editor = $derived(appState.horizonEditor);
	let alt = $state<number[]>([]);
	let veg = $state<boolean[]>([]);
	let source = $state('');
	let minAltitude = $state<number | null>(null);
	let history = $state<{ alt: number[]; veg: boolean[] }[]>([]);
	let hoverAz = $state<number | null>(null);
	let computing = $state(false);
	let message = $state('');

	$effect(() => {
		if (!editor) return;
		const h = editor.horizon;
		alt = h ? [...h.alt] : Array(360).fill(0);
		veg = h ? [...h.veg] : Array(360).fill(false);
		source = h?.source ?? '';
		minAltitude = editor.minAltitude;
		history = [];
		message = '';
	});

	function remember() {
		history = [...history.slice(-30), { alt: [...alt], veg: [...veg] }];
	}

	// Un tracé à la main remplace la mesure : l'obstacle devient opaque et la source le signale
	function onedit(next: number[], touched: number[]) {
		alt = next;
		const v = [...veg];
		for (const i of touched) v[i] = false;
		veg = v;
		if (source && !source.includes('retouché')) source = `${source}, retouché à la main`;
		if (!source) source = 'Tracé à la main';
	}

	function undo() {
		const last = history.at(-1);
		if (!last) return;
		alt = last.alt;
		veg = last.veg;
		history = history.slice(0, -1);
	}

	function clear() {
		remember();
		alt = Array(360).fill(0);
		veg = Array(360).fill(false);
		source = 'Tracé à la main';
	}

	async function compute() {
		if (!editor) return;
		computing = true;
		message = 'Calcul depuis le LiDAR HD de l’IGN…';
		const result = await appState.lidarHorizon(editor.lat, editor.lon, editor.instrumentHeight);
		computing = false;
		if (!result) { message = ''; return; }
		remember();
		alt = result.alt;
		veg = result.veg;
		source = result.source;
		message = '';
	}

	function apply() {
		if (!editor) return;
		const horizon: Horizon | null = alt.some(a => a > 0) ? { alt, veg, source } : null;
		editor.onApply(horizon, minAltitude);
		appState.horizonEditor = null;
	}

	function close() {
		appState.horizonEditor = null;
	}

	function handleKeydown(e: KeyboardEvent) {
		if (!appState.horizonEditor) return;
		if (e.key === 'Escape') { e.stopPropagation(); close(); }
		if (e.key === 'z' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); undo(); }
	}

	// --- Carte de l'emplacement, avec la direction survolée ---
	let map: LeafletMap | null = null;
	let ray: Polyline | null = null;
	function initMap(node: HTMLElement) {
		let destroyed = false;
		import('leaflet').then((L) => {
			if (destroyed || !editor) return;
			const layers = baseLayers(L);
			map = L.map(node, { zoomControl: true, attributionControl: true }).setView([editor.lat, editor.lon], 19);
			layers['Photo aérienne'].addTo(map);
			const relief = lidarOverlay(L);
			L.control.layers(layers, { 'Relief LiDAR': relief }, { collapsed: false }).addTo(map);
			map.attributionControl.setPrefix(false);
			L.circleMarker([editor.lat, editor.lon], { radius: 6, color: '#fff', weight: 2, fillColor: '#e11d48', fillOpacity: 1 }).addTo(map);
			ray = L.polyline([], { color: '#a5b4fc', weight: 3, dashArray: '6 5' }).addTo(map);
		});
		return {
			destroy() {
				destroyed = true;
				map?.remove();
				map = null;
				ray = null;
			}
		};
	}
	// --- Carte sous le dôme : le dôme sert de loupe sur les alentours de l'instrument ---
	// Le bord du dôme correspond à `domeRadius` mètres au sol (l'échelle est libre : le dôme mesure des angles).
	let domeMap = $state(true);
	let domeRadius = $state(50);
	const RADII = [20, 50, 100, 200];
	function underMap(node: HTMLElement, params: { R: number; metres: number }) {
		let m: LeafletMap | null = null;
		let current = params;
		const zoomFor = (p: { R: number; metres: number }) =>
			Math.log2((156543.03392 * Math.cos(((editor?.lat ?? 0) * Math.PI) / 180) * Math.max(1, p.R)) / p.metres);
		const place = () => {
			if (!m || !editor) return;
			m.invalidateSize();
			m.setView([editor.lat, editor.lon], zoomFor(current), { animate: false });
		};
		import('leaflet').then((L) => {
			if (!editor || !node.isConnected) return;
			m = L.map(node, {
				zoomControl: false, attributionControl: false, dragging: false, scrollWheelZoom: false, doubleClickZoom: false,
				boxZoom: false, keyboard: false, touchZoom: false, zoomSnap: 0, maxZoom: 22
			});
			baseLayers(L)['Photo aérienne'].addTo(m);
			place();
		});
		return {
			update(next: { R: number; metres: number }) { current = next; place(); },
			destroy() { m?.remove(); m = null; }
		};
	}

	$effect(() => {
		if (!ray || !editor) return;
		ray.setLatLngs(hoverAz == null ? [] : [[editor.lat, editor.lon], destination(editor.lat, editor.lon, hoverAz + 0.5, 80)]);
	});
</script>

<svelte:window onkeydowncapture={handleKeydown} />

{#if editor}
	<div transition:fade={{ duration: 120 }} class="fixed inset-0 z-70 bg-[#121214] flex flex-col">
		<div class="h-14 border-b border-[#333] bg-[#1a1a1d] px-6 flex items-center justify-between shrink-0 select-none">
			<div class="flex items-center gap-3 min-w-0">
				<span class="text-xl">⛰</span>
				<h2 class="text-sm font-bold uppercase tracking-widest text-white">Horizon — {editor.label || 'nouveau lieu'}</h2>
				<span class="text-xs text-surface-400 truncate">{source || 'Aucun horizon'}</span>
			</div>
			<div class="flex items-center gap-2">
				<button type="button" onclick={compute} disabled={computing} class="btn-secondary text-xs disabled:opacity-40">
					{computing ? 'Calcul…' : 'Calculer depuis le LiDAR HD'}
				</button>
				<button type="button" onclick={undo} disabled={!history.length} class="btn-secondary text-xs disabled:opacity-40" title="Ctrl+Z">↶ Annuler</button>
				<button type="button" onclick={clear} class="btn-secondary text-xs">Tout effacer</button>
				<button type="button" onclick={close} class="btn-secondary text-xs">Fermer sans garder</button>
				<button type="button" onclick={apply} class="btn-primary text-xs">Valider l’horizon</button>
			</div>
		</div>

		<div class="flex-1 min-h-0 grid grid-cols-[minmax(0,1fr)_minmax(0,1.3fr)] gap-6 p-6">
			<!-- Dôme : le ciel vu de dessus, orienté comme la carte -->
			<div class="flex flex-col gap-2 min-w-0 min-h-0">
				<div class="flex items-center justify-between gap-3 text-[11px]">
					<span class="uppercase font-bold text-surface-400">Vu de dessus (nord en haut)</span>
					<div class="flex items-center gap-3 text-surface-300">
						<label class="flex items-center gap-1.5"><input type="checkbox" bind:checked={domeMap} /> photo aérienne dessous</label>
						{#if domeMap}
							<label class="flex items-center gap-1.5" title="Distance au sol représentée par le bord du dôme">
								rayon
								<select class="form-input py-0.5" style="width: 5.5rem" bind:value={domeRadius}>
									{#each RADII as r (r)}<option value={r}>{r} m</option>{/each}
								</select>
							</label>
						{/if}
					</div>
				</div>
				<div class="flex-1 min-h-0">
					{#snippet aerial(R: number)}
						<div use:underMap={{ R, metres: domeRadius }} class="w-full h-full bg-[#e5e3df]"></div>
					{/snippet}
					<HorizonView mode="dome" {alt} {veg} {minAltitude} maxAltitude={90} editable bind:hoverAz onedit={onedit} onstrokestart={remember}
						underlay={domeMap ? aerial : undefined} />
				</div>
			</div>

			<div class="flex flex-col gap-4 min-w-0 min-h-0">
				<div class="flex flex-col gap-2">
					<span class="text-[11px] uppercase font-bold text-surface-400">Tour d'horizon (0 à 360°)</span>
					<HorizonView mode="strip" {alt} {veg} {minAltitude} editable bind:hoverAz onedit={onedit} onstrokestart={remember} />
				</div>

				<div class="flex flex-wrap items-center gap-x-6 gap-y-2 text-[11px] text-surface-300">
					<span class="flex items-center gap-1.5"><span class="legend solid"></span> bâti, mur, relief</span>
					<span class="flex items-center gap-1.5"><span class="legend veg"></span> végétation (en partie transparente)</span>
					<label class="flex items-center gap-2">
						<span class="legend min"></span> hauteur minimale
						<input type="number" min="0" max="60" step="1" class="form-input py-0.5" style="width: 4.5rem" value={minAltitude ?? ''}
							oninput={(e) => (minAltitude = e.currentTarget.value === '' ? null : Number(e.currentTarget.value))} placeholder="—" />°
					</label>
				</div>
				<p class="text-[11px] text-surface-400 leading-relaxed">
					Glissez la souris dans le dôme ou dans la bande pour tracer l'horizon : chaque direction survolée prend la hauteur du
					pointeur. Un tracé remplace la mesure LiDAR à cet endroit. Survolez une direction pour la voir sur la carte.
				</p>
				{#if message}<p class="text-[11px] text-indigo-300">{message}</p>{/if}

				<div class="relative flex-1 min-h-48 rounded-lg overflow-hidden border border-[#333]">
					<div use:initMap class="absolute inset-0 bg-[#e5e3df]"></div>
				</div>
			</div>
		</div>
	</div>
{/if}

<style>
	.legend { display: inline-block; width: 14px; height: 10px; border-radius: 2px; }
	.legend.solid { background: #4b4b55; }
	.legend.veg { background: repeating-linear-gradient(45deg, #2f4a36 0 3px, #8fc79b 3px 5px); }
	.legend.min { height: 0; border-top: 2px dashed #c98500; }
</style>
