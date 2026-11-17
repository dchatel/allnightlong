<script lang="ts">
	import { appState } from '$lib/state.svelte';

	let onTargets = $derived(appState.leftTab === 'targets');
	let totalObservations = $derived(appState.observations.length);

	function toggleSort() {
		if (onTargets) appState.targetSortDescending = !appState.targetSortDescending;
		else appState.observationSortOldestFirst = !appState.observationSortOldestFirst;
	}

	function create() {
		if (onTargets) appState.createNewTarget();
		else appState.createNewObservation(null);
	}
</script>

<aside class="w-80 border-r border-[#2a2a2d] flex flex-col bg-[#161619] h-full shrink-0">
	<!-- Onglets -->
	<div class="grid grid-cols-2 border-b border-[#2a2a2d] text-xs font-bold uppercase tracking-widest">
		{#each [{ key: 'targets', label: 'Cibles' }, { key: 'observations', label: 'Observations' }] as tab (tab.key)}
			<button
				onclick={() => (appState.leftTab = tab.key as 'targets' | 'observations')}
				disabled={appState.isEditingTarget}
				class="py-3 transition-colors border-b-2 disabled:opacity-30 disabled:cursor-not-allowed"
				class:tab-active={appState.leftTab === tab.key}
				class:tab-idle={appState.leftTab !== tab.key}
			>
				{tab.label}
			</button>
		{/each}
	</div>

	<!-- Recherche, tri, création -->
	<div class="p-4 border-b border-[#2a2a2d] flex space-x-2">
		{#if onTargets}
			<input
				type="text"
				placeholder="Rechercher un objet..."
				class="bg-[#202024] border border-[#333] rounded px-3 py-1.5 text-sm flex-1 min-w-0 text-white focus:outline-none disabled:opacity-30 disabled:cursor-not-allowed"
				disabled={appState.isEditingTarget}
				bind:value={appState.searchQuery}
			/>
		{:else}
			<input
				type="text"
				placeholder="Filtrer…"
				title="Cible, lieu, filtre, notes ou date"
				class="bg-[#202024] border border-[#333] rounded px-3 py-1.5 text-sm flex-1 min-w-0 text-white focus:outline-none"
				bind:value={appState.observationSearch}
			/>
		{/if}
		<button
			onclick={toggleSort}
			title={onTargets ? 'Inverser l\'ordre alphabétique' : 'Inverser l\'ordre chronologique'}
			class="bg-[#2a2a2d] hover:bg-[#333] border border-[#444] text-surface-200 px-2 py-1.5 rounded text-xs font-bold transition-colors whitespace-nowrap disabled:opacity-30 disabled:cursor-not-allowed"
			disabled={appState.isEditingTarget}
		>
			{#if onTargets}
				{appState.targetSortDescending ? 'Z→A' : 'A→Z'}
			{:else}
				{appState.observationSortOldestFirst ? 'Anciennes ↑' : 'Récentes ↓'}
			{/if}
		</button>
		<button
			onclick={create}
			title={onTargets ? 'Nouvelle cible' : 'Nouveau rapport'}
			class="bg-[#2a2a2d] hover:bg-[#333] border border-[#444] text-white px-3.5 py-1.5 rounded text-sm font-bold transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
			disabled={appState.isEditingTarget}
		>
			+
		</button>
	</div>

	<div class="flex-1 overflow-y-auto" class:opacity-30={appState.isEditingTarget}>
		{#if onTargets}
			{#if appState.filteredTargets.length === 0}
				<div class="p-8 text-center text-sm text-surface-400 opacity-50">Aucun objet</div>
			{:else}
				<div class="divide-y divide-[#2a2a2d]/50">
					{#each appState.filteredTargets as target (target.id)}
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
		{:else}
			<div class="divide-y divide-[#2a2a2d]/50">
				<button
					onclick={() => (appState.observationMonth = null)}
					class="w-full text-left p-4 hover:bg-[#202024] transition-colors flex flex-col relative"
					class:active-item={appState.observationMonth === null}
				>
					<div class="flex justify-between items-baseline mb-1">
						<span class="font-bold text-white text-base">Toutes les observations</span>
						<span class="text-xs text-surface-400">{totalObservations}</span>
					</div>
					<div class="text-xs text-surface-400">Triées par date</div>
				</button>
				{#each appState.observationMonths as month (month.key)}
					<button
						onclick={() => (appState.observationMonth = month.key)}
						class="w-full text-left p-4 hover:bg-[#202024] transition-colors flex flex-col relative"
						class:active-item={appState.observationMonth === month.key}
					>
						<div class="flex justify-between items-baseline mb-1">
							<span class="font-bold text-white text-base">{month.label}</span>
							<span class="text-xs text-surface-400">{month.count}</span>
						</div>
						<div class="text-xs text-surface-400 truncate">{month.preview}</div>
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
	.tab-active {
		color: white;
		border-bottom-color: #6366f1;
	}
	.tab-idle {
		color: #8b8b94;
		border-bottom-color: transparent;
	}
	.tab-idle:hover {
		color: white;
	}
</style>
