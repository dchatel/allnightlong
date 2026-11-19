<script lang="ts">
	import type { Snippet } from 'svelte';
	import { imageSrc } from '$lib/state.svelte';

	// Présentation commune des images (fiche cible, galerie du rapport) :
	// titre au-dessus, cadre, légende en dessous. Gère l'image absente et le fichier introuvable.
	let {
		title = '',
		path = '',
		subtitle = '',
		showPath = false,
		missing = false,
		highlight = false,
		fill = false,
		frameClass = 'h-52',
		overlay = null,
		empty = { text: 'Aucune image', hint: '' },
		onclick = undefined,
		headerRight = undefined,
		header = undefined,
		corner = undefined
	}: {
		title?: string;
		path?: string;
		subtitle?: string;
		// Chemin du fichier sous l'image, en discret : utile pour vérifier où l'application va le chercher
		showPath?: boolean;
		missing?: boolean;
		// Bordure dorée (image favorite)
		highlight?: boolean;
		// Le cadre occupe toute la hauteur disponible
		fill?: boolean;
		frameClass?: string;
		// Texte affiché au survol quand l'image est cliquable
		overlay?: { icon: string; text: string } | null;
		empty?: { text: string; hint?: string; icon?: string };
		onclick?: () => void;
		headerRight?: Snippet;
		// Remplace le titre à gauche de l'en-tête (texte mis en forme)
		header?: Snippet;
		// Bouton posé dans l'angle du cadre (retirer l'image)
		corner?: Snippet;
	} = $props();

	// Fichier illisible (déplacé, disque débranché) : même affichage qu'un fichier signalé manquant
	let broken = $state(false);
	$effect(() => {
		path;
		broken = false;
	});
	let unavailable = $derived(missing || broken);
</script>

{#snippet content()}
	{#if title || header || headerRight}
		<span class="flex items-center justify-between gap-2 mb-1 shrink-0">
			{#if header}{@render header()}{:else}<span class="text-xs font-bold text-white truncate">{title}</span>{/if}
			{@render headerRight?.()}
		</span>
	{/if}
	<span
		class="relative block rounded border transition-colors overflow-hidden {fill ? 'flex-1 min-h-0' : frameClass}
			{highlight ? 'border-yellow-500/70' : 'border-[#333]'} {onclick ? 'group-hover:border-indigo-500' : ''}"
	>
		{#if !path}
			<span class="absolute inset-0 rounded border border-dashed border-[#444] flex flex-col items-center justify-center text-center p-2 bg-black/30">
				{#if empty.icon}<span class="text-xl mb-1 text-[#555] group-hover:text-indigo-400 transition-colors">{empty.icon}</span>{/if}
				<span class="text-[11px] font-bold text-surface-400 group-hover:text-indigo-300 transition-colors">{empty.text}</span>
				{#if empty.hint}<span class="text-[9px] text-surface-500 mt-0.5">{empty.hint}</span>{/if}
			</span>
		{:else if unavailable}
			<span class="absolute inset-0 rounded border border-dashed border-[#444] flex flex-col items-center justify-center text-center p-2 bg-black/30">
				<span class="text-[11px] font-bold text-surface-400">Image introuvable</span>
				<span class="text-[9px] text-surface-500 break-all mt-1">{path}</span>
			</span>
		{:else}
			<img src={imageSrc(path)} alt={title} onerror={() => (broken = true)} class="absolute inset-0 w-full h-full object-contain bg-black/30" />
		{/if}
		{#if overlay && path}
			<span class="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 flex flex-col justify-center items-center transition-opacity">
				<span class="text-xl mb-1">{overlay.icon}</span>
				<span class="text-[9px] text-white font-bold tracking-wider uppercase">{overlay.text}</span>
			</span>
		{/if}
		{@render corner?.()}
	</span>
	{#if subtitle}
		<span class="block text-[10px] text-surface-400 mt-1 truncate shrink-0">{subtitle}</span>
	{/if}
	{#if showPath && path && !unavailable}
		<!-- Coupé au début plutôt qu'à la fin : le nom du fichier reste lisible.
		     Une image introuvable affiche déjà son chemin dans le cadre. -->
		<span class="path block text-[9px] text-surface-500 truncate shrink-0" title={path}><bdi>{path}</bdi></span>
	{/if}
{/snippet}

{#if onclick}
	<!-- div cliquable plutôt que <button> : l'angle peut contenir un vrai bouton (retirer l'image) -->
	<div
		role="button"
		tabindex="0"
		{onclick}
		onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onclick?.(); } }}
		class="group text-left cursor-pointer flex flex-col {fill ? 'h-full' : ''}"
	>
		{@render content()}
	</div>
{:else}
	<div class="flex flex-col {fill ? 'h-full' : ''}">
		{@render content()}
	</div>
{/if}

<style>
	.path {
		direction: rtl;
		text-align: left;
	}
</style>
