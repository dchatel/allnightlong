<script lang="ts">
	import { open } from '@tauri-apps/plugin-dialog';
	import ImageFrame from '$lib/components/ImageFrame.svelte';

	// Image choisie par l'utilisateur, dans le cadre commun (ImageFrame).
	// En modification, un clic ouvre l'explorateur pour choisir ou changer le fichier.
	let {
		title,
		imageUrl,               // valeur affichée, fournie par le parent (lecture seule ici)
		onchange = undefined,   // remonte le nouveau chemin choisi par l'utilisateur
		isEditing = false,
		clearable = true,       // croix « retirer l'image » dans l'angle
		missing = false,
		fill = false,
		frameClass = 'h-52',
		subtitle = '',
		showPath = true,
		viewOverlayText = '',
		viewOverlayIcon = '🌌',
		onViewClick = undefined
	}: {
		title: string;
		imageUrl: string;
		onchange?: (path: string) => void;
		isEditing?: boolean;
		clearable?: boolean;
		missing?: boolean;
		fill?: boolean;
		frameClass?: string;
		subtitle?: string;
		showPath?: boolean;
		viewOverlayText?: string;
		viewOverlayIcon?: string;
		onViewClick?: () => void;
	} = $props();

	async function pickFile() {
		const selectedPath = await open({
			multiple: false,
			title: `Choisir une image pour : ${title}`,
			filters: [{ name: 'Images', extensions: ['png', 'jpg', 'jpeg', 'webp', 'tif', 'tiff', 'fits'] }]
		});
		// On remonte le nouveau chemin au parent — on ne modifie jamais imageUrl localement
		if (selectedPath && typeof selectedPath === 'string') onchange?.(selectedPath);
	}

	// Retire uniquement la référence en base — ne touche jamais au fichier sur le disque.
	function clear(e: MouseEvent) {
		e.stopPropagation();
		onchange?.('');
	}

	let overlay = $derived(
		isEditing
			? { icon: '📁', text: "Changer l'image" }
			: viewOverlayText && onViewClick
				? { icon: viewOverlayIcon, text: viewOverlayText }
				: null
	);
	let onclick = $derived(isEditing ? pickFile : onViewClick);
</script>

<ImageFrame
	{title}
	path={imageUrl}
	{subtitle}
	{showPath}
	{missing}
	{fill}
	{frameClass}
	{overlay}
	{onclick}
	empty={isEditing
		? { icon: '📁', text: 'Parcourir', hint: 'Cliquer pour choisir un fichier' }
		: { text: 'Aucune image' }}
>
	{#snippet corner()}
		{#if isEditing && clearable && imageUrl}
			<button
				type="button"
				onclick={clear}
				title="Retirer l'image (le fichier reste sur le disque)"
				class="absolute top-2 right-2 z-10 w-6 h-6 flex items-center justify-center rounded-full bg-black/70 hover:bg-red-600 text-white text-xs transition-colors"
			>✕</button>
		{/if}
	{/snippet}
</ImageFrame>
