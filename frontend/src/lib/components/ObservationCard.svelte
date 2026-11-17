<script lang="ts">
	import { appState, formatDate, type ObservationTarget } from '$lib/state.svelte';
	import { convertFileSrc } from '@tauri-apps/api/core';

	// targetId : cible dont on montre les poses (fiche cible) ; sinon la première de l'observation
	let { obs, targetId = null }: { obs: any; targetId?: number | null } = $props();

	function displayUrl(imageUrl: string) {
		if (!imageUrl) return '';
		if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://')) return imageUrl;
		try {
			return convertFileSrc(imageUrl);
		} catch (e) {
			return imageUrl;
		}
	}

	// Image traitée en priorité (résultat final, plus représentatif en vignette),
	// on retombe sur le raw si elle n'existe pas encore.
	let img = $derived(displayUrl(obs.imageProcessed || obs.imageRaw || ''));
	let kind = $derived(obs.imageProcessed ? 'Traitée' : obs.imageRaw ? 'Brute' : null);
	let row = $derived<ObservationTarget | undefined>(
		obs.targets.find((t: ObservationTarget) => t.targetId === targetId) ?? obs.targets[0]
	);
	// Une seule cible : son nom usuel aide à la reconnaître (« IC 1848 · Nébuleuse de l'Âme »)
	let names = $derived.by(() => {
		if (obs.targets.length !== 1) return appState.observationTargetNames(obs);
		const target = appState.targets.find(t => t.id === obs.targets[0].targetId);
		return [target?.name, target?.usualName].filter(Boolean).join(' · ');
	});
	let details = $derived([appState.locationText(obs), obs.filter].filter(Boolean).join(' · '));
</script>

<button
	onclick={() => appState.openObservation(obs.id)}
	class="relative aspect-square rounded-lg overflow-hidden border border-[#333] bg-[#1e1e21] group text-left"
>
	{#if img}
		<img src={img} alt="Observation du {formatDate(obs.start)}" class="absolute inset-0 w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
	{:else}
		<div class="absolute inset-0 flex items-center justify-center text-3xl opacity-30">🌌</div>
	{/if}

	{#if kind}
		<span class="absolute top-2 right-2 text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-black/60 text-surface-200">
			{kind}
		</span>
	{/if}

	<!-- Dégradé pour garantir la lisibilité du texte peu importe l'image -->
	<div class="absolute inset-0 bg-linear-to-t from-black/85 via-black/10 to-transparent"></div>

	<div class="absolute bottom-0 left-0 right-0 p-3">
		<span class="text-sm font-bold text-white block">{formatDate(obs.start)}</span>
		{#if names}
			<span class="text-[11px] font-bold text-indigo-300 block truncate">{names}</span>
		{/if}
		<span class="text-[10px] text-surface-300 block truncate">{details || '—'}</span>
		{#if row && (row.imgGood || row.imgPass || row.imgBad)}
			<div class="flex gap-1 mt-1.5 h-1 rounded-full overflow-hidden w-24">
				<div class="bg-green-400" style="flex: {row.imgGood || 0}"></div>
				<div class="bg-yellow-500" style="flex: {row.imgPass || 0}"></div>
				<div class="bg-red-500" style="flex: {row.imgBad || 0}"></div>
			</div>
		{/if}
	</div>
</button>
