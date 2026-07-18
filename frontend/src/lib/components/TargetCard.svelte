<script lang="ts">
	import { appState } from '$lib/state.svelte';
	import ImagePicker from '$lib/components/ImagePicker.svelte';
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

<section class="bg-[#1a1a1d] p-6 rounded-lg border border-[#333] shadow-xl shrink-0">
	<div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
		
		<!-- Texte -->
		<div class="lg:col-span-9 space-y-4">
			<div class="flex justify-between items-center border-b border-[#333] pb-3">
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

			<div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
				<div>
					<label for="target-constellation" class="text-surface-400 block mb-1">Constellation</label>
					<Input id="target-constellation" isEditing={appState.isEditingTarget} class="form-input" value={fieldValue('constellation')} onchange={setField('constellation')} />
				</div>
				<div>
					<label for="target-otherDesignations" class="text-surface-400 block mb-1">Désignations</label>
					<Input id="target-otherDesignations" isEditing={appState.isEditingTarget} class="form-input" value={fieldValue('otherDesignations')} onchange={setField('otherDesignations')} />
				</div>
				<div>
					<label for="target-type" class="text-surface-400 block mb-1">Type d'objet</label>
					<Input id="target-type" isEditing={appState.isEditingTarget} class="form-input" value={fieldValue('type')} onchange={setField('type')} />
				</div>
				<div>
					<label for="target-magnitude" class="text-surface-400 block mb-1">Magnitude</label>
					<Input id="target-magnitude" isEditing={appState.isEditingTarget} class="form-input" value={fieldValue('magnitude')} onchange={setField('magnitude')} />
				</div>
				<div>
					<label for="target-surfBrightness" class="text-surface-400 block mb-1">Brillance surf.</label>
					<Input id="target-surfBrightness" isEditing={appState.isEditingTarget} class="form-input" value={fieldValue('surfBrightness')} onchange={setField('surfBrightness')} />
				</div>
				<div>
					<label for="target-size" class="text-surface-400 block mb-1">Taille</label>
					<Input id="target-size" isEditing={appState.isEditingTarget} class="form-input" value={fieldValue('size')} onchange={setField('size')} />
				</div>
				<div>
					<label for="target-ra" class="text-surface-400 block mb-1">Coordonnées AD</label>
					<Input id="target-ra" isEditing={appState.isEditingTarget} class="form-input" value={fieldValue('ra')} onchange={setField('ra')} />
				</div>
				<div>
					<label for="target-dec" class="text-surface-400 block mb-1">Coordonnées DEC</label>
					<Input id="target-dec" isEditing={appState.isEditingTarget} class="form-input" value={fieldValue('dec')} onchange={setField('dec')} />
				</div>
			</div>
		</div>

		<!-- Image étirable -->
		<div class="lg:col-span-3 relative h-52 flex flex-col overflow-hidden rounded-lg">
			<ImagePicker
				title="Image de référence"
				imageUrl={fieldValue('imageRef')}
				onchange={setField('imageRef')}
				isEditing={appState.isEditingTarget}
				viewOverlayText="Explorer la carte céleste"
				viewOverlayIcon="🌌"
				onViewClick={() => appState.showMapModal = true}
			/>
		</div>

	</div>
</section>