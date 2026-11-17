<script lang="ts">
	import { appState, parseLegacyCoords, emptyObservationTarget, formatDate, formatDateTime, type ObservationTarget } from '$lib/state.svelte';
	import { fade, slide } from 'svelte/transition';
	import ImageGallery from '$lib/components/ImageGallery.svelte';
	import WeatherReadings from '$lib/components/WeatherReadings.svelte';

	let obs = $derived(appState.activeObservation);

	// Lecture : source = obs (original) hors édition, observationForm pendant l'édition.
	// Écriture : toujours vers observationForm — jamais l'original tant que ce n'est
	// pas sauvegardé. Même principe que TargetCard.
	function fieldValue(key: string) {
		return appState.isEditingObservation ? appState.observationForm[key] : obs?.[key];
	}
	function setField(key: string) {
		return (v: any) => { appState.observationForm[key] = v; };
	}

	let rows = $derived<ObservationTarget[]>(fieldValue('targets') ?? []);

	// Cible dont la galerie montre les images (null = toutes) ; remise à zéro à chaque rapport
	let filterTargetId = $state<number | null>(null);
	$effect(() => {
		appState.activeObservationId;
		filterTargetId = null;
	});

	function imageCount(targetId: number | null) {
		// Même règle que le filtre de la galerie : ses images et celles du champ entier
		return (fieldValue('images') ?? []).filter((i: any) => i.targetIds.length === 0 || i.targetIds.includes(targetId)).length;
	}

	// --- LIEU ---
	const NEW_LOCATION = 'new';
	let selectedLocation = $derived(appState.locationById(fieldValue('locationId')));

	function chooseLocation(select: HTMLSelectElement) {
		if (select.value !== NEW_LOCATION) {
			setField('locationId')(select.value ? Number(select.value) : null);
			return;
		}
		// La liste revient sur le lieu actuel : le nouveau lieu n'est choisi qu'une fois enregistré
		select.value = String(fieldValue('locationId') ?? '');
		// La carte s'ouvre sur les coordonnées déjà saisies en texte libre, s'il y en a
		appState.openLocationEditor(
			{ ...(parseLegacyCoords(fieldValue('legacyLocation')) ?? {}) },
			(saved) => setField('locationId')(saved.id)
		);
	}

	// Bortle de la nuit, sinon celui du lieu
	let bortle = $derived(fieldValue('bortle') ?? selectedLocation?.bortle ?? null);

	// --- DATES (TU) ---
	// Le champ datetime-local lit et écrit "AAAA-MM-JJTHH:MM" ; la base stocke "AAAA-MM-JJ HH:MM"
	function toInput(value: string) {
		return (value ?? '').replace(' ', 'T');
	}
	function setStart(value: string) {
		const start = value.replace('T', ' ');
		setField('start')(start);
		// Fin pré-remplie le même jour : il ne reste souvent qu'à changer l'heure (et le jour après minuit)
		if (!fieldValue('end') && start) setField('end')(start);
	}

	// --- CIBLES ---
	function addTarget() {
		appState.observationForm.targets = [...rows, emptyObservationTarget()];
	}
	function removeTarget(index: number) {
		appState.observationForm.targets = rows.filter((_, i) => i !== index);
	}
	// Une cible déjà présente dans une autre ligne n'est pas proposée
	function choices(index: number) {
		const used = new Set(rows.filter((_, i) => i !== index).map(r => r.targetId));
		return appState.targetsByName.filter(t => !used.has(t.id));
	}
	const NEW_TARGET = 'new';

	function chooseTarget(row: ObservationTarget, select: HTMLSelectElement) {
		if (select.value !== NEW_TARGET) {
			row.targetId = select.value ? Number(select.value) : null;
			return;
		}
		// La liste revient sur la cible actuelle : la nouvelle n'est choisie qu'une fois créée
		select.value = String(row.targetId ?? '');
		appState.openTargetCreator((saved) => (row.targetId = saved.id));
	}

	// Rappel de la cible sous son nom : nom usuel, constellation, type
	function targetSummary(target: any) {
		return [target.usualName, target.constellation, target.type].filter(Boolean).join(' · ');
	}

	// Temps d'acquisition : toutes les poses prises, retenues ou non
	let totalDuration = $derived(((Number(fieldValue('imgTotal')) || 0) * (Number(fieldValue('subExposure')) || 0)) / 60);

	// Temps de pose retenu pour cette cible
	function duration(row: ObservationTarget) {
		const minutes = ((Number(row.imgGood) || 0) * (Number(fieldValue('subExposure')) || 0)) / 60;
		return minutes ? `${minutes.toFixed(1)} min` : '—';
	}

	function total(row: ObservationTarget) {
		return (Number(row.imgGood) || 0) + (Number(row.imgPass) || 0) + (Number(row.imgBad) || 0);
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
				<div class="flex items-center space-x-3 min-w-0">
					<span class="text-xl">🔭</span>
					<h2 class="text-sm font-bold uppercase tracking-widest text-white truncate">
						Rapport du {formatDate(fieldValue('start')) || '…'}
						{#if appState.observationTargetNames({ targets: rows })}
							<span class="text-indigo-300"> — {appState.observationTargetNames({ targets: rows })}</span>
						{/if}
					</h2>
				</div>
				<div class="flex items-center space-x-2 shrink-0">
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
						<div class="grid grid-cols-1 md:grid-cols-2 gap-6 shrink-0">

							<!-- SESSION -->
							<div class="space-y-4 bg-[#1e1e21] p-4 rounded-lg border border-[#333]">
								<span class="text-[10px] uppercase font-bold text-surface-400 block border-b border-[#333] pb-1.5">1. Session</span>
								<!-- Lieu et Début calés à gauche, Bortle et Fin calés à droite -->
								<div class="flex justify-between gap-3">
									<div class="flex-1 min-w-0">
										<label for="obs-location" class="block text-[10px] text-surface-400 mb-1">Lieu</label>
										{#if appState.isEditingObservation}
											<div class="flex gap-1">
												<select
													id="obs-location"
													class="form-input flex-1 min-w-0"
													value={fieldValue('locationId') ?? ''}
													onchange={(e) => chooseLocation(e.currentTarget)}
												>
													<option value="">— Aucun lieu —</option>
													{#each appState.locations as location (location.id)}
														<option value={location.id}>{location.label}</option>
													{/each}
													<option value={NEW_LOCATION}>+ Nouveau lieu…</option>
												</select>
												{#if selectedLocation}
													<button
														type="button"
														title="Modifier ce lieu"
														onclick={() => appState.openLocationEditor({ ...selectedLocation })}
														class="btn-secondary text-xs px-2"
													>✎</button>
												{/if}
											</div>
											{#if !selectedLocation && fieldValue('legacyLocation')}
												<span class="block text-[10px] text-surface-500 mt-1">Ancienne saisie : {fieldValue('legacyLocation')}</span>
											{/if}
										{:else}
											<span id="obs-location" class="block text-sm text-white">{appState.locationText(obs) || '—'}</span>
										{/if}
									</div>
									<div class="w-28 shrink-0 text-right">
										<label for="obs-bortle" class="block text-[10px] text-surface-400 mb-1">Bortle (nuit)</label>
										{#if appState.isEditingObservation}
											<input
												id="obs-bortle"
												type="number"
												step="0.5"
												min="1"
												max="9"
												class="form-input"
												value={fieldValue('bortle') ?? ''}
												placeholder={selectedLocation?.bortle != null ? `${selectedLocation.bortle} (lieu)` : ''}
												oninput={(e) => setField('bortle')(e.currentTarget.value === '' ? null : Number(e.currentTarget.value))}
											/>
										{:else}
											<span id="obs-bortle" class="block text-sm text-white">{bortle ?? '—'}</span>
										{/if}
									</div>
								</div>
								<div class="flex justify-between gap-3">
									<div class="session-date">
										<label for="obs-start" class="block text-[10px] text-surface-400 mb-1">Début (TU)</label>
										{#if appState.isEditingObservation}
											<input id="obs-start" type="datetime-local" class="form-input px-1.5" value={toInput(fieldValue('start'))} oninput={(e) => setStart(e.currentTarget.value)} />
										{:else}
											<span id="obs-start" class="block text-sm text-white">{formatDateTime(fieldValue('start')) || '—'}</span>
										{/if}
									</div>
									<div class="session-date text-right">
										<label for="obs-end" class="block text-[10px] text-surface-400 mb-1">Fin (TU)</label>
										{#if appState.isEditingObservation}
											<input id="obs-end" type="datetime-local" class="form-input px-1.5" value={toInput(fieldValue('end'))} oninput={(e) => setField('end')(e.currentTarget.value.replace('T', ' '))} />
										{:else}
											<span id="obs-end" class="block text-sm text-white">{formatDateTime(fieldValue('end')) || '—'}</span>
										{/if}
									</div>
								</div>
							</div>

							<!-- MATÉRIEL & POSE -->
							<div class="bg-[#1e1e21] p-4 rounded-lg border border-[#333]">
								<span class="text-[10px] uppercase font-bold text-surface-400 block border-b border-[#333] pb-1.5 mb-4">2. Matériel</span>
								<div class="grid grid-cols-2 gap-x-3 gap-y-4">
									{#each [
										{ key: 'instrument', label: 'Instrument (facultatif)' },
										{ key: 'sensor', label: 'Capteur' },
										{ key: 'filter', label: 'Filtre' },
										{ key: 'sensorTemp', label: 'Temp. Capteur (°C)' }
									] as field (field.key)}
										<div>
											<label for="obs-{field.key}" class="block text-[10px] text-surface-400 mb-1">{field.label}</label>
											{#if appState.isEditingObservation}
												<input id="obs-{field.key}" type="text" class="form-input" value={fieldValue(field.key)} oninput={(e) => setField(field.key)(e.currentTarget.value)} />
											{:else}
												<span id="obs-{field.key}" class="block text-sm text-white">{fieldValue(field.key) || '—'}</span>
											{/if}
										</div>
									{/each}
								</div>
							</div>
						</div>

						<!-- CIBLES DU CHAMP -->
						<div class="bg-[#1e1e21] p-4 rounded-lg border border-[#333] shrink-0">
							<div class="flex items-end justify-between gap-4 border-b border-[#333] pb-1.5 mb-2">
								<span class="text-[10px] uppercase font-bold text-surface-400 whitespace-nowrap">Cibles du champ</span>
								<!-- Total des poses × pose individuelle = durée totale d'acquisition -->
								<div class="flex items-center gap-2 text-[10px] text-surface-400 whitespace-nowrap">
									<label for="obs-imgTotal">Total des poses</label>
									{#if appState.isEditingObservation}
										<input id="obs-imgTotal" type="number" min="0" class="form-input py-0.5" style="width: 5rem" value={fieldValue('imgTotal')} oninput={(e) => setField('imgTotal')(Number(e.currentTarget.value))} />
									{:else}
										<span id="obs-imgTotal" class="text-sm font-bold text-white">{fieldValue('imgTotal') ?? 0}</span>
									{/if}
									<span class="text-sm text-surface-500">×</span>
									<label for="obs-subExposure">Pose indiv.</label>
									{#if appState.isEditingObservation}
										<input id="obs-subExposure" type="text" class="form-input py-0.5" style="width: 3.5rem" value={fieldValue('subExposure')} oninput={(e) => setField('subExposure')(e.currentTarget.value)} />
									{:else}
										<span id="obs-subExposure" class="text-sm font-bold text-white">{fieldValue('subExposure') || '—'}</span>
									{/if}
									<span>s</span>
									<span class="text-sm text-surface-500">=</span>
									<span>Durée totale</span>
									<span class="text-sm font-black text-white">{totalDuration.toFixed(1)} min</span>
								</div>
							</div>
							<div class="grid grid-cols-[minmax(0,1.6fr)_minmax(0,0.7fr)_repeat(3,minmax(0,0.55fr))_minmax(0,0.6fr)_auto] gap-x-2 gap-y-1 items-center">
								<span class="text-[10px] text-surface-400">Cible</span>
								<span class="text-[10px] text-surface-400">Hauteur (°)</span>
								<span class="text-[10px] text-green-400">Bon</span>
								<span class="text-[10px] text-yellow-500">Pass</span>
								<span class="text-[10px] text-red-500">Bad</span>
								<span class="text-[10px] text-surface-400" title="Poses retenues × pose individuelle">Durée retenue</span>
								<span class="text-[10px] text-surface-400">{appState.isEditingObservation ? '' : 'Images'}</span>

								{#each rows as row, i (i)}
									{@const target = appState.targets.find(t => t.id === row.targetId)}
									{#if appState.isEditingObservation}
										<div class="min-w-0">
											<div class="flex gap-1">
											<select
												class="form-input flex-1 min-w-0"
												value={row.targetId ?? ''}
												onchange={(e) => chooseTarget(row, e.currentTarget)}
											>
												<option value="">— Choisir une cible —</option>
												{#each choices(i) as choice (choice.id)}
													<option value={choice.id}>{choice.name}{choice.usualName ? ` (${choice.usualName})` : ''}</option>
												{/each}
												<option value={NEW_TARGET}>+ Nouvelle cible…</option>
											</select>
											{#if target}
												<button type="button" title="Voir la fiche de la cible" onclick={() => appState.openTargetSheet(target.id)} class="btn-secondary px-2 flex items-center">
													<svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 10.5v6" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/><circle cx="12" cy="7.3" r="1.3" fill="currentColor"/></svg>
												</button>
											{/if}
											</div>
										</div>
										<input type="text" class="form-input" bind:value={row.altitude} />
										<input type="number" min="0" class="form-input px-1" bind:value={row.imgGood} />
										<input type="number" min="0" class="form-input px-1" bind:value={row.imgPass} />
										<input type="number" min="0" class="form-input px-1" bind:value={row.imgBad} />
										<span class="text-sm text-surface-300">{duration(row)}</span>
										<button type="button" title="Retirer cette cible" onclick={() => removeTarget(i)} class="text-red-400 hover:text-red-300 px-1">✕</button>
										<!-- Rappel de la cible sur sa propre ligne : la ligne des champs reste alignée -->
										{#if target}
											<span class="col-span-7 -mt-0.5 text-[10px] text-surface-500 truncate">{targetSummary(target)}</span>
										{/if}
										<input
											type="text"
											class="form-input col-span-6 mb-2"
											placeholder="Note pour cette cible (facultatif)"
											bind:value={row.notes}
										/>
										<span></span>
									{:else}
										<div class="min-w-0">
											{#if target}
												<button
													type="button"
													title="Voir la fiche de la cible"
													onclick={() => appState.openTargetSheet(target.id)}
													class="text-sm font-bold text-white hover:text-indigo-300 underline decoration-dotted underline-offset-4"
												>{target.name}</button>
												<span class="block text-[10px] text-surface-400 leading-snug">{targetSummary(target)}</span>
											{:else}
												<span class="text-sm text-surface-500">Cible inconnue</span>
											{/if}
										</div>
										<span class="text-sm text-white">{row.altitude || '—'}</span>
										<div class="col-span-3">
											<span class="text-sm">
												<span class="text-green-400">{row.imgGood}</span> /
												<span class="text-yellow-500">{row.imgPass}</span> /
												<span class="text-red-500">{row.imgBad}</span>
											</span>
											{#if total(row) > 0}
												<div class="flex gap-0.5 mt-1 h-1.5 rounded-full overflow-hidden">
													<div class="bg-green-400" style="flex: {row.imgGood || 0}"></div>
													<div class="bg-yellow-500" style="flex: {row.imgPass || 0}"></div>
													<div class="bg-red-500" style="flex: {row.imgBad || 0}"></div>
												</div>
											{/if}
										</div>
										<span class="text-sm text-white">{duration(row)}</span>
										<button
											type="button"
											title="Afficher les images de cette cible"
											onclick={() => (filterTargetId = filterTargetId === row.targetId ? null : row.targetId)}
											class="text-xs px-2 py-0.5 rounded-full border transition-colors {filterTargetId === row.targetId ? 'bg-indigo-500 border-indigo-500 text-white font-bold' : 'border-[#333] text-surface-300 hover:border-indigo-500'}"
										>🖼 {imageCount(row.targetId)}</button>
										{#if row.notes}
											<p class="col-span-7 text-xs text-surface-300 whitespace-pre-wrap -mt-0.5 mb-1.5">Note : {row.notes}</p>
										{/if}
									{/if}
								{/each}
							</div>
							{#if appState.isEditingObservation}
								<button type="button" onclick={addTarget} class="mt-1 text-xs font-bold text-indigo-400 hover:text-indigo-300">+ Ajouter une cible</button>
							{:else if rows.length === 0}
								<p class="text-xs text-surface-500">Aucune cible.</p>
							{/if}
						</div>

						<!-- NOTES DE SÉANCE -->
						<div class="flex flex-col">
							<label for="obs-notes" class="block text-xs text-surface-400 mb-1 shrink-0">Notes de la séance</label>
							{#if appState.isEditingObservation}
								<textarea id="obs-notes" class="form-input min-h-40 resize-y py-2" value={fieldValue('notes')} oninput={(e) => setField('notes')(e.currentTarget.value)}></textarea>
							{:else}
								<p id="obs-notes" class="text-sm text-white whitespace-pre-wrap min-h-12">{fieldValue('notes') || '—'}</p>
							{/if}
						</div>

						<!-- CONDITIONS DE LA NUIT (session) -->
						<WeatherReadings sessionId={obs.sessionId} />
					</div>

					<!-- Images -->
					<div class="xl:col-span-4">
						<ImageGallery
							images={fieldValue('images') ?? []}
							{rows}
							isEditing={appState.isEditingObservation}
							setImages={(images) => (appState.observationForm.images = images)}
							bind:filterTargetId
						/>
					</div>

				</div>
			</div>
		</div>
	</div>
{/if}

<style>
	/* Largeur commune du début et de la fin : une date + heure a toujours la même longueur */
	.session-date {
		width: 11.5rem;
		flex-shrink: 0;
	}
</style>
