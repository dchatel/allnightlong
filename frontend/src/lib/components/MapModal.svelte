<script lang="ts">
	import { appState } from '$lib/state.svelte';
	import { fade, slide } from 'svelte/transition'; // [3]

	// Miroir ESA du relevé DSS2 couleur : l'appli ne dépend pas des serveurs du CDS pour l'imagerie
	const DSS_SURVEY_URL = 'https://skies.esac.esa.int/DSSColor/';

	let mapError = $state('');

	// Convertit "05 35 16.47 / 83.81" ou "05h 35m 17s" en valeur décimale (heures ou degrés)
	function parseSexagesimal(value: string): number | null {
		const sexagesimal = value.split('/')[0].replace(/,/g, '.');
		const [first, minutes = 0, seconds = 0] = (sexagesimal.match(/\d+(?:\.\d+)?/g) ?? []).map(Number);
		if (first === undefined) return null;

		const absolute = first + minutes / 60 + seconds / 3600;
		return sexagesimal.trim().startsWith('-') ? -absolute : absolute;
	}

	// Des coordonnées évitent la résolution du nom par Sesame, service uniquement hébergé au CDS
	function getAladinTarget(target: { name: string; ra: string; dec: string }): string {
		const raHours = parseSexagesimal(target.ra);
		const dec = parseSexagesimal(target.dec);
		if (raHours === null || dec === null) return target.name;

		return `${(raHours * 15).toFixed(6)} ${dec >= 0 ? '+' : ''}${dec.toFixed(6)}`;
	}

	function initAladin(node: HTMLElement) {
		let destroyed = false;
		mapError = '';

		// Import à la demande : ces 2,4 Mo ne doivent pas ralentir le démarrage de l'appli
		import('aladin-lite')
			.then(async ({ default: A }) => {
				await A.init;
				if (destroyed) return;

				A.aladin(node, {
					survey: DSS_SURVEY_URL,
					target: appState.activeTarget ? getAladinTarget(appState.activeTarget) : 'M42',
					fov: 1.5,
					showFullscreenControl: false,
					showLayersControl: true
				});
			})
			.catch((err) => {
				console.error("Erreur d'initialisation d'Aladin:", err);
				mapError = "Impossible d'initialiser la carte céleste.";
			});

		return {
			destroy() {
				destroyed = true;
			}
		};
	}
</script>

{#if appState.showMapModal && appState.activeTarget}
	<div 
		transition:fade={{ duration: 150 }}
		class="fixed inset-0 bg-black/85 backdrop-blur-md z-50 flex items-center justify-center p-8"
	>
		<div 
			transition:slide={{ duration: 200 }}
			class="bg-[#161619] border border-[#333] rounded-2xl w-[90vw] h-[85vh] flex flex-col overflow-hidden shadow-2xl"
		>
			<div class="h-14 border-b border-[#333] bg-[#1a1a1d] px-6 flex items-center justify-between shrink-0 select-none">
				<div class="flex items-center space-x-3">
					<span class="text-xl">🌌</span>
					<h2 class="text-sm font-bold uppercase tracking-widest text-white">
						Carte Céleste — {appState.activeTarget.name} ({appState.activeTarget.usualName || 'Inconnu'})
					</h2>
				</div>
				<button 
					onclick={() => appState.showMapModal = false}
					class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-surface-800 text-surface-400 hover:text-white transition-colors text-lg"
				>
					✕
				</button>
			</div>

			{#if mapError}
				<div class="flex-1 w-full bg-black flex items-center justify-center text-sm text-surface-400">
					{mapError}
				</div>
			{:else}
				<div use:initAladin class="flex-1 w-full bg-black"></div>
			{/if}
		</div>
	</div>
{/if}