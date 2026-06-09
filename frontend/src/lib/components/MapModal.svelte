<script lang="ts">
	import { appState } from '$lib/state.svelte';
	import { fade, slide } from 'svelte/transition'; // [3]

	function initAladin(node: HTMLElement) {
		const A = (window as any).A;
		if (!A) return;

		A.init.then(() => {
			A.aladin(node, {
				survey: 'P/DSS2/color',
				target: appState.activeTarget ? appState.activeTarget.name : 'M42',
				fov: 1.5,
				showFullscreenControl: false,
				showLayersControl: true
			});
		});
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

			<div use:initAladin class="flex-1 w-full bg-black"></div>
		</div>
	</div>
{/if}