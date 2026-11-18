<script lang="ts">
	import { appState } from '$lib/state.svelte';
	import { fade } from 'svelte/transition';
	import HorizonView from '$lib/components/HorizonView.svelte';

	// Liste des lieux. Un lieu est un emplacement d'instrument : deux coins du jardin font deux lieux.
	let sessionsByLocation = $derived.by(() => {
		const counts = new Map<number, number>();
		for (const o of appState.observations) if (o.locationId) counts.set(o.locationId, (counts.get(o.locationId) ?? 0) + 1);
		return counts;
	});

	function close() {
		appState.showLocations = false;
	}

	function handleKeydown(e: KeyboardEvent) {
		// La fiche d'un lieu ou l'éditeur d'horizon, ouverts par-dessus, ferment d'abord
		if (e.key !== 'Escape' || !appState.showLocations || appState.locationEditor || appState.horizonEditor) return;
		e.stopPropagation();
		close();
	}
</script>

<svelte:window onkeydowncapture={handleKeydown} />

{#if appState.showLocations}
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div transition:fade={{ duration: 150 }} onclick={close} class="fixed inset-0 bg-black/70 backdrop-blur-sm z-60 flex items-center justify-center p-8">
		<div onclick={(e) => e.stopPropagation()} class="bg-[#161619] border border-[#333] rounded-2xl w-full max-w-4xl max-h-[85vh] flex flex-col overflow-hidden shadow-2xl">
			<div class="h-14 border-b border-[#333] bg-[#1a1a1d] px-6 flex items-center justify-between shrink-0 select-none">
				<div class="flex items-center space-x-3">
					<span class="text-xl">📍</span>
					<h2 class="text-sm font-bold uppercase tracking-widest text-white">Lieux d'observation</h2>
				</div>
				<div class="flex items-center gap-2">
					<button type="button" onclick={() => appState.openLocationEditor()} class="btn-primary text-xs">+ Nouveau lieu</button>
					<button onclick={close} class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-surface-800 text-surface-400 hover:text-white transition-colors text-lg">✕</button>
				</div>
			</div>

			<div class="flex-1 overflow-y-auto p-6 space-y-3">
				{#if appState.locations.length === 0}
					<p class="text-sm text-surface-400 text-center py-10">Aucun lieu. « + Nouveau lieu » permet d'en placer un sur la carte.</p>
				{/if}
				{#each appState.locations as location (location.id)}
					<button
						type="button"
						onclick={() => appState.openLocationEditor({ ...location })}
						class="w-full text-left bg-[#1e1e21] border border-[#2a2a2d] hover:border-indigo-500 rounded-lg p-4 grid grid-cols-[minmax(0,14rem)_minmax(0,1fr)] gap-5 items-center transition-colors"
					>
						<div class="min-w-0">
							<span class="block text-sm font-bold text-white truncate">{location.label}</span>
							<span class="block text-[11px] text-surface-400">{location.lat.toFixed(5)} / {location.lon.toFixed(5)}</span>
							<span class="block text-[11px] text-surface-400">
								{[location.bortle != null ? `Bortle ${location.bortle}` : '', location.elevationM != null ? `${location.elevationM} m` : '',
									`${sessionsByLocation.get(location.id!) ?? 0} observation(s)`].filter(Boolean).join(' · ')}
							</span>
						</div>
						<div class="min-w-0 pointer-events-none">
							{#if location.horizon}
								<HorizonView mode="strip" alt={location.horizon.alt} veg={location.horizon.veg} minAltitude={location.minAltitude} />
							{:else}
								<span class="text-[11px] text-surface-500">Horizon non renseigné</span>
							{/if}
						</div>
					</button>
				{/each}
			</div>
		</div>
	</div>
{/if}
