<script lang="ts">
	import { imageSrc, imageTitle, type ObservationImage } from '$lib/state.svelte';
	import { fade } from 'svelte/transition';

	// Deux images d'une observation côte à côte (Siril contre Wizard, RVB contre Hubble…).
	// Le zoom (molette) et le déplacement (glisser) sont communs aux deux : on regarde le même détail.
	let {
		images,
		left = $bindable(0),
		right = $bindable(1),
		subtitle,
		onclose
	}: {
		images: ObservationImage[];
		left?: number;
		right?: number;
		subtitle: (image: ObservationImage) => string;
		onclose: () => void;
	} = $props();

	const MIN_ZOOM = 1;
	const MAX_ZOOM = 12;
	let zoom = $state(1);
	// Décalage du centre de l'image, en fraction de la taille du panneau
	let panX = $state(0);
	let panY = $state(0);
	let dragging: { x: number; y: number; panX: number; panY: number; w: number; h: number } | null = null;

	function reset() {
		zoom = 1;
		panX = 0;
		panY = 0;
	}

	// Zoom vers le point sous la souris : ce point reste immobile à l'écran
	function onWheel(e: WheelEvent) {
		e.preventDefault();
		const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
		const fx = (e.clientX - rect.left) / rect.width - 0.5;
		const fy = (e.clientY - rect.top) / rect.height - 0.5;
		const next = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, zoom * (e.deltaY < 0 ? 1.2 : 1 / 1.2)));
		panX = fx - ((fx - panX) * next) / zoom;
		panY = fy - ((fy - panY) * next) / zoom;
		zoom = next;
		if (zoom === MIN_ZOOM) reset();
	}

	function onDown(e: PointerEvent) {
		const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
		dragging = { x: e.clientX, y: e.clientY, panX, panY, w: rect.width, h: rect.height };
		(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
	}

	function onMove(e: PointerEvent) {
		if (!dragging || zoom === 1) return;
		panX = dragging.panX + (e.clientX - dragging.x) / dragging.w;
		panY = dragging.panY + (e.clientY - dragging.y) / dragging.h;
	}

	function onUp() {
		dragging = null;
	}

	function zoomBy(factor: number) {
		zoom = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, zoom * factor));
		if (zoom === MIN_ZOOM) reset();
	}

	// Phase de capture : Échap ferme la comparaison sans fermer le rapport
	function handleKeydown(e: KeyboardEvent) {
		if (e.key !== 'Escape') return;
		e.stopPropagation();
		onclose();
	}

	let transform = $derived(`translate(${panX * 100}%, ${panY * 100}%) scale(${zoom})`);
</script>

<svelte:window onkeydowncapture={handleKeydown} />

<div transition:fade={{ duration: 120 }} class="fixed inset-0 z-70 bg-black/95 flex flex-col p-5 gap-3">
	<div class="flex items-center justify-between gap-4 text-white shrink-0">
		<span class="text-sm font-bold uppercase tracking-widest">Comparer deux images</span>
		<div class="flex items-center gap-2 text-xs">
			<span class="text-surface-400 mr-2">Molette : zoom · glisser : déplacer · double-clic : vue entière</span>
			<button type="button" onclick={() => zoomBy(1 / 1.5)} class="btn-secondary px-2" title="Dézoomer">−</button>
			<span class="w-12 text-center tabular-nums">{Math.round(zoom * 100)} %</span>
			<button type="button" onclick={() => zoomBy(1.5)} class="btn-secondary px-2" title="Zoomer">+</button>
			<button type="button" onclick={reset} class="btn-secondary">Vue entière</button>
			<button type="button" onclick={onclose} class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-surface-800 text-surface-400 hover:text-white text-lg ml-2" title="Fermer (Échap)">✕</button>
		</div>
	</div>

	<div class="flex-1 min-h-0 grid grid-cols-2 gap-3">
		{#each [{ side: 'left' }, { side: 'right' }] as pane (pane.side)}
			{@const index = pane.side === 'left' ? left : right}
			{@const image = images[index]}
			<div class="flex flex-col min-h-0 gap-2">
				<select
					class="form-input shrink-0"
					value={index}
					onchange={(e) => {
						const value = Number(e.currentTarget.value);
						if (pane.side === 'left') left = value;
						else right = value;
					}}
				>
					{#each images as candidate, n (n)}
						<option value={n}>{imageTitle(candidate)} — {subtitle(candidate)}</option>
					{/each}
				</select>
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<div
					class="flex-1 min-h-0 relative overflow-hidden rounded border border-[#333] bg-black select-none"
					class:cursor-grab={zoom > 1}
					onwheel={onWheel}
					onpointerdown={onDown}
					onpointermove={onMove}
					onpointerup={onUp}
					onpointercancel={onUp}
					ondblclick={reset}
				>
					{#if image?.missing}
						<div class="absolute inset-0 flex flex-col items-center justify-center text-center p-4">
							<span class="text-sm font-bold text-surface-400">Image introuvable</span>
							<span class="text-[10px] text-surface-500 break-all mt-1">{image.path}</span>
						</div>
					{:else if image}
						<img
							src={imageSrc(image.path)}
							alt={imageTitle(image)}
							draggable="false"
							class="absolute inset-0 w-full h-full object-contain"
							style="transform: {transform}; transform-origin: 50% 50%;"
						/>
					{/if}
				</div>
			</div>
		{/each}
	</div>
</div>
