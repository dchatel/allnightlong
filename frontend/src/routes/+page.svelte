<script lang="ts">
	// Import du statut partagé
	import { appState } from '$lib/state.svelte';

	// Import des sous-composants
	import Sidebar from '$lib/components/Sidebar.svelte';
	import TargetCard from '$lib/components/TargetCard.svelte';
	import ObservationHistory from '$lib/components/ObservationHistory.svelte';
	import ObservationDetail from '$lib/components/ObservationDetail.svelte';
	import MapModal from '$lib/components/MapModal.svelte';
</script>

<div class="flex h-full w-full bg-[#121214] overflow-hidden">
	
	<!-- 1. BARRE LATÉRALE (GAUCHE) -->
	<Sidebar />

	<!-- 2. CONTENU PRINCIPAL (DROITE) -->
	<main class="flex-1 h-full flex flex-col bg-[#121214] p-8 space-y-6 overflow-y-auto xl:overflow-hidden">
		{#if appState.activeTarget}
			
			<!-- Fiche d'identité fixe -->
			<TargetCard />

			<!-- Zone basse hybride indépendante -->
			<div class="bg-[#161619] border border-[#2a2a2d] rounded-xl p-6 shadow-2xl flex flex-col shrink-0 h-auto xl:flex-1 xl:min-h-0 xl:overflow-hidden">
				{#if appState.bottomView === 'list'}
					<ObservationHistory />
				{:else}
					<ObservationDetail />
				{/if}
			</div>

		{:else}
			<!-- Écran d'accueil vide -->
			<div class="h-full w-full flex flex-col justify-center items-center p-8 opacity-40">
				<span class="text-6xl mb-4">🌌</span>
				<p class="text-sm">Sélectionnez ou créez un objet céleste pour commencer</p>
			</div>
		{/if}
	</main>

</div>

<!-- 3. LA MODALE CARTE (OVERLAY) -->
<MapModal />