<script lang="ts">
	import { appState } from '$lib/state.svelte';

    let target = $derived(appState.activeTarget!);
</script>

<section class="bg-[#1a1a1d] p-6 rounded-lg border border-[#333] shadow-xl shrink-0">
	<div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
		
		<!-- Texte -->
		<div class="lg:col-span-9 space-y-4">
			<div class="flex justify-between items-center border-b border-[#333] pb-3">
				<div class="flex items-baseline space-x-4">
					{#if appState.isEditingTarget}
						<input type="text" class="form-input text-xl font-bold text-white w-40" bind:value={appState.targetForm.name} />
						<input type="text" class="form-input text-sm text-surface-400 w-60" bind:value={appState.targetForm.usualName} />
					{:else}
						<h1 class="text-2xl font-black text-white">{target.name}</h1>
						<span class="text-sm text-surface-400 font-semibold">{target.usualName}</span>
					{/if}
				</div>
				
				<div class="flex space-x-2">
					{#if appState.isEditingTarget}
						<button onclick={() => appState.saveTarget()} class="btn-primary">Enregistrer</button>
						<button onclick={() => appState.isEditingTarget = false} class="btn-secondary">Annuler</button>
						<button onclick={() => appState.deleteTarget()} class="btn-danger">Supprimer</button>
					{:else}
						<button onclick={() => appState.startEditTarget()} class="btn-secondary text-xs">Modifier la cible</button>
					{/if}
				</div>
			</div>

			<div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
				<div>
					<label for="target-constellation" class="text-surface-400 block mb-1">Constellation</label>
					<input id="target-constellation" type="text" class="form-input" disabled={!appState.isEditingTarget} bind:value={appState.targetForm.constellation} />
				</div>
				<div>
					<label for="target-otherDesignations" class="text-surface-400 block mb-1">Désignations</label>
					<input id="target-otherDesignations" type="text" class="form-input" disabled={!appState.isEditingTarget} bind:value={appState.targetForm.otherDesignations} />
				</div>
				<div>
					<label for="target-type" class="text-surface-400 block mb-1">Type d'objet</label>
					<input id="target-type" type="text" class="form-input" disabled={!appState.isEditingTarget} bind:value={appState.targetForm.type} />
				</div>
				<div>
					<label for="target-magnitude" class="text-surface-400 block mb-1">Magnitude</label>
					<input id="target-magnitude" type="text" class="form-input" disabled={!appState.isEditingTarget} bind:value={appState.targetForm.magnitude} />
				</div>
				<div>
					<label for="target-surfBrightness" class="text-surface-400 block mb-1">Brillance surf.</label>
					<input id="target-surfBrightness" type="text" class="form-input" disabled={!appState.isEditingTarget} bind:value={appState.targetForm.surfBrightness} />
				</div>
				<div>
					<label for="target-size" class="text-surface-400 block mb-1">Taille</label>
					<input id="target-size" type="text" class="form-input" disabled={!appState.isEditingTarget} bind:value={appState.targetForm.size} />
				</div>
				<div>
					<label for="target-ra" class="text-surface-400 block mb-1">Coordonnées AD</label>
					<input id="target-ra" type="text" class="form-input" disabled={!appState.isEditingTarget} bind:value={appState.targetForm.ra} />
				</div>
				<div>
					<label for="target-dec" class="text-surface-400 block mb-1">Coordonnées DEC</label>
					<input id="target-dec" type="text" class="form-input" disabled={!appState.isEditingTarget} bind:value={appState.targetForm.dec} />
				</div>
			</div>
		</div>

		<!-- Image étirable -->
		<div class="xl:col-span-3 relative h-44 xl:h-auto flex flex-col overflow-hidden rounded-lg">
			{#if appState.isEditingTarget}
				<div class="border border-[#333] p-2.5 rounded bg-[#1e1e21] flex flex-col flex-1 w-full">
					<span class="text-[10px] uppercase font-bold text-surface-400 mb-1.5 block">Image de référence</span>
					<div class="flex-1 border border-dashed border-[#444] rounded flex items-center justify-center overflow-hidden">
						<input type="text" class="form-input text-[10px] m-1" bind:value={appState.targetForm.imageRef} placeholder="Lien de l'image (URL)" />
					</div>
				</div>
			{:else}
				<button 
					onclick={() => appState.showMapModal = true}
					class="border border-[#333] p-2.5 rounded bg-[#1e1e21] flex flex-col flex-1 w-full text-left group hover:border-indigo-500 transition-colors cursor-pointer"
				>
					<span class="text-[10px] uppercase font-bold text-surface-400 mb-1.5 block">Image de référence</span>
					<div class="flex-1 rounded flex items-center justify-center overflow-hidden relative bg-black/30 w-full">
						{#if target.imageRef}
							<img src={target.imageRef} alt="Illustration" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
							<div class="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 flex flex-col justify-center items-center transition-opacity">
								<span class="text-xl mb-1">🌌</span>
								<span class="text-[9px] text-white font-bold tracking-wider uppercase">Explorer la carte céleste</span>
							</div>
						{:else}
							<div class="text-center p-2 flex flex-col items-center">
								<span class="text-[10px] text-[#777] font-bold">Aucune image</span>
								<span class="text-[8px] text-[#555]">Cliquez pour explorer</span>
							</div>
						{/if}
					</div>
				</button>
			{/if}
		</div>

	</div>
</section>