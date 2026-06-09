<script lang="ts">
	import { appState } from '$lib/state.svelte';
	import { fade, slide } from 'svelte/transition'; // [3]
</script>

<div in:fade={{ duration: 150 }} out:slide={{ duration: 150 }} class="flex flex-col h-auto xl:h-full space-y-6">
	<div class="flex justify-between items-center shrink-0">
		<h2 class="text-sm font-bold uppercase tracking-widest text-surface-400">Historique des Observations ({appState.activeTargetObservations.length})</h2>
		<button onclick={() => appState.createNewObservation()} class="btn-primary text-xs">+ Nouvelle observation</button>
	</div>

	{#if appState.activeTargetObservations.length === 0}
		<div class="text-center py-16 text-surface-400/50">
			<p class="text-3xl mb-2">🔭</p>
			<p class="text-sm">Aucun rapport pour cet objet céleste.</p>
		</div>
	{:else}
		<div class="overflow-x-auto xl:flex-1 xl:min-h-0 xl:overflow-y-auto pr-1">
			<table class="w-full text-left border-collapse text-sm">
				<thead>
					<tr class="border-b border-[#333] text-surface-400 text-xs uppercase tracking-wider">
						<th class="py-3 px-4">Date</th>
						<th class="py-3 px-4">Localisation</th>
						<th class="py-3 px-4">Durée de pose</th>
						<th class="py-3 px-4">Notes</th>
						<th class="py-3 px-4 text-right">Action</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-[#2a2a2d]">
					{#each appState.activeTargetObservations as obs}
						<tr class="hover:bg-[#202024]/50 transition-colors cursor-pointer" onclick={() => appState.openObservation(obs.id)}>
							<td class="py-3.5 px-4 font-bold text-white">📅 {obs.date}</td>
							<td class="py-3.5 px-4 text-surface-400">{obs.location}</td>
							<td class="py-3.5 px-4 text-surface-400">
								{((obs.imgGood * Number(obs.subExposure)) / 60).toFixed(1)} minutes
							</td>
							<td class="py-3.5 px-4 text-surface-400 truncate max-w-xs">{obs.otherObjects || 'Aucune note'}</td>
							<td class="py-3.5 px-4 text-right">
								<span class="text-xs text-indigo-400 font-bold hover:underline">Ouvrir la fiche →</span>
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
</div>