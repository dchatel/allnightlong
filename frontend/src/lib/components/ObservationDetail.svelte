<script lang="ts">
	import { appState } from '$lib/state.svelte';
	import { fade, slide } from 'svelte/transition';
	import ImagePicker from '$lib/components/ImagePicker.svelte';

	let obs = $derived(appState.activeObservation);

	// --- CALCULS DU GRAPHIQUE SVG (ANNEAU ÉPAIS ANIMÉ) ---
	let goodCount = $derived(Number(fieldValue('imgGood')) || 0);
	let passCount = $derived(Number(fieldValue('imgPass')) || 0);
	let badCount = $derived(Number(fieldValue('imgBad')) || 0);
	let totalGraded = $derived(goodCount + passCount + badCount);

	let goodPct = $derived(totalGraded === 0 ? 0 : (goodCount / totalGraded) * 100);
	let passPct = $derived(totalGraded === 0 ? 0 : (passCount / totalGraded) * 100);
	let badPct = $derived(totalGraded === 0 ? 0 : (badCount / totalGraded) * 100);

	// On ajoute un gap (2%) uniquement s'il y a plus d'une catégorie utilisée
	let activeSegments = $derived((goodCount > 0 ? 1 : 0) + (passCount > 0 ? 1 : 0) + (badCount > 0 ? 1 : 0));
	let gap = $derived(activeSegments > 1 ? 2 : 0);

	// Longueur de chaque segment (on soustrait le gap pour faire la coupure)
	let goodDash = $derived(goodPct > gap ? goodPct - gap : goodPct);
	let passDash = $derived(passPct > gap ? passPct - gap : passPct);
	let badDash = $derived(badPct > gap ? badPct - gap : badPct);

	// Position de départ de chaque segment sur le cercle
	let passOffset = $derived(-goodPct);
	let badOffset = $derived(-(goodPct + passPct));
	// ------------------------------------------------------

	// Lecture : source = obs (original) hors édition, observationForm pendant l'édition.
	// Écriture : toujours vers observationForm — jamais l'original tant que ce n'est
	// pas sauvegardé. Même principe que TargetCard.
	function fieldValue(key: string) {
		return appState.isEditingObservation ? appState.observationForm[key] : obs?.[key];
	}
	function setField(key: string) {
		return (v: any) => { appState.observationForm[key] = v; };
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape' && appState.isObservationModalOpen) {
			appState.closeObservation();
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

{#if appState.isObservationModalOpen && obs}
	<!--
		Le clic sur ce calque de fond est une commodité souris ; l'équivalent
		clavier est Échap (géré ci-dessus via svelte:window), pas un focus sur
		ce div. Rendre ce calque focusable (role="button" + tabindex) serait
		pire pour l'accessibilité : un immense piège à focus derrière la vraie
		zone interactive, sans bénéfice réel pour un utilisateur clavier.
	-->
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		transition:fade={{ duration: 150 }}
		onclick={() => appState.closeObservation()}
		class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-8"
	>
		<div
			transition:slide={{ duration: 200 }}
			onclick={(e) => e.stopPropagation()}
			class="bg-[#161619] border border-[#333] rounded-2xl w-[90vw] h-[85vh] flex flex-col overflow-hidden shadow-2xl"
		>
			<!-- Header -->
			<div class="h-14 border-b border-[#333] bg-[#1a1a1d] px-6 flex items-center justify-between shrink-0 select-none">
				<div class="flex items-center space-x-3">
					<span class="text-xl">🔭</span>
					<h2 class="text-sm font-bold uppercase tracking-widest text-white">
						Rapport du {fieldValue('date')}
					</h2>
				</div>
				<div class="flex items-center space-x-2">
					{#if appState.isEditingObservation}
						<button onclick={() => appState.saveObservation()} class="btn-primary text-xs">Enregistrer</button>
						<button onclick={() => appState.cancelEditObservation()} class="btn-secondary text-xs">Annuler</button>
						<button onclick={() => appState.deleteObservation()} class="btn-danger text-xs">Supprimer</button>
					{:else}
						<button onclick={() => appState.startEditObservation()} class="btn-secondary text-xs">Modifier ce rapport</button>
					{/if}
					<button
						onclick={() => appState.closeObservation()}
						class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-surface-800 text-surface-400 hover:text-white transition-colors text-lg ml-2"
					>
						✕
					</button>
				</div>
			</div>

			<!-- Contenu -->
			<div class="flex-1 min-h-0 overflow-y-auto p-6 flex flex-col">
				<div class="grid grid-cols-1 xl:grid-cols-12 gap-8 flex-1">

					<div class="xl:col-span-8 flex flex-col gap-6">
						<div class="grid grid-cols-1 md:grid-cols-3 gap-6 shrink-0">

							<!-- SESSION -->
							<div class="space-y-4 bg-[#1e1e21] p-4 rounded-lg border border-[#333]">
								<span class="text-[10px] uppercase font-bold text-surface-400 block border-b border-[#333] pb-1.5">1. Session</span>
								<div>
									<label for="obs-date" class="block text-[10px] text-surface-400 mb-1">Date</label>
									{#if appState.isEditingObservation}
										<input id="obs-date" type="date" class="form-input" value={fieldValue('date')} oninput={(e) => setField('date')(e.currentTarget.value)} />
									{:else}
										<span id="obs-date" class="block text-sm text-white">{fieldValue('date')}</span>
									{/if}
								</div>
								<div class="grid grid-cols-2 gap-2">
									<div>
										<label for="obs-obsStart" class="block text-[10px] text-surface-400 mb-1">Début</label>
										{#if appState.isEditingObservation}
											<input id="obs-obsStart" type="time" class="form-input" value={fieldValue('obsStart')} oninput={(e) => setField('obsStart')(e.currentTarget.value)} />
										{:else}
											<span id="obs-obsStart" class="block text-sm text-white">{fieldValue('obsStart') || '—'}</span>
										{/if}
									</div>
									<div>
										<label for="obs-obsEnd" class="block text-[10px] text-surface-400 mb-1">Fin</label>
										{#if appState.isEditingObservation}
											<input id="obs-obsEnd" type="time" class="form-input" value={fieldValue('obsEnd')} oninput={(e) => setField('obsEnd')(e.currentTarget.value)} />
										{:else}
											<span id="obs-obsEnd" class="block text-sm text-white">{fieldValue('obsEnd') || '—'}</span>
										{/if}
									</div>
								</div>
								<div>
									<label for="obs-location" class="block text-[10px] text-surface-400 mb-1">Localisation</label>
									{#if appState.isEditingObservation}
										<input id="obs-location" type="text" class="form-input" value={fieldValue('location')} oninput={(e) => setField('location')(e.currentTarget.value)} />
									{:else}
										<span id="obs-location" class="block text-sm text-white">{fieldValue('location') || '—'}</span>
									{/if}
								</div>
								<div>
									<label for="obs-altitude" class="block text-[10px] text-surface-400 mb-1">Hauteur de cible (°)</label>
									{#if appState.isEditingObservation}
										<input id="obs-altitude" type="text" class="form-input" value={fieldValue('altitude')} oninput={(e) => setField('altitude')(e.currentTarget.value)} />
									{:else}
										<span id="obs-altitude" class="block text-sm text-white">{fieldValue('altitude') || '—'}</span>
									{/if}
								</div>
							</div>

							<!-- POSE -->
							<div class="space-y-4 bg-[#1e1e21] p-4 rounded-lg border border-[#333]">
								<span class="text-[10px] uppercase font-bold text-surface-400 block border-b border-[#333] pb-1.5">2. Matériel & Pose</span>
								<div>
									<label for="obs-sensor" class="block text-[10px] text-surface-400 mb-1">Capteur</label>
									{#if appState.isEditingObservation}
										<input id="obs-sensor" type="text" class="form-input" value={fieldValue('sensor')} oninput={(e) => setField('sensor')(e.currentTarget.value)} />
									{:else}
										<span id="obs-sensor" class="block text-sm text-white">{fieldValue('sensor') || '—'}</span>
									{/if}
								</div>
								<div>
									<label for="obs-filter" class="block text-[10px] text-surface-400 mb-1">Filtre</label>
									{#if appState.isEditingObservation}
										<input id="obs-filter" type="text" class="form-input" value={fieldValue('filter')} oninput={(e) => setField('filter')(e.currentTarget.value)} />
									{:else}
										<span id="obs-filter" class="block text-sm text-white">{fieldValue('filter') || '—'}</span>
									{/if}
								</div>
								<div>
									<label for="obs-sensorTemp" class="block text-[10px] text-surface-400 mb-1">Temp. Capteur (°C)</label>
									{#if appState.isEditingObservation}
										<input id="obs-sensorTemp" type="text" class="form-input" value={fieldValue('sensorTemp')} oninput={(e) => setField('sensorTemp')(e.currentTarget.value)} />
									{:else}
										<span id="obs-sensorTemp" class="block text-sm text-white">{fieldValue('sensorTemp') || '—'}</span>
									{/if}
								</div>
								<div>
									<label for="obs-subExposure" class="block text-[10px] text-surface-400 mb-1">Pose indiv. (s)</label>
									{#if appState.isEditingObservation}
										<input id="obs-subExposure" type="text" class="form-input" value={fieldValue('subExposure')} oninput={(e) => setField('subExposure')(e.currentTarget.value)} />
									{:else}
										<span id="obs-subExposure" class="block text-sm text-white">{fieldValue('subExposure') || '—'}</span>
									{/if}
								</div>
							</div>

							<!-- IMAGES STATS -->
							<div class="space-y-4 bg-[#1e1e21] p-4 rounded-lg border border-[#333]">
								<span class="text-[10px] uppercase font-bold text-surface-400 block border-b border-[#333] pb-1.5">3. Images</span>
								<div class="grid grid-cols-2 gap-2">
									<div>
										<label for="obs-imgTotal" class="block text-[10px] text-surface-400 mb-1">Total</label>
										{#if appState.isEditingObservation}
											<input id="obs-imgTotal" type="number" class="form-input" value={fieldValue('imgTotal')} oninput={(e) => setField('imgTotal')(Number(e.currentTarget.value))} />
										{:else}
											<span id="obs-imgTotal" class="block text-sm text-white">{fieldValue('imgTotal') ?? 0}</span>
										{/if}
									</div>
									<div>
										<span class="block text-[10px] text-indigo-400 mb-1 font-bold">Lights</span>
										<span class="block text-sm font-bold text-indigo-400">{appState.calculatedLightImages}</span>
									</div>
								</div>
								<div class="grid grid-cols-3 gap-1 text-[9px]">
									<div>
										<label for="obs-imgGood" class="block text-[9px] text-green-400 mb-1">Bon</label>
										{#if appState.isEditingObservation}
											<input id="obs-imgGood" type="number" class="form-input px-1" value={fieldValue('imgGood')} oninput={(e) => setField('imgGood')(Number(e.currentTarget.value))} />
										{:else}
											<span class="block text-sm text-green-400">{fieldValue('imgGood') ?? 0}</span>
										{/if}
									</div>
									<div>
										<label for="obs-imgPass" class="block text-[9px] text-yellow-500 mb-1">Pass</label>
										{#if appState.isEditingObservation}
											<input id="obs-imgPass" type="number" class="form-input px-1" value={fieldValue('imgPass')} oninput={(e) => setField('imgPass')(Number(e.currentTarget.value))} />
										{:else}
											<span class="block text-sm text-yellow-500">{fieldValue('imgPass') ?? 0}</span>
										{/if}
									</div>
									<div>
										<label for="obs-imgBad" class="block text-[9px] text-red-500 mb-1">Bad</label>
										{#if appState.isEditingObservation}
											<input id="obs-imgBad" type="number" class="form-input px-1" value={fieldValue('imgBad')} oninput={(e) => setField('imgBad')(Number(e.currentTarget.value))} />
										{:else}
											<span class="block text-sm text-red-500">{fieldValue('imgBad') ?? 0}</span>
										{/if}
									</div>
								</div>
								<div class="border-t border-[#333] pt-4 mt-2 flex items-center gap-6">
									<!-- GRAPHIQUE (Anneau très épais en bas à gauche) -->
									<div class="w-16 h-16 shrink-0 relative drop-shadow-md">
										<!-- 
											Astuce mathématique : Un cercle de rayon 15.9155 a une circonférence exacte de 100.
											Cela permet de mapper directement nos pourcentages (0 à 100) sur le stroke-dasharray !
										-->
										<svg viewBox="0 0 44 44" class="w-full h-full transform -rotate-90">
											<!-- Fond / Cercle vide (gris) -->
											<circle cx="22" cy="22" r="15.9155" fill="transparent" class="stroke-[#2a2a2e]" stroke-width="12" />
											
											<!-- Segment : Bon (Vert) -->
											<circle cx="22" cy="22" r="15.9155" fill="transparent" class="stroke-green-400" stroke-width="12" 
												stroke-dasharray="{goodDash} 100" stroke-dashoffset="0" 
												style="transition: stroke-dasharray 0.6s cubic-bezier(0.4, 0, 0.2, 1), stroke-dashoffset 0.6s cubic-bezier(0.4, 0, 0.2, 1);" />
												
											<!-- Segment : Pass (Jaune) -->
											<circle cx="22" cy="22" r="15.9155" fill="transparent" class="stroke-yellow-500" stroke-width="12" 
												stroke-dasharray="{passDash} 100" stroke-dashoffset="{passOffset}" 
												style="transition: stroke-dasharray 0.6s cubic-bezier(0.4, 0, 0.2, 1), stroke-dashoffset 0.6s cubic-bezier(0.4, 0, 0.2, 1);" />
												
											<!-- Segment : Bad (Rouge) -->
											<circle cx="22" cy="22" r="15.9155" fill="transparent" class="stroke-red-500" stroke-width="12" 
												stroke-dasharray="{badDash} 100" stroke-dashoffset="{badOffset}" 
												style="transition: stroke-dasharray 0.6s cubic-bezier(0.4, 0, 0.2, 1), stroke-dashoffset 0.6s cubic-bezier(0.4, 0, 0.2, 1);" />
										</svg>
										
										<!-- Petit label central optionnel (ex: % total, ou on le laisse vide) -->
										{#if totalGraded === 0}
											<div class="absolute inset-0 flex items-center justify-center text-[10px] text-surface-500">?</div>
										{/if}
									</div>

									<!-- TEXTE DURÉE TOTALE (Décalé sur la droite) -->
									<div class="flex flex-col">
										<span class="text-[10px] text-surface-400 mb-1">Durée totale</span>
										<span class="text-xl font-black text-white">{appState.calculatedDuration.toFixed(1)} <span class="text-xs text-surface-400 font-bold">min</span></span>
									</div>
								</div>
							</div>

						</div>

						<div class="flex-1 flex flex-col min-h-0">
							<label for="obs-otherObjects" class="block text-xs text-surface-400 mb-1 shrink-0">Autres objets dans le champ / Notes</label>
							{#if appState.isEditingObservation}
								<textarea id="obs-otherObjects" class="form-input flex-1 min-h-24 resize-none py-2" value={fieldValue('otherObjects')} oninput={(e) => setField('otherObjects')(e.currentTarget.value)}></textarea>
							{:else}
								<p id="obs-otherObjects" class="text-sm text-white whitespace-pre-wrap flex-1 overflow-y-auto min-h-12">{fieldValue('otherObjects') || '—'}</p>
							{/if}
						</div>
					</div>

					<!-- Images -->
					<div class="xl:col-span-4 space-y-4">
						<div class="h-64 flex flex-col">
							<ImagePicker
								title="Image Brute (Seestar)"
								imageUrl={fieldValue('imageRaw')}
								onchange={setField('imageRaw')}
								isEditing={appState.isEditingObservation}
							/>
						</div>

						<div class="h-64 flex flex-col">
							<ImagePicker
								title="Image finale traitée"
								imageUrl={fieldValue('imageProcessed')}
								onchange={setField('imageProcessed')}
								isEditing={appState.isEditingObservation}
							/>
						</div>
					</div>

				</div>
			</div>
		</div>
	</div>
{/if}