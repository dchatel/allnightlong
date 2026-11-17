<script lang="ts">
	import { appState } from '$lib/state.svelte';
	import { fade } from 'svelte/transition';
	import 'leaflet/dist/leaflet.css';
	import type { Map as LeafletMap, Marker } from 'leaflet';

	const TILE_URL = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
	const TILE_ATTRIBUTION = '© <a href="https://www.openstreetmap.org/copyright">contributeurs OpenStreetMap</a>';
	const FRANCE = { lat: 46.6, lon: 2.4, zoom: 6 };
	const PLACE_ZOOM = 17;

	// Repère dessiné en SVG : les icônes PNG de Leaflet se perdent au moment de la compilation
	const PIN_SVG = `<svg viewBox="0 0 24 36" width="28" height="42"><path d="M12 0C5.4 0 0 5.4 0 12c0 9 12 24 12 24s12-15 12-24C24 5.4 18.6 0 12 0z" fill="#e11d48" stroke="#fff" stroke-width="1.5"/><circle cx="12" cy="12" r="4.5" fill="#fff"/></svg>`;

	let editor = $derived(appState.locationEditor);
	let form = $state<any>(null);
	let labelTouched = $state(false);
	let address = $state('');
	let lookupStatus = $state('');
	let searchQuery = $state('');
	let searchResults = $state<{ address: string; lat: number; lon: number }[]>([]);
	let saving = $state(false);

	let leaflet: typeof import('leaflet') | null = null;
	let map: LeafletMap | null = null;
	let marker: Marker | null = null;
	// Ignore les réponses d'une recherche d'adresse dépassée par un clic plus récent
	let lookupId = 0;

	// Copie de travail à chaque ouverture
	$effect(() => {
		if (editor) {
			form = { ...editor.form };
			labelTouched = Boolean(editor.form.label);
			address = '';
			lookupStatus = '';
			searchQuery = '';
			searchResults = [];
		} else {
			form = null;
		}
	});

	let hasPoint = $derived(form && Number.isFinite(form.lat) && Number.isFinite(form.lon));
	let canSave = $derived(hasPoint && form.label.trim() !== '' && !saving);

	function round(value: number, digits: number) {
		const factor = 10 ** digits;
		return Math.round(value * factor) / factor;
	}

	function placeMarker(lat: number, lon: number) {
		if (!leaflet || !map) return;
		if (marker) {
			marker.setLatLng([lat, lon]);
		} else {
			const icon = leaflet.divIcon({ html: PIN_SVG, className: '', iconSize: [28, 42], iconAnchor: [14, 42] });
			marker = leaflet.marker([lat, lon], { icon, draggable: true }).addTo(map);
			marker.on('dragend', () => {
				const position = marker!.getLatLng();
				setPoint(position.lat, position.lng);
			});
		}
	}

	// Nouveau point : coordonnées, repère, puis adresse et altitude demandées en ligne
	async function setPoint(lat: number, lon: number) {
		form.lat = round(lat, 5);
		form.lon = round(lon, 5);
		placeMarker(form.lat, form.lon);
		await lookup();
	}

	async function lookup() {
		const id = ++lookupId;
		lookupStatus = 'Recherche de l’adresse…';
		const point = { lat: form.lat, lon: form.lon };
		const [place, elevation] = await Promise.all([
			appState.geo('reverse', point),
			appState.geo('elevation', point)
		]);
		if (id !== lookupId || !form) return;

		address = place?.address ?? '';
		if (place?.place && !labelTouched) form.label = place.place;
		if (elevation?.elevationM != null) form.elevationM = Math.round(elevation.elevationM);
		lookupStatus = place || elevation ? '' : 'Adresse et altitude indisponibles (pas de connexion ?). Le lieu peut quand même être enregistré.';
	}

	// Saisie directe des coordonnées : le repère suit, sans relancer de recherche à chaque frappe
	function onCoordsInput() {
		if (!hasPoint) return;
		placeMarker(form.lat, form.lon);
		map?.panTo([form.lat, form.lon]);
	}

	async function search() {
		const query = searchQuery.trim();
		if (!query) return;
		const results = await appState.geo('search', { q: query });
		searchResults = results ?? [];
		if (results === null) lookupStatus = 'Recherche indisponible (pas de connexion ?).';
		else if (results.length === 0) lookupStatus = 'Aucun résultat.';
		else lookupStatus = '';
	}

	function chooseResult(result: { lat: number; lon: number }) {
		searchResults = [];
		map?.setView([result.lat, result.lon], PLACE_ZOOM);
		setPoint(result.lat, result.lon);
	}

	function initMap(node: HTMLElement) {
		let destroyed = false;

		import('leaflet').then((L) => {
			if (destroyed) return;
			leaflet = L;

			const reference = hasPoint ? form : appState.locations[0];
			const center = reference ? [reference.lat, reference.lon] : [FRANCE.lat, FRANCE.lon];
			const zoom = hasPoint ? PLACE_ZOOM : reference ? 12 : FRANCE.zoom;

			map = L.map(node).setView(center as [number, number], zoom);
			L.tileLayer(TILE_URL, { maxZoom: 19, attribution: TILE_ATTRIBUTION }).addTo(map);
			map.attributionControl.setPrefix(false);
			map.on('click', (e) => setPoint(e.latlng.lat, e.latlng.lng));

			if (hasPoint) {
				placeMarker(form.lat, form.lon);
				// Lieu à créer depuis d'anciennes coordonnées : proposer libellé et altitude
				if (!form.id) lookup();
			}
		});

		return {
			destroy() {
				destroyed = true;
				map?.remove();
				map = null;
				marker = null;
			}
		};
	}

	async function save() {
		if (!canSave) return;
		saving = true;
		await appState.saveLocation({
			...form,
			label: form.label.trim(),
			elevationM: Number.isFinite(form.elevationM) ? form.elevationM : null,
			bortle: Number.isFinite(form.bortle) ? form.bortle : null
		});
		saving = false;
	}

	// Phase de capture : Échap ferme ce lieu sans atteindre le rapport ouvert en dessous
	function handleKeydown(e: KeyboardEvent) {
		if (e.key !== 'Escape' || !appState.locationEditor) return;
		e.stopPropagation();
		appState.closeLocationEditor();
	}
