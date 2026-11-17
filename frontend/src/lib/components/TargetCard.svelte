<script lang="ts">
	import { appState } from '$lib/state.svelte';
	import TargetFields from '$lib/components/TargetFields.svelte';
	import Input from './Input.svelte';

    let target = $derived(appState.activeTarget!);

    // Petit helper local : en édition on lit/écrit dans targetForm,
    // sinon on ne fait qu'afficher la valeur de target.
    // Input.svelte n'a pas besoin de connaître cette logique : il reçoit
    // juste value + onchange, comme n'importe quel composant contrôlé.
    function fieldValue(key: string) {
        return appState.isEditingTarget ? appState.targetForm[key] : target[key];
    }
    function setField(key: string) {
        return (v: string) => { appState.targetForm[key] = v; };
    }
</script>

<section class="bg-[#1a1a1d] p-6 rounded-lg border border-[#333] shadow-xl shrink-0 flex flex-col gap-5">

	<!-- ================= EN-TÊTE (Pleine largeur) ================= -->
	<div class="flex justify-between items-center border-b border-[#333] pb-4">
		<div class="flex items-baseline space-x-4">
			<Input
				isEditing={appState.isEditingTarget}
				class={appState.isEditingTarget ? "form-input text-xl font-bold text-white w-40" : "text-2xl font-black text-white"}
				value={fieldValue('name')}
				onchange={setField('name')}
			/>
			<Input
				isEditing={appState.isEditingTarget}
				class={appState.isEditingTarget ? "form-input text-sm text-surface-400 w-60" : "text-sm text-surface-400 font-semibold"}
				value={fieldValue('usualName')}
				onchange={setField('usualName')}
			/>
		</div>
		
		<div class="flex space-x-2">
			{#if appState.isEditingTarget}
				<button onclick={() => appState.saveTarget()} class="btn-primary">Enregistrer</button>
				<button onclick={() => appState.cancelEditTarget()} class="btn-secondary">Annuler</button>
				<button onclick={() => appState.deleteTarget()} class="btn-danger">Supprimer</button>
			{:else}
				<button onclick={() => appState.startEditTarget()} class="btn-secondary text-xs">Modifier la cible</button>
			{/if}
		</div>
	</div>

	<!-- ================= CORPS (2 Colonnes) ================= -->
	<TargetFields
		values={appState.isEditingTarget ? appState.targetForm : target}
		isEditing={appState.isEditingTarget}
		onfield={(key, value) => setField(key)(value)}
		onViewClick={() => appState.showMapModal = true}
	/>
</section>