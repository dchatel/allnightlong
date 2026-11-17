<script lang="ts">
	import ImagePicker from '$lib/components/ImagePicker.svelte';

	// Corps de la fiche cible (caractéristiques, notes, image de référence), sans en-tête.
	// Utilisé par la fiche de l'onglet Cibles et par la fiche ouverte depuis un rapport.
	let {
		values,
		isEditing = false,
		onfield,
		onViewClick = undefined,
		idPrefix = 'target'
	}: {
		values: any;
		isEditing?: boolean;
		onfield: (key: string, value: string) => void;
		onViewClick?: () => void;
		idPrefix?: string;
	} = $props();

	const FIELDS = [
		{ key: 'constellation', label: 'Constellation' },
		{ key: 'otherDesignations', label: 'Désignations' },
		{ key: 'type', label: "Type d'objet" },
		{ key: 'magnitude', label: 'Magnitude' },
		{ key: 'surfBrightness', label: 'Brillance surf.' },
		{ key: 'size', label: 'Taille' },
		{ key: 'ra', label: 'Coordonnées AD' },
		{ key: 'dec', label: 'Coordonnées DEC' }
	];
</script>

<div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
	<!-- Colonne de gauche : Détails et Notes -->
	<div class="lg:col-span-9 space-y-5">
		<div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
			{#each FIELDS as field (field.key)}
				<div>
					<label for="{idPrefix}-{field.key}" class="text-surface-400 block mb-1">{field.label}</label>
					{#if isEditing}
						<input
							id="{idPrefix}-{field.key}"
							type="text"
							class="form-input"
							value={values[field.key] ?? ''}
							oninput={(e) => onfield(field.key, e.currentTarget.value)}
						/>
					{:else}
						<span id="{idPrefix}-{field.key}">{values[field.key] ?? ''}</span>
					{/if}
				</div>
			{/each}
		</div>

		<div>
			<label for="{idPrefix}-notes" class="text-surface-400 block mb-1 text-xs">Notes / Description libre</label>
			{#if isEditing}
				<textarea
					id="{idPrefix}-notes"
					class="w-full form-input rounded p-2 text-white text-sm focus:outline-none focus:border-primary-500 resize-y min-h-24"
					value={values.notes ?? ''}
					oninput={(e) => onfield('notes', e.currentTarget.value)}
					placeholder="Ajoutez vos notes personnelles sur cette cible..."
				></textarea>
			{:else}
				<!-- En mode lecture, 'whitespace-pre-wrap' permet de respecter les sauts de ligne -->
				<div id="{idPrefix}-notes" class="text-sm whitespace-pre-wrap p-3 min-h-12">
					{#if values.notes}
						{values.notes}
					{:else}
						<em class="text-surface-500">Aucune note.</em>
					{/if}
				</div>
			{/if}
		</div>
	</div>

	<!-- Image étirable -->
	<div class="lg:col-span-3 h-60">
		<ImagePicker
			fill
			title="Image de référence"
			imageUrl={values.imageRef}
			onchange={(v: string) => onfield('imageRef', v)}
			{isEditing}
			viewOverlayText={onViewClick ? 'Explorer la carte céleste' : ''}
			viewOverlayIcon="🌌"
			{onViewClick}
		/>
	</div>
</div>
