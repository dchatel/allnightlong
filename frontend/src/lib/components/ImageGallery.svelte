<script lang="ts">
	import { appState, IMAGE_KINDS, imageTitle, imageSrc, type ObservationImage, type ObservationTarget } from '$lib/state.svelte';
	import { open } from '@tauri-apps/plugin-dialog';
	import { fade } from 'svelte/transition';
	import ImageFrame from '$lib/components/ImageFrame.svelte';
	import ImagePicker from '$lib/components/ImagePicker.svelte';

	// Images d'une observation, dans la colonne de droite du rapport.
	// filterTargetId : cible choisie (bouton ou ligne du tableau des cibles), null = toutes.
	let {
		images,
		rows,
		isEditing = false,
		setImages,
		filterTargetId = $bindable(null)
	}: {
		images: ObservationImage[];
		rows: ObservationTarget[];
		isEditing?: boolean;
		setImages: (images: ObservationImage[]) => void;
		filterTargetId?: number | null;
	} = $props();

	const SOFTWARE = ['Siril', 'Stacking Wizard', 'AstroWizard', 'Photoshop', 'PixInsight', 'Seestar'];
	const PALETTES = ['Naturelle (RVB)', 'Hubble (SHO)', 'Dual band', 'Fausses couleurs', 'Noir et blanc'];

	let targetIds = $derived(rows.map(r => r.targetId).filter((id): id is number => id != null));
	let showFilters = $derived(targetIds.length > 1);

	// Une cible montre ses images et celles du champ entier
	let visible = $derived(
		filterTargetId == null || !targetIds.includes(filterTargetId)
			? images
			: images.filter(i => i.targetIds.length === 0 || i.targetIds.includes(filterTargetId!))
	);

	function countFor(id: number) {
		return images.filter(i => i.targetIds.length === 0 || i.targetIds.includes(id)).length;
	}

	function subtitle(image: ObservationImage) {
		const where = image.targetIds.length
			? image.targetIds.map(id => appState.targetName(id)).join(' + ')
			: 'Champ entier';
		return [where, IMAGE_KINDS[image.kind] ?? image.kind, image.caption].filter(Boolean).join(' · ');
	}

	// --- Visionneuse ---
	let viewerIndex = $state<number | null>(null);
	let viewed = $derived(viewerIndex == null ? null : visible[viewerIndex] ?? null);

	function step(delta: number) {
		if (viewerIndex == null || visible.length === 0) return;
		viewerIndex = (viewerIndex + delta + visible.length) % visible.length;
	}

	function handleKeydown(e: KeyboardEvent) {
		if (viewerIndex == null) return;
		if (e.key === 'Escape') { e.stopPropagation(); viewerIndex = null; }
		else if (e.key === 'ArrowRight') step(1);
		else if (e.key === 'ArrowLeft') step(-1);
	}

	// --- Modification ---
	let selectedIndex = $state(0);
	let selected = $derived(images[selectedIndex] ?? null);

	async function addImages() {
		const picked = await open({
			multiple: true,
			title: 'Ajouter des images à ce rapport',
			defaultPath: appState.settings.imagesFolder || undefined,
			filters: [{ name: 'Images', extensions: ['png', 'jpg', 'jpeg', 'webp', 'tif', 'tiff'] }]
		});
		const paths = Array.isArray(picked) ? picked : picked ? [picked] : [];
		if (paths.length === 0) return;
		const added: ObservationImage[] = paths.map((path, n) => ({
			path,
			kind: 'traitée',
			software: '',
			palette: '',
			caption: '',
			isFavorite: images.length === 0 && n === 0,
			// Une seule cible dans l'observation : l'image la montre sûrement
			targetIds: targetIds.length === 1 ? [...targetIds] : []
		}));
		setImages([...images, ...added]);
		selectedIndex = images.length;
	}

	function replaceFile(image: ObservationImage, path: string) {
		image.path = path;
		image.missing = false;
	}

	function remove(index: number) {
		const wasFavorite = images[index].isFavorite;
		const rest = images.filter((_, i) => i !== index);
		if (wasFavorite && rest.length) rest[0].isFavorite = true;
		setImages(rest);
		selectedIndex = Math.min(selectedIndex, Math.max(0, rest.length - 1));
	}

	function makeFavorite(index: number) {
		images.forEach((image, i) => (image.isFavorite = i === index));
	}

	function toggleTarget(image: ObservationImage, id: number, on: boolean) {
		image.targetIds = on ? [...image.targetIds, id] : image.targetIds.filter(t => t !== id);
	}
