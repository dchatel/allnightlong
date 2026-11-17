<script lang="ts">
	import { appState } from '$lib/state.svelte';
	import ObservationCard from '$lib/components/ObservationCard.svelte';
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
				<ObservationCard {obs} targetId={appState.selectedTargetId} />
			{/each}
		</div>
	{/if}
</div>
