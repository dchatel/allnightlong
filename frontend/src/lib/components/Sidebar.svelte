<script lang="ts">
	import { appState } from '$lib/state.svelte';
</script>

<aside class="w-80 border-r border-[#2a2a2d] flex flex-col bg-[#161619] h-full shrink-0">
	<div class="p-4 border-b border-[#2a2a2d] flex space-x-2">
		<input 
			type="text" 
			placeholder="Rechercher un objet..." 
			class="bg-[#202024] border border-[#333] rounded px-3 py-1.5 text-sm flex-1 text-white focus:outline-none disabled:opacity-30 disabled:cursor-not-allowed"
			disabled={appState.isEditingTarget}
			bind:value={appState.searchQuery}
		/>
		<button 
			onclick={() => appState.createNewTarget()}
			class="bg-[#2a2a2d] hover:bg-[#333] border border-[#444] text-white px-3.5 py-1.5 rounded text-sm font-bold transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
			disabled={appState.isEditingTarget}
		>
			+
		</button>
	</div>

	<div class="flex-1 overflow-y-auto" class:opacity-30={appState.isEditingTarget}>
		{#if appState.filteredTargets.length === 0}
			<div class="p-8 text-center text-sm text-surface-400 opacity-50">Aucun objet</div>
		{:else}
			<div class="divide-y divide-[#2a2a2d]/50">
				{#each appState.filteredTargets as target}
					<button 
						onclick={() => appState.selectTarget(target.id)}
						class="w-full text-left p-4 hover:bg-[#202024] transition-colors flex flex-col relative disabled:cursor-not-allowed"
						disabled={appState.isEditingTarget}
						class:active-item={appState.selectedTargetId === target.id}
					>
						<div class="flex justify-between items-baseline mb-1">
							<span class="font-bold text-white text-base">{target.name}</span>
							<span class="text-xs text-surface-400 uppercase tracking-widest">{target.constellation}</span>
						</div>
						<div class="text-xs text-surface-400 truncate">{target.usualName || 'Pas de nom usuel'}</div>
					</button>
				{/each}
			</div>
		{/if}
	</div>
</aside>

<style>
	.active-item {
		background-color: #202024;
		border-left: 3px solid #6366f1;
	}
</style>