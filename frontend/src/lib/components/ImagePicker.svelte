<script lang="ts">
	import { open } from '@tauri-apps/plugin-dialog';
	import { convertFileSrc } from '@tauri-apps/api/core';

	// Les "Props" du composant (Svelte 5)
	let {
		title,
		imageUrl,               // valeur affichée, fournie par le parent (lecture seule ici)
		onchange = undefined,   // remonte le nouveau chemin choisi par l'utilisateur
		isEditing = false,
		viewOverlayText = "",
		viewOverlayIcon = "🌌",
		onViewClick = undefined
	} = $props();

	// Calcul automatique de l'URL d'affichage (Local vs Web)
	let displayUrl = $derived.by(() => {
		if (!imageUrl) return '';
		if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://')) {
			return imageUrl; // Lien Web normal
		}
		// Lien du disque dur local : on le convertit pour Tauri
		try {
			return convertFileSrc(imageUrl);
		} catch (e) {
			return imageUrl;
		}
	});

	// Gestion du clic
	async function handleClick() {
		if (isEditing) {
			// Mode Édition : Ouvrir l'explorateur Windows
			const selectedPath = await open({
				multiple: false,
				title: `Choisir une image pour : ${title}`,
				filters: [{ name: 'Images', extensions: ['png', 'jpg', 'jpeg', 'webp', 'fits'] }]
			});

			// Si l'utilisateur a sélectionné un fichier, on remonte le nouveau chemin
			// au parent — on ne modifie jamais imageUrl localement (prop en lecture seule).
			if (selectedPath && typeof selectedPath === 'string') {
				onchange?.(selectedPath);
			}
		} else if (onViewClick) {
			// Mode Vue : Exécuter l'action personnalisée (ex: ouvrir la carte)
			onViewClick();
		}
	}
</script>

<button 
	onclick={handleClick}
	class="border border-[#333] p-2.5 rounded bg-[#1e1e21] flex flex-col flex-1 w-full h-full text-left group transition-colors"
	class:hover:border-indigo-500={isEditing || onViewClick}
	class:cursor-pointer={isEditing || onViewClick}
	class:cursor-default={!isEditing && !onViewClick}
>
	<span class="text-[10px] uppercase font-bold text-surface-400 mb-1.5 block">{title}</span>
	
	<div class="flex-1 min-h-0 rounded flex items-center justify-center overflow-hidden relative bg-black/30 w-full border border-dashed border-transparent"
		 class:border-[#444]={isEditing && !imageUrl}>
		
		{#if displayUrl}
			<!-- L'image est présente -->
			<img src={displayUrl} alt={title} class="w-full h-full object-contain group-hover:scale-105 transition-transform duration-300" />
			
			<!-- Overlay Édition -->
			{#if isEditing}
				<div class="absolute inset-0 bg-black/70 opacity-0 group-hover:opacity-100 flex flex-col justify-center items-center transition-opacity">
					<span class="text-xl mb-1">📁</span>
					<span class="text-[9px] text-white font-bold tracking-wider uppercase">Changer l'image</span>
				</div>
			<!-- Overlay Vue (Optionnel) -->
			{:else if viewOverlayText && onViewClick}
				<div class="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 flex flex-col justify-center items-center transition-opacity">
					<span class="text-xl mb-1">{viewOverlayIcon}</span>
					<span class="text-[9px] text-white font-bold tracking-wider uppercase">{viewOverlayText}</span>
				</div>
			{/if}
			
		{:else}
			<!-- Pas d'image -->
			<div class="text-center p-2 flex flex-col items-center">
				{#if isEditing}
					<span class="text-xl mb-1 text-[#444] group-hover:text-indigo-400 transition-colors">📁</span>
					<span class="text-[10px] text-[#777] group-hover:text-indigo-300 transition-colors font-bold">Parcourir</span>
					<span class="text-[8px] text-[#555]">Cliquer pour choisir un fichier</span>
				{:else}
					<span class="text-[10px] text-[#777] font-bold">Aucune image</span>
				{/if}
			</div>
		{/if}
	</div>
</button>