</script>

<svelte:window onkeydowncapture={handleKeydown} />

{#if editor && form}
	<div transition:fade={{ duration: 150 }} class="fixed inset-0 bg-black/70 backdrop-blur-sm z-60 flex items-center justify-center p-8">
		<div class="bg-[#161619] border border-[#333] rounded-2xl w-[85vw] h-[80vh] flex flex-col overflow-hidden shadow-2xl">
			<div class="h-14 border-b border-[#333] bg-[#1a1a1d] px-6 flex items-center justify-between shrink-0 select-none">
				<div class="flex items-center space-x-3">
					<span class="text-xl">📍</span>
					<h2 class="text-sm font-bold uppercase tracking-widest text-white">
						{form.id ? 'Modifier le lieu' : 'Nouveau lieu'}
					</h2>
				</div>
				<button
					onclick={() => appState.closeLocationEditor()}
					class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-surface-800 text-surface-400 hover:text-white transition-colors text-lg"
				>✕</button>
			</div>

			<div class="flex-1 min-h-0 flex">
				<!-- Carte -->
				<div class="flex-1 relative">
					<div use:initMap class="absolute inset-0 bg-[#e5e3df]"></div>
					<form
						onsubmit={(e) => { e.preventDefault(); search(); }}
						class="absolute top-3 left-14 right-3 z-1000 max-w-md"
					>
						<input
							type="search"
							class="form-input w-full shadow-lg"
							placeholder="Rechercher une adresse ou une commune, puis Entrée"
							bind:value={searchQuery}
						/>
						{#if searchResults.length}
							<ul class="mt-1 bg-[#1e1e21] border border-[#333] rounded-lg overflow-hidden shadow-lg">
								{#each searchResults as result}
									<li>
										<button type="button" onclick={() => chooseResult(result)} class="w-full text-left text-xs text-white px-3 py-2 hover:bg-[#2a2a2e]">
											{result.address}
										</button>
									</li>
								{/each}
							</ul>
						{/if}
					</form>
				</div>

				<!-- Informations du lieu -->
				<div class="w-80 shrink-0 border-l border-[#333] p-5 flex flex-col gap-4 overflow-y-auto">
					{#if !hasPoint}
						<p class="text-xs text-indigo-300">Cliquez sur la carte à l'endroit de l'observation. Le repère peut ensuite être déplacé.</p>
					{/if}
					<div>
						<label for="loc-label" class="block text-[10px] text-surface-400 mb-1">Libellé (modifiable)</label>
						<input id="loc-label" type="text" class="form-input" bind:value={form.label} oninput={() => (labelTouched = true)} placeholder="Jardin, gîte, club…" />
					</div>
					<div>
						<span class="block text-[10px] text-surface-400 mb-1">Adresse détectée</span>
						<span class="block text-xs text-surface-200 min-h-4">{address || '—'}</span>
					</div>
					<div class="grid grid-cols-2 gap-2">
						<div>
							<label for="loc-lat" class="block text-[10px] text-surface-400 mb-1">Latitude</label>
							<input id="loc-lat" type="number" step="0.00001" class="form-input" bind:value={form.lat} oninput={onCoordsInput} />
						</div>
						<div>
							<label for="loc-lon" class="block text-[10px] text-surface-400 mb-1">Longitude</label>
							<input id="loc-lon" type="number" step="0.00001" class="form-input" bind:value={form.lon} oninput={onCoordsInput} />
						</div>
						<div>
							<label for="loc-elevation" class="block text-[10px] text-surface-400 mb-1">Altitude (m)</label>
							<input id="loc-elevation" type="number" class="form-input" bind:value={form.elevationM} placeholder="auto" />
						</div>
						<div>
							<label for="loc-bortle" class="block text-[10px] text-surface-400 mb-1">Bortle par défaut</label>
							<input id="loc-bortle" type="number" step="0.5" min="1" max="9" class="form-input" bind:value={form.bortle} />
						</div>
					</div>
					<div>
						<label for="loc-notes" class="block text-[10px] text-surface-400 mb-1">Notes</label>
						<textarea id="loc-notes" class="form-input min-h-20 resize-none py-2" bind:value={form.notes}></textarea>
					</div>
					{#if lookupStatus}
						<p class="text-[11px] text-surface-400">{lookupStatus}</p>
					{/if}
					<div class="mt-auto flex justify-end gap-2">
						<button onclick={() => appState.closeLocationEditor()} class="btn-secondary text-xs">Annuler</button>
						<button onclick={save} disabled={!canSave} class="btn-primary text-xs disabled:opacity-40">Enregistrer</button>
					</div>
				</div>
			</div>
		</div>
	</div>
{/if}