</script>

<svelte:window onkeydowncapture={handleKeydown} />

{#if isEditing}
	<!-- ================= MODIFICATION ================= -->
	<div class="flex flex-col gap-3">
		<div class="flex items-center justify-between">
			<span class="text-[10px] uppercase font-bold text-surface-400">Images ({images.length})</span>
			<button type="button" onclick={addImages} class="btn-secondary text-xs">+ Ajouter…</button>
		</div>

		{#if images.length === 0}
			<ImageFrame
				frameClass="h-40"
				onclick={addImages}
				empty={{ icon: '📁', text: 'Parcourir', hint: "Cliquer pour choisir une ou plusieurs images" }}
			/>
		{/if}

		<div class="flex flex-col gap-1 max-h-72 overflow-y-auto pr-1">
			{#each images as image, i (i)}
				<div
					class="flex items-center gap-2 p-1.5 rounded border transition-colors"
					class:border-indigo-500={i === selectedIndex}
					class:border-transparent={i !== selectedIndex}
					style={i === selectedIndex ? 'background-color: rgb(99 102 241 / 0.15)' : ''}
				>
					<button type="button" onclick={() => (selectedIndex = i)} class="flex items-center gap-2 flex-1 min-w-0 text-left">
						{#if image.missing}
							<span class="w-12 h-9 shrink-0 rounded bg-black/40 flex items-center justify-center text-[10px] text-surface-500">?</span>
						{:else}
							<img src={imageSrc(image.path)} alt="" class="w-12 h-9 shrink-0 rounded object-cover bg-black/40" />
						{/if}
						<span class="min-w-0">
							<span class="block text-xs font-bold text-white truncate">{imageTitle(image)}</span>
							<span class="block text-[10px] text-surface-400 truncate">{subtitle(image)}</span>
						</span>
					</button>
					<button
						type="button"
						title={image.isFavorite ? 'Image favorite (vignette)' : 'Choisir comme image favorite'}
						onclick={() => makeFavorite(i)}
						class="text-base px-1"
						class:opacity-30={!image.isFavorite}
					>⭐</button>
					<button type="button" title="Retirer l'image (le fichier reste sur le disque)" onclick={() => remove(i)} class="text-red-400 hover:text-red-300 px-1">✕</button>
				</div>
			{/each}
		</div>

		{#if selected}
			<div class="bg-[#1e1e21] border border-indigo-500/60 rounded-lg p-3 flex flex-col gap-3">
				<span class="text-[10px] uppercase font-bold text-surface-400">Image sélectionnée</span>
				<!-- Même cadre que la fiche cible ; la croix est inutile, la liste au-dessus a déjà ✕ -->
				<ImagePicker
					title={imageTitle(selected)}
					imageUrl={selected.path}
					missing={selected.missing}
					isEditing
					clearable={false}
					frameClass="h-40"
					onchange={(path) => replaceFile(selected, path)}
				/>
				<div class="grid grid-cols-2 gap-2">
					<div>
						<label for="img-kind" class="block text-[10px] text-surface-400 mb-1">Type</label>
						<select id="img-kind" class="form-input" bind:value={selected.kind}>
							{#each Object.entries(IMAGE_KINDS) as [value, label] (value)}
								<option {value}>{label}</option>
							{/each}
						</select>
					</div>
					<div>
						<label for="img-software" class="block text-[10px] text-surface-400 mb-1">Logiciel</label>
						<input id="img-software" type="text" list="img-software-list" class="form-input" bind:value={selected.software} />
					</div>
					<div class="col-span-2">
						<label for="img-palette" class="block text-[10px] text-surface-400 mb-1">Palette</label>
						<input id="img-palette" type="text" list="img-palette-list" class="form-input" bind:value={selected.palette} />
					</div>
					<div class="col-span-2">
						<label for="img-caption" class="block text-[10px] text-surface-400 mb-1">Légende (facultatif)</label>
						<input id="img-caption" type="text" class="form-input" bind:value={selected.caption} placeholder="Recadrée, finition Photoshop…" />
					</div>
				</div>
				{#if targetIds.length}
					<div>
						<span class="block text-[10px] text-surface-400 mb-1">Cibles visibles (aucune = champ entier)</span>
						<div class="flex flex-wrap gap-x-4 gap-y-1">
							{#each targetIds as id (id)}
								<label class="flex items-center gap-1.5 text-xs text-white">
									<input type="checkbox" checked={selected.targetIds.includes(id)} onchange={(e) => toggleTarget(selected, id, e.currentTarget.checked)} />
									{appState.targetName(id)}
								</label>
							{/each}
						</div>
					</div>
				{/if}
			</div>
		{/if}
		<datalist id="img-software-list">{#each SOFTWARE as s (s)}<option value={s}></option>{/each}</datalist>
		<datalist id="img-palette-list">{#each PALETTES as s (s)}<option value={s}></option>{/each}</datalist>
	</div>
{:else}
	<!-- ================= LECTURE ================= -->
	<div class="flex flex-col gap-3 min-h-0">
		{#if showFilters}
			<div class="flex flex-wrap gap-1.5">
				<button type="button" onclick={() => (filterTargetId = null)} class="filter-btn" class:filter-on={filterTargetId == null}>Toutes ({images.length})</button>
				{#each targetIds as id (id)}
					<button type="button" onclick={() => (filterTargetId = id)} class="filter-btn" class:filter-on={filterTargetId === id}>
						{appState.targetName(id)} ({countFor(id)})
					</button>
				{/each}
			</div>
		{/if}

		{#if visible.length === 0}
			<ImageFrame frameClass="h-40" />
		{/if}

		<div class="flex flex-col gap-4 overflow-y-auto pr-1 max-h-[calc(85vh-9rem)]">
			{#each visible as image, i (image.id ?? i)}
				<ImageFrame
					title={imageTitle(image)}
					path={image.path}
					subtitle={subtitle(image)}
					showPath
					missing={image.missing}
					highlight={image.isFavorite}
					onclick={() => (viewerIndex = i)}
				>
					{#snippet headerRight()}
						{#if image.isFavorite}<span title="Image favorite (vignette)">⭐</span>{/if}
					{/snippet}
				</ImageFrame>
			{/each}
		</div>
	</div>
{/if}

<!-- Visionneuse plein écran -->
{#if viewed}
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div transition:fade={{ duration: 120 }} onclick={() => (viewerIndex = null)} class="fixed inset-0 z-70 bg-black/90 flex flex-col p-6">
		<div class="flex items-center justify-between text-white mb-3 shrink-0">
			<div class="min-w-0">
				<span class="block text-sm font-bold">{imageTitle(viewed)}</span>
				<span class="block text-xs text-surface-400 truncate">{subtitle(viewed)}</span>
			</div>
			<span class="text-xs text-surface-400 shrink-0">{(viewerIndex ?? 0) + 1} / {visible.length} · ← → pour naviguer · Échap pour fermer</span>
		</div>
		<div class="flex-1 min-h-0 flex items-center gap-4">
			<button type="button" onclick={(e) => { e.stopPropagation(); step(-1); }} class="text-4xl text-white/60 hover:text-white px-2">‹</button>
			<div class="flex-1 h-full min-w-0 flex items-center justify-center">
				{#if viewed.missing}
					<span class="text-surface-400 text-sm">Image introuvable : {viewed.path}</span>
				{:else}
					<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
					<img src={imageSrc(viewed.path)} alt={imageTitle(viewed)} onclick={(e) => e.stopPropagation()} class="max-h-full max-w-full object-contain" />
				{/if}
			</div>
			<button type="button" onclick={(e) => { e.stopPropagation(); step(1); }} class="text-4xl text-white/60 hover:text-white px-2">›</button>
		</div>
	</div>
{/if}

<style>
	.filter-btn {
		padding: 2px 10px;
		border-radius: 999px;
		font-size: 11px;
		background: #202024;
		border: 1px solid #333;
		color: #c4c4cc;
	}
	.filter-btn:hover {
		border-color: #6366f1;
	}
	.filter-on {
		background: #6366f1;
		border-color: #6366f1;
		color: white;
		font-weight: bold;
	}
</style>
