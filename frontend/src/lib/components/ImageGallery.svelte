<script lang="ts">
	import { appState, IMAGE_KINDS, imageTitle, imageSrc, favoriteImage, type ObservationImage, type ObservationTarget } from '$lib/state.svelte';
	import { open } from '@tauri-apps/plugin-dialog';
	import { fade } from 'svelte/transition';
	import ImageFrame from '$lib/components/ImageFrame.svelte';
	import ImagePicker from '$lib/components/ImagePicker.svelte';
	import ImageCompare from '$lib/components/ImageCompare.svelte';

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

	// Cibles de l'observation visibles sur l'image ; aucune = champ entier
	function shownTargets(image: ObservationImage) {
		return image.targetIds.filter(id => targetIds.includes(id));
	}

	// Ce que montre l'image, chaque élément marqué s'il en est la favorite
	function placesOf(image: ObservationImage) {
		const shown = shownTargets(image);
		if (!shown.length) return [{ name: 'Champ entier', favorite: image.isFavorite }];
		return shown.map(id => ({ name: appState.targetName(id), favorite: (image.favoriteTargetIds ?? []).includes(id) }));
	}

	function subtitle(image: ObservationImage) {
		const where = placesOf(image).map(p => (p.favorite ? `⭐ ${p.name}` : p.name)).join(' + ');
		return [where, IMAGE_KINDS[image.kind] ?? image.kind, image.caption].filter(Boolean).join(' · ');
	}

	// Lecture : l'image qui sert de vignette pour le filtre choisi, si elle a été choisie comme favorite
	let highlighted = $derived.by(() => {
		const image = favoriteImage({ images, targets: rows }, filterTargetId);
		return image && (image.isFavorite || (image.favoriteTargetIds ?? []).length) ? image : null;
	});

	// --- Comparaison de deux images (parmi celles du filtre) ---
	let compare = $state<{ left: number; right: number } | null>(null);
	function openCompare(left: number) {
		viewerIndex = null;
		compare = { left, right: left + 1 < visible.length ? left + 1 : 0 };
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
			// Une seule cible dans l'observation : l'image la montre sûrement
			targetIds: targetIds.length === 1 ? [...targetIds] : [],
			// La première image devient la favorite de ce qu'elle montre, si rien n'en a encore
			isFavorite: n === 0 && targetIds.length !== 1 && !images.some(i => i.isFavorite),
			favoriteTargetIds: n === 0 && targetIds.length === 1 && !images.some(i => (i.favoriteTargetIds ?? []).includes(targetIds[0])) ? [...targetIds] : []
		}));
		setImages([...images, ...added]);
		selectedIndex = images.length;
	}

	function replaceFile(image: ObservationImage, path: string) {
		image.path = path;
		image.missing = false;
	}

	function remove(index: number) {
		const rest = images.filter((_, i) => i !== index);
		setImages(rest);
		selectedIndex = Math.min(selectedIndex, Math.max(0, rest.length - 1));
	}

	// Chips de l'image : « Champ entier » (id null, exclusive) ou une cible (choix multiple).
	// Tout changement retire à l'image ses favorites : elles sont à redonner à la main.
	function toggleChip(image: ObservationImage, id: number | null) {
		const shown = shownTargets(image);
		if (id == null) {
			if (!shown.length) return;
			image.targetIds = [];
		} else {
			image.targetIds = shown.includes(id) ? shown.filter(t => t !== id) : [...shown, id];
		}
		image.isFavorite = false;
		image.favoriteTargetIds = [];
	}

	// Étoile d'une chip : l'image devient la favorite du champ (id null) ou de cette cible, à la place d'une autre
	function toggleStar(image: ObservationImage, id: number | null) {
		if (id == null) {
			const on = !image.isFavorite;
			images.forEach(i => (i.isFavorite = false));
			image.isFavorite = on;
			return;
		}
		const on = !(image.favoriteTargetIds ?? []).includes(id);
		images.forEach(i => (i.favoriteTargetIds = (i.favoriteTargetIds ?? []).filter(t => t !== id)));
		if (on) image.favoriteTargetIds = [...image.favoriteTargetIds, id];
	}

	function isStarred(image: ObservationImage, id: number | null) {
		return id == null ? image.isFavorite : (image.favoriteTargetIds ?? []).includes(id);
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
						<span class="min-w-0 flex-1">
							<span class="block text-xs font-bold text-white truncate">{imageTitle(image)}</span>
							{#if image.caption}<span class="block text-[10px] text-surface-400 truncate">{image.caption}</span>{/if}
						</span>
						<!-- Ce que montre l'image (⭐ devant ce dont elle est la favorite), puis son type -->
						<span class="shrink-0 max-w-[55%] text-right text-[10px] text-surface-400 truncate">
							{#each placesOf(image) as place, n (n)}{n ? ' + ' : ''}{#if place.favorite}<span class="font-bold text-white">⭐ {place.name}</span>{:else}{place.name}{/if}{/each}
							<span class="text-surface-500"> · {IMAGE_KINDS[image.kind] ?? image.kind}</span>
						</span>
					</button>
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
				<div>
					<span class="block text-[10px] text-surface-400 mb-1">
						Ce que montre l'image <span class="text-surface-500">· nom : choisir · ☆ : en faire la favorite</span>
					</span>
					<div class="flex flex-wrap gap-1.5">
						{#each [null, ...targetIds] as id (id ?? 'champ')}
							{@const on = id == null ? shownTargets(selected).length === 0 : shownTargets(selected).includes(id)}
							{@const name = id == null ? 'Champ entier' : appState.targetName(id)}
							<span class="chip" class:chip-on={on}>
								<button type="button" onclick={() => toggleChip(selected, id)} class="chip-name">{name}</button>
								{#if on}
									<button
										type="button"
										title={isStarred(selected, id) ? `Favorite de ${name} (cliquer pour la retirer)` : `En faire la favorite de ${name}`}
										onclick={() => toggleStar(selected, id)}
										class="chip-star"
										class:chip-star-on={isStarred(selected, id)}
									>{isStarred(selected, id) ? '★' : '☆'}</button>
								{/if}
							</span>
						{/each}
					</div>
				</div>
			</div>
		{/if}
		<datalist id="img-software-list">{#each SOFTWARE as s (s)}<option value={s}></option>{/each}</datalist>
		<datalist id="img-palette-list">{#each PALETTES as s (s)}<option value={s}></option>{/each}</datalist>
	</div>
{:else}
	<!-- ================= LECTURE ================= -->
	<div class="flex flex-col gap-3 min-h-0">
		{#if visible.length > 1}
			<div class="flex justify-end">
				<button type="button" onclick={() => openCompare(0)} class="text-[11px] font-bold text-indigo-400 hover:text-indigo-300">⇆ Comparer deux images</button>
			</div>
		{/if}
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
					subtitle={image.caption}
					showPath
					missing={image.missing}
					highlight={image === highlighted}
					onclick={() => (viewerIndex = i)}
				>
					{#snippet header()}
						<span class="text-xs text-white truncate min-w-0">
							<span class="font-bold">{#each placesOf(image) as place, n (n)}{n ? ' + ' : ''}{place.favorite ? '⭐ ' : ''}{place.name}{/each} · {IMAGE_KINDS[image.kind] ?? image.kind}</span>
							{#if image.software || image.palette}<span class="text-surface-400"> · {[image.software, image.palette].filter(Boolean).join(' · ')}</span>{/if}
						</span>
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
			<div class="flex items-center gap-4 shrink-0">
				<span class="text-xs text-surface-400">{(viewerIndex ?? 0) + 1} / {visible.length} · ← → pour naviguer · Échap pour fermer</span>
				{#if visible.length > 1}
					<button type="button" onclick={(e) => { e.stopPropagation(); openCompare(viewerIndex ?? 0); }} class="btn-secondary text-xs">⇆ Comparer…</button>
				{/if}
			</div>
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

{#if compare}
	<ImageCompare images={visible} bind:left={compare.left} bind:right={compare.right} {subtitle} onclose={() => (compare = null)} />
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
	.chip {
		display: inline-flex;
		align-items: center;
		border-radius: 999px;
		font-size: 11px;
		background: #202024;
		border: 1px solid #333;
		color: #c4c4cc;
	}
	.chip:hover {
		border-color: #6366f1;
	}
	.chip-on {
		background: #6366f1;
		border-color: #6366f1;
		color: white;
		font-weight: bold;
	}
	.chip-name {
		padding: 2px 10px;
	}
	.chip-on .chip-name {
		padding-right: 2px;
	}
	.chip-star {
		align-self: stretch;
		display: flex;
		align-items: center;
		padding: 0 8px 2px 4px;
		font-size: 12px;
		line-height: 1;
		color: rgb(255 255 255 / 0.7);
	}
	.chip-star:hover,
	.chip-star-on {
		color: #fbbf24;
	}
	.filter-on {
		background: #6366f1;
		border-color: #6366f1;
		color: white;
		font-weight: bold;
	}
</style>
