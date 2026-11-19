<script lang="ts">
	import { appState, formatDate, favoriteImage, imageSrc, IMAGE_KINDS } from '$lib/state.svelte';

	// targetId : carte vue depuis cette cible (sa fiche) ; sa favorite sert de vignette
	let { obs, targetId = null }: { obs: any; targetId?: number | null } = $props();

	let image = $derived(favoriteImage(obs, targetId));
	let img = $derived(image && !image.missing ? imageSrc(image.path) : '');
	let kind = $derived(image ? (IMAGE_KINDS[image.kind] ?? image.kind) : null);
	let imageCount = $derived(obs.images?.length ?? 0);
	// Une seule cible : son nom usuel aide à la reconnaître (« IC 1848 · Nébuleuse de l'Âme »)
	let names = $derived.by(() => {
		if (obs.targets.length !== 1) return appState.observationTargetNames(obs);
		const target = appState.targets.find(t => t.id === obs.targets[0].targetId);
		return [target?.name, target?.usualName].filter(Boolean).join(' · ');
	});
	let details = $derived([appState.locationText(obs), obs.filter].filter(Boolean).join(' · '));
</script>

<button
	onclick={() => appState.openObservation(obs.id, targetId)}
	class="relative aspect-square rounded-lg overflow-hidden border border-[#333] bg-[#1e1e21] group text-left"
>
	{#if img}
		<img src={img} alt="Observation du {formatDate(obs.start)}" class="absolute inset-0 w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
	{:else}
		<div class="absolute inset-0 flex items-center justify-center text-3xl opacity-30">🌌</div>
	{/if}

	{#if kind}
		<span class="absolute top-2 right-2 text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-black/60 text-surface-200">
			{kind}{imageCount > 1 ? ` · ${imageCount}` : ''}
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
		{#if obs.imgGood || obs.imgPass || obs.imgBad}
			<div class="flex gap-1 mt-1.5 h-1 rounded-full overflow-hidden w-24">
				<div class="bg-green-400" style="flex: {obs.imgGood || 0}"></div>
				<div class="bg-yellow-500" style="flex: {obs.imgPass || 0}"></div>
				<div class="bg-red-500" style="flex: {obs.imgBad || 0}"></div>
			</div>
		{/if}
	</div>
</button>
