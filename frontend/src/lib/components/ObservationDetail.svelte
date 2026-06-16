<script lang="ts">
	import { appState } from '$lib/state.svelte';
	import { fade, slide } from 'svelte/transition'; // [3]

    let obs = $derived(appState.activeObservation!);
</script>

<div in:slide={{ duration: 150 }} out:fade={{ duration: 150 }} class="flex flex-col h-auto xl:h-full space-y-6">
	
	<!-- Header -->
	<div class="flex justify-between items-center border-b border-[#333] pb-4 shrink-0">
		<div class="flex items-center space-x-3">
			<button onclick={() => appState.bottomView = 'list'} class="btn-secondary text-xs">← Retour à l'historique</button>
			<h2 class="text-sm font-bold uppercase tracking-widest text-surface-100">Rapport du {obs.date}</h2>
		</div>
		<div class="flex space-x-2">
			<button onclick={() => appState.saveObservation()} class="btn-primary text-xs">Sauvegarder</button>
			<button onclick={() => appState.deleteObservation()} class="btn-danger text-xs">Supprimer ce rapport</button>
		</div>
	</div>

	<!-- Formulaire & Images (Défilement indépendant !) [3] -->
	<div class="grid grid-cols-1 xl:grid-cols-12 gap-8 xl:flex-1 xl:min-h-0 xl:overflow-y-auto pr-2">
		
		<div class="xl:col-span-8 space-y-6">
			<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
				
				<!-- SESSION -->
				<div class="space-y-4 bg-[#1e1e21] p-4 rounded-lg border border-[#333]">
					<span class="text-[10px] uppercase font-bold text-surface-400 block border-b border-[#333] pb-1.5">1. Session</span>
					<div>
						<label for="obs-date" class="block text-[10px] text-surface-400 mb-1">Date</label>
						<input id="obs-date" type="date" class="form-input" bind:value={obs.date} />
					</div>
					<div class="grid grid-cols-2 gap-2">
						<div>
							<label for="obs-obsStart" class="block text-[10px] text-surface-400 mb-1">Début</label>
							<input id="obs-obsStart" type="time" class="form-input" bind:value={obs.obsStart} />
						</div>
						<div>
							<label for="obs-obsEnd" class="block text-[10px] text-surface-400 mb-1">Fin</label>
							<input id="obs-obsEnd" type="time" class="form-input" bind:value={obs.obsEnd} />
						</div>
					</div>
					<div>
						<label for="obs-location" class="block text-[10px] text-surface-400 mb-1">Localisation</label>
						<input id="obs-location" type="text" class="form-input" bind:value={obs.location} />
					</div>
					<div>
						<label for="obs-altitude" class="block text-[10px] text-surface-400 mb-1">Hauteur de cible (°)</label>
                        <input id="obs-altitude" type="text" class="form-input" bind:value={obs.altitude} />
					</div>
				</div>

				<!-- POSE -->
				<div class="space-y-4 bg-[#1e1e21] p-4 rounded-lg border border-[#333]">
					<span class="text-[10px] uppercase font-bold text-surface-400 block border-b border-[#333] pb-1.5">2. Matériel & Pose</span>
					<div>
						<label for="obs-sensor" class="block text-[10px] text-surface-400 mb-1">Capteur</label>
                        <input id="obs-sensor" type="text" class="form-input" bind:value={obs.sensor} />
					</div>
					<div>
						<label for="obs-filter" class="block text-[10px] text-surface-400 mb-1">Filtre</label>
                        <input id="obs-filter" type="text" class="form-input" bind:value={obs.filter} />
					</div>
					<div>
						<label for="obs-sensorTemp" class="block text-[10px] text-surface-400 mb-1">Temp. Capteur (°C)</label>
                        <input id="obs-sensorTemp" type="text" class="form-input" bind:value={obs.sensorTemp} />
					</div>
					<div>
						<label for="obs-subExposure" class="block text-[10px] text-surface-400 mb-1">Pose indiv. (s)</label>
                        <input id="obs-subExposure" type="text" class="form-input" bind:value={obs.subExposure} />
					</div>
				</div>

				<!-- IMAGES STATS -->
				<div class="space-y-4 bg-[#1e1e21] p-4 rounded-lg border border-[#333]">
					<span class="text-[10px] uppercase font-bold text-surface-400 block border-b border-[#333] pb-1.5">3. Images</span>
					<div class="grid grid-cols-2 gap-2">
						<div>
							<label for="obs-imgTotal" class="block text-[10px] text-surface-400 mb-1">Total</label>
                            <input id="obs-imgTotal" type="number" class="form-input" bind:value={obs.imgTotal} />
						</div>
						<div>
							<label for="obs-lightImages" class="block text-[10px] text-indigo-400 mb-1 font-bold">Lights</label>
                            <input id="obs-lightImages" type="text" class="form-input text-indigo-400 font-bold bg-[#1a1a1d]" disabled value={appState.calculatedLightImages} />
                        </div>
					</div>
					<div class="grid grid-cols-3 gap-1 text-[9px]">
						<div>
							<label for="obs-imgGood" class="block text-[9px] text-green-400 mb-1">Bon</label>
                            <input id="obs-imgGood" type="number" class="form-input px-1" bind:value={obs.imgGood} />
						</div>
						<div>
							<label for="obs-imgPass" class="block text-[9px] text-yellow-500 mb-1">Pass</label>
                            <input id="obs-imgPass" type="number" class="form-input px-1" bind:value={obs.imgPass} />
						</div>
						<div>
							<label for="obs-imgBad" class="block text-[9px] text-red-500 mb-1">Bad</label>
                            <input id="obs-imgBad" type="number" class="form-input px-1" bind:value={obs.imgBad} />
						</div>
					</div>
					<div class="border-t border-[#333] pt-2">
						<span class="text-[10px] text-surface-400 block mb-1">Durée totale :</span>
						<span class="text-sm font-black text-white">{appState.calculatedDuration.toFixed(1)} min</span>
					</div>
				</div>

			</div>

			<div class="col-span-3">
				<label for="obs-otherObjects" class="block text-xs text-surface-400 mb-1">Autres objets dans le champ / Notes</label>
                <textarea id="obs-otherObjects" class="form-input h-24 resize-none py-2" bind:value={obs.otherObjects}></textarea>
			</div>
		</div>

		<!-- Images -->
		<div class="xl:col-span-4 space-y-4">
			<div class="border border-[#333] p-3 rounded bg-[#1a1a1d] flex flex-col h-60">
				<span class="text-[10px] uppercase font-bold text-surface-400 mb-2">Image Brute (Seestar)</span>
				<div class="flex-1 border border-dashed border-[#444] rounded flex flex-col items-center justify-center overflow-hidden relative group">
					{#if obs.imageRaw}
						<img src={obs.imageRaw} alt="Brute" class="w-full h-full object-cover" />
					{:else}
						<span class="text-[10px] text-[#555] font-bold">Lier JPEG Seestar</span>
					{/if}
				</div>
			</div>

			<div class="border border-[#333] p-3 rounded bg-[#1a1a1d] flex flex-col h-60">
				<span class="text-[10px] uppercase font-bold text-surface-400 mb-2">Image finale traitée</span>
				<div class="flex-1 border border-dashed border-[#444] rounded flex flex-col items-center justify-center overflow-hidden relative group">
					{#if obs.imageProcessed}
						<img src={obs.imageProcessed} alt="Traitée" class="w-full h-full object-cover" />
					{:else}
						<span class="text-[10px] text-[#555] font-bold">Lier image finale</span>
					{/if}
				</div>
			</div>
		</div>

	</div>
</div>