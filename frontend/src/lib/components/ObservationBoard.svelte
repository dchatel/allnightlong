<script lang="ts">
	import { appState, monthLabel } from '$lib/state.svelte';
	import ObservationCard from '$lib/components/ObservationCard.svelte';

	let title = $derived(appState.observationMonth ? monthLabel(appState.observationMonth) : 'Toutes les observations');
	let list = $derived(appState.visibleObservations);
</script>

<div class="bg-[#161619] border border-[#2a2a2d] rounded-xl p-6 shadow-2xl flex flex-col h-full min-h-0">
	<div class="flex items-center justify-between mb-4 shrink-0">
		<h2 class="text-sm font-bold uppercase tracking-widest text-surface-100">
			{title}
			<span class="text-surface-400 font-normal normal-case tracking-normal ml-2">{list.length} observation{list.length > 1 ? 's' : ''}</span>
		</h2>
		<button onclick={() => appState.createNewObservation(null)} class="btn-primary text-xs">+ Nouveau rapport</button>
	</div>

	<div class="flex-1 min-h-0 overflow-y-auto">
		{#if list.length === 0}
			<div class="h-40 flex flex-col items-center justify-center text-surface-400 text-xs opacity-60">
				<span class="text-2xl mb-2">🔭</span>
				Aucune observation
			</div>
		{:else}
			<div class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-4">
				{#each list as obs (obs.id)}
					<ObservationCard {obs} />
				{/each}
			</div>
		{/if}
	</div>
</div>
