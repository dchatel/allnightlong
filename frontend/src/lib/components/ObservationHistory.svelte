<script lang="ts">
	import { appState } from '$lib/state.svelte';
	import { convertFileSrc } from '@tauri-apps/api/core';

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
	function thumbnail(obs: any) {
		return obs.imageProcessed || obs.imageRaw || '';
	}

	function thumbnailKind(obs: any) {
		if (obs.imageProcessed) return 'Traitée';
		if (obs.imageRaw) return 'Brute';
		return null;
	}
</script>

<div class="h-full overflow-y-auto">
	<div class="flex items-center justify-between mb-4 shrink-0">
		<h2 class="text-sm font-bold uppercase tracking-widest text-surface-100">Historique des observations</h2>
		<button onclick={() => appState.createNewObservation()} class="btn-primary text-xs">+ Nouveau rapport</button>
	</div>

	{#if appState.activeTargetObservations.length === 0}
		<div class="h-40 flex flex-col items-center justify-center text-surface-400 text-xs opacity-60">
			<span class="text-2xl mb-2">🔭</span>
			Aucune observation enregistrée pour cette cible
		</div>
	{:else}
		<div class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
			{#each appState.activeTargetObservations as obs (obs.id)}
				{@const img = displayUrl(thumbnail(obs))}
				<button
					onclick={() => appState.openObservation(obs.id)}
					class="relative aspect-square rounded-lg overflow-hidden border border-[#333] bg-[#1e1e21] group text-left"
				>
					{#if img}
						<img src={img} alt="Observation du {obs.date}" class="absolute inset-0 w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
					{:else}
						<div class="absolute inset-0 flex items-center justify-center text-3xl opacity-30">🌌</div>
					{/if}

					{#if thumbnailKind(obs)}
						<span class="absolute top-2 right-2 text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-black/60 text-surface-200">
							{thumbnailKind(obs)}
						</span>
					{/if}

					<!-- Dégradé pour garantir la lisibilité du texte peu importe l'image -->
					<div class="absolute inset-0 bg-linear-to-t from-black/85 via-black/10 to-transparent"></div>

					<div class="absolute bottom-0 left-0 right-0 p-3">
						<span class="text-sm font-bold text-white block">{obs.date}</span>
						<span class="text-[10px] text-surface-300 block">{obs.location || '—'}</span>
						{#if obs.imgGood || obs.imgPass || obs.imgBad}
							<div class="flex gap-1 mt-1.5 h-1 rounded-full overflow-hidden w-24">
								<div class="bg-green-400" style="flex: {obs.imgGood || 0}"></div>
								<div class="bg-yellow-500" style="flex: {obs.imgPass || 0}"></div>
								<div class="bg-red-500" style="flex: {obs.imgBad || 0}"></div>
							</div>
						{/if}
					</div>
				</button>
			{/each}
		</div>
	{/if}
</div>