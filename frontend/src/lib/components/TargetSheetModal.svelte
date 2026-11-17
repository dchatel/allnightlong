<script lang="ts">
	import { appState } from '$lib/state.svelte';
	import { fade } from 'svelte/transition';
	import TargetFields from '$lib/components/TargetFields.svelte';

	let sheet = $derived(appState.targetSheet);
	let creating = $derived(sheet?.mode === 'create');
	let values = $derived(creating ? sheet?.form : appState.targets.find(t => t.id === sheet?.targetId));

	// Phase de capture : Échap ferme cette fiche sans atteindre le rapport ouvert en dessous
	function handleKeydown(e: KeyboardEvent) {
		if (e.key !== 'Escape' || !appState.targetSheet) return;
		e.stopPropagation();
		appState.closeTargetSheet();
	}
</script>

<svelte:window onkeydowncapture={handleKeydown} />

{#if sheet && values}
	<!-- Clic à côté : ferme la fiche consultée, comme le rapport (Échap au clavier).
		 Une fiche en création ne se ferme qu'avec Annuler, pour ne pas perdre la saisie. -->
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		transition:fade={{ duration: 150 }}
		onclick={() => { if (!creating) appState.closeTargetSheet(); }}
		class="fixed inset-0 bg-black/70 backdrop-blur-sm z-60 flex items-center justify-center p-8"
	>
		<div onclick={(e) => e.stopPropagation()} class="bg-[#1a1a1d] border border-[#333] rounded-2xl w-[80vw] max-h-[85vh] flex flex-col overflow-hidden shadow-2xl">
			<div class="border-b border-[#333] px-6 py-4 flex items-center justify-between gap-4 shrink-0">
				{#if creating}
					<div class="flex items-baseline gap-3 flex-1 min-w-0">
						<span class="text-xl">✨</span>
						<input
							type="text"
							class="form-input text-xl font-bold text-white w-48"
							placeholder="Nom (ex. NGC 891)"
							bind:value={sheet.form.name}
						/>
						<input
							type="text"
							class="form-input text-sm text-surface-400 w-72"
							placeholder="Nom usuel (facultatif)"
							bind:value={sheet.form.usualName}
						/>
					</div>
					<div class="flex gap-2 shrink-0">
						<button onclick={() => appState.createTargetFromSheet()} class="btn-primary text-xs">Créer la cible</button>
						<button onclick={() => appState.closeTargetSheet()} class="btn-secondary text-xs">Annuler</button>
					</div>
				{:else}
					<div class="flex items-baseline gap-4 min-w-0">
						<span class="text-2xl font-black text-white">{values.name}</span>
						<span class="text-sm text-surface-400 font-semibold truncate">{values.usualName}</span>
					</div>
					<div class="flex items-center gap-2 shrink-0">
						{#if appState.isEditingObservation}
							<span class="text-[10px] text-surface-500">Enregistrez le rapport pour ouvrir la fiche dans l'onglet Cibles</span>
						{:else}
							<button onclick={() => appState.showTargetInTargetsTab(values.id)} class="btn-secondary text-xs">Voir dans l'onglet Cibles</button>
						{/if}
						<button
							onclick={() => appState.closeTargetSheet()}
							class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-surface-800 text-surface-400 hover:text-white transition-colors text-lg"
						>✕</button>
					</div>
				{/if}
			</div>
			<div class="p-6 overflow-y-auto">
				<TargetFields
					{values}
					isEditing={creating}
					idPrefix="sheet"
					onfield={(key, value) => { if (sheet.form) sheet.form[key] = value; }}
				/>
			</div>
		</div>
	</div>
{/if}
