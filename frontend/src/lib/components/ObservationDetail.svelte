<script lang="ts">
	import { appState, parseLegacyCoords, emptyObservationTarget, formatDate, formatDateTime, type ObservationTarget } from '$lib/state.svelte';
	import { fade, slide } from 'svelte/transition';
	import { open } from '@tauri-apps/plugin-dialog';
	import ImageGallery from '$lib/components/ImageGallery.svelte';
	import WeatherReadings from '$lib/components/WeatherReadings.svelte';
	import { makeObserver, targetAltitude, targetCoords, utcDate } from '$lib/astro';

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

	// Cible dont la galerie montre les images (null = toutes) : à chaque rapport, la cible d'où on l'a ouvert
	let filterTargetId = $state<number | null>(null);
	$effect(() => {
		appState.activeObservationId;
		filterTargetId = appState.observationOpenedFromTargetId;
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
	// Hauteur calculée de chaque cible pendant le créneau : au milieu et au plus haut
	let observer = $derived.by(() => {
		const location = appState.locationById(fieldValue('locationId'));
		const point = location ?? parseLegacyCoords(fieldValue('legacyLocation'));
		return point ? makeObserver(point.lat, point.lon, location?.elevationM) : null;
	});
	function computedAltitude(target: any) {
		const start = fieldValue('start'), end = fieldValue('end');
		const coords = targetCoords(target);
		if (!observer || !coords || !start || start.length <= 10 || !end || end.length <= 10) return null;
		const t0 = utcDate(start).getTime(), t1 = utcDate(end).getTime();
		if (!(t1 > t0)) return null;
		let max = -90;
		for (let t = t0; t <= t1; t += 10 * 60_000) max = Math.max(max, targetAltitude(coords, new Date(t), observer));
		return { middle: Math.round(targetAltitude(coords, new Date((t0 + t1) / 2), observer)), max: Math.round(max) };
	}

	function targetSummary(target: any) {
		return [target.usualName, target.constellation, target.type].filter(Boolean).join(' · ');
	}

	// Temps d'acquisition : toutes les poses prises, retenues ou non
	let totalDuration = $derived(((Number(fieldValue('imgTotal')) || 0) * (Number(fieldValue('subExposure')) || 0)) / 60);

	// Poses du champ : tout l'empilement est traité de la même façon pour chacune de ses cibles
	const POSE_FIELDS = [
		{ key: 'imgGood', label: 'Bon', color: 'text-green-400', stroke: 'stroke-green-400' },
		{ key: 'imgPass', label: 'Pass', color: 'text-yellow-500', stroke: 'stroke-yellow-500' },
		{ key: 'imgBad', label: 'Bad', color: 'text-red-500', stroke: 'stroke-red-500' }
	];
	let poseSum = $derived(POSE_FIELDS.reduce((sum, f) => sum + (Number(fieldValue(f.key)) || 0), 0));
	// Parts de l'anneau, en % du tour
	let poseSlices = $derived.by(() => {
		let offset = 0;
		return POSE_FIELDS.map(f => {
			const dash = poseSum ? ((Number(fieldValue(f.key)) || 0) / poseSum) * 100 : 0;
			const slice = { key: f.key, stroke: f.stroke, dash, offset };
			offset += dash;
			return slice;
		});
	});
	// Temps de pose retenu
	let keptDuration = $derived(((Number(fieldValue('imgGood')) || 0) * (Number(fieldValue('subExposure')) || 0)) / 60);

	// Reprise de l'ancien format : les cibles avaient des comptes différents (signalé tant que ce n'est pas réglé)
	let poseConflict = $derived<any[]>(obs?.poseConflict ?? []);
	let conflictKey = $derived(`poses-merge:${obs?.id}`);
	let showConflict = $derived(poseConflict.length > 0 && !appState.dismissedChecks.includes(conflictKey));

	// --- PRÉ-REMPLISSAGE DEPUIS UN FITS ---
	// Dossier du dernier FITS choisi : la fenêtre de choix s'y rouvre (préférence de ce poste seulement)
	const FITS_DIR_KEY = 'allnightlong.lastFitsDir';
	let fitsMessage = $state<{ filled: string[]; warnings: string[] } | null>(null);
	$effect(() => {
		appState.activeObservationId;
		fitsMessage = null;
	});

	// Noms de filtre du Seestar → ceux que l'utilisateur emploie dans ses rapports
	const FILTER_NAMES: Record<string, string> = { LP: 'LP dual bande', IRCUT: 'IRCUT' };

	async function fillFromFits() {
		let lastDir: string | undefined;
		try { lastDir = localStorage.getItem(FITS_DIR_KEY) ?? undefined; } catch { /* stockage indisponible */ }
		const picked = await open({
			multiple: false,
			title: 'Choisir le FITS empilé (Stacked_…) de cette observation',
			defaultPath: lastDir,
			filters: [{ name: 'FITS du Seestar', extensions: ['fit', 'fits', 'fts'] }]
		});
		if (typeof picked !== 'string') return;
		try { localStorage.setItem(FITS_DIR_KEY, picked.replace(/[\\/][^\\/]*$/, '')); } catch { /* idem */ }

		const fits = await appState.readFits(picked);
		if (!fits) return;
		const form = appState.observationForm;
		const filled: string[] = [];
		const warnings: string[] = [];

		form.start = fits.start;
		form.end = fits.end;
		filled.push(`début ${formatDateTime(fits.start)}, fin ${formatDateTime(fits.end)} (TU)`);
		if (!fits.startExact) warnings.push('Début estimé à partir du nombre de poses : le dossier « _sub » des poses n’a pas été trouvé.');
		if (fits.filter) {
			form.filter = FILTER_NAMES[fits.filter] ?? fits.filter;
			filled.push(`filtre ${form.filter}`);
		}
		if (fits.sensorTemp != null) {
			form.sensorTemp = fits.sensorTemp.toFixed(1);
			filled.push(`capteur ${form.sensorTemp} °C`);
		}
		if (fits.exposure) {
			form.subExposure = String(Math.round(fits.exposure * 10) / 10);
			filled.push(`pose ${form.subExposure} s`);
		}
		if (fits.frames) {
			form.imgTotal = fits.frames;
			filled.push(`${fits.frames} poses`);
		}
		if (fits.instrument && !String(form.sensor ?? '').toLowerCase().includes('seestar')) {
			form.sensor = fits.instrument;
		}
		if (fits.locationId) {
			form.locationId = fits.locationId;
			filled.push(`lieu ${appState.locationById(fits.locationId)?.label}`);
		} else {
			warnings.push('Aucun lieu enregistré près des coordonnées du Seestar : choisissez-le dans la liste.');
		}

		// Cibles : elles complètent le tableau, une ligne vide est réutilisée
		const present = new Set(form.targets.map((r: ObservationTarget) => r.targetId));
		for (const id of fits.targetIds.filter(id => !present.has(id))) {
			const empty = form.targets.find((r: ObservationTarget) => !r.targetId);
			if (empty) empty.targetId = id;
			else form.targets = [...form.targets, emptyObservationTarget(id)];
		}
		if (fits.targetIds.length) {
			filled.push(`cible${fits.targetIds.length > 1 ? 's' : ''} ${fits.targetIds.map(id => appState.targetName(id)).join(', ')}`);
		} else {
			warnings.push(`Cible « ${fits.object || '?'} » introuvable dans vos cibles : choisissez-la ou créez-la dans le tableau.`);
		}

		// Aperçu enregistré par le Seestar, ajouté comme image brute du champ entier
		if (fits.preview && !form.images.some((i: any) => i.path.toLowerCase() === fits.preview.toLowerCase())) {
			form.images = [...form.images, {
				path: fits.preview, kind: 'brute', software: 'Seestar', palette: '', caption: 'Empilement du Seestar',
				isFavorite: !form.images.some((i: any) => i.isFavorite), targetIds: [], favoriteTargetIds: []
			}];
			filled.push('aperçu du Seestar dans les images');
		}
		fitsMessage = { filled, warnings };
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
						<button onclick={fillFromFits} class="btn-secondary text-xs" title="Remplir le rapport à partir du FITS empilé du Seestar">Depuis un FITS…</button>
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
				{#if appState.isEditingObservation && fitsMessage}
					<!-- Ce que le FITS a rempli, et ce qui reste à faire -->
					<div class="mb-4 rounded-lg border border-indigo-500/50 bg-indigo-500/10 px-4 py-2.5 text-xs flex items-start gap-3">
						<div class="flex-1">
							<span class="font-bold text-white">Rempli depuis le FITS :</span>
							<span class="text-surface-200">{fitsMessage.filled.join(' · ')}.</span>
							{#each fitsMessage.warnings as warning (warning)}
								<span class="block text-yellow-500 mt-1">⚠ {warning}</span>
							{/each}
							<span class="block text-surface-400 mt-1">Vérifiez, puis enregistrez. Les poses retenues (bon, pass, bad) restent à saisir.</span>
						</div>
						<button type="button" onclick={() => (fitsMessage = null)} class="text-surface-400 hover:text-white">✕</button>
					</div>
				{/if}
				<div class="grid grid-cols-1 xl:grid-cols-12 gap-8 flex-1">

					<div class="xl:col-span-8 flex flex-col gap-6 @container">
						<!-- Trois cadres côte à côte quand la place le permet ; sinon la session en haut, matériel et poses dessous -->
						<div class="grid grid-cols-1 @xl:grid-cols-2 @5xl:grid-cols-[minmax(25.5rem,1.3fr)_minmax(0,0.9fr)_minmax(0,1.1fr)] gap-4 shrink-0">

							<!-- SESSION -->
							<div class="space-y-4 bg-[#1e1e21] p-4 rounded-lg border border-[#333] @xl:col-span-2 @5xl:col-span-1">
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
													<option value={NEW_LOCATION} class="create-option">+ Nouveau lieu…</option>
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
								<div class="grid grid-cols-2 @5xl:grid-cols-1 gap-x-3 gap-y-3">
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

							<!-- POSES : tout l'empilement est trié une fois pour le champ, commun à ses cibles -->
							<div class="bg-[#1e1e21] p-4 rounded-lg border border-[#333]">
								<span class="text-[10px] uppercase font-bold text-surface-400 block border-b border-[#333] pb-1.5 mb-4">3. Poses</span>
								<div class="grid grid-cols-2 gap-x-3 gap-y-4">
									<div>
										<label for="obs-imgTotal" class="block text-[10px] text-surface-400 mb-1">Total des poses</label>
										{#if appState.isEditingObservation}
											<input id="obs-imgTotal" type="number" min="0" class="form-input" value={fieldValue('imgTotal')} oninput={(e) => setField('imgTotal')(Number(e.currentTarget.value))} />
										{:else}
											<span id="obs-imgTotal" class="block text-sm text-white">{fieldValue('imgTotal') ?? 0}</span>
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
								<div class="grid grid-cols-3 gap-2 mt-4">
									{#each POSE_FIELDS as f (f.key)}
										<div>
											<label for="obs-{f.key}" class="block text-[10px] mb-1 {f.color}">{f.label}</label>
											{#if appState.isEditingObservation}
												<input id="obs-{f.key}" type="number" min="0" class="form-input px-1 no-spin" value={fieldValue(f.key)} oninput={(e) => setField(f.key)(Number(e.currentTarget.value))} />
											{:else}
												<span id="obs-{f.key}" class="block text-sm font-bold {f.color}">{fieldValue(f.key) ?? 0}</span>
											{/if}
										</div>
									{/each}
								</div>
								<div class="border-t border-[#333] pt-3 mt-4 flex items-center gap-4">
									<!-- Anneau : un cercle de rayon 15.9155 mesure 100 de tour, les parts s'y posent en % -->
									<div class="w-20 h-20 shrink-0 relative" title="Part des poses bonnes">
										<svg viewBox="0 0 44 44" class="w-full h-full -rotate-90">
											<circle cx="22" cy="22" r="15.9155" fill="transparent" class="stroke-[#2a2a2e]" stroke-width="10" />
											{#each poseSlices as slice (slice.key)}
												<circle cx="22" cy="22" r="15.9155" fill="transparent" class="ring-slice {slice.stroke}" stroke-width="10"
													stroke-dasharray="{slice.dash} 100" stroke-dashoffset={-slice.offset} />
											{/each}
										</svg>
										<span class="absolute inset-0 flex items-center justify-center text-[11px] font-bold {poseSum ? 'text-green-400' : 'text-surface-500'}">
											{poseSum ? `${Math.round(((Number(fieldValue('imgGood')) || 0) / poseSum) * 100)} %` : '?'}
										</span>
									</div>
									<div class="grid grid-cols-[auto_auto] justify-start items-baseline gap-x-3 gap-y-1 min-w-0">
										<span class="text-[10px] text-surface-400 whitespace-nowrap">Durée totale</span>
										<span class="text-sm font-black text-white whitespace-nowrap text-right">{totalDuration.toFixed(1)} min</span>
										<span class="text-[10px] text-surface-400 whitespace-nowrap" title="Poses bonnes × pose individuelle">Durée retenue</span>
										<span class="text-sm font-black text-green-400 whitespace-nowrap text-right">{keptDuration ? `${keptDuration.toFixed(1)} min` : '—'}</span>
									</div>
								</div>
							</div>
						</div>

						{#if showConflict}
							<div class="-mt-2 px-3 py-2 rounded border border-amber-500/40 bg-amber-500/10 text-xs text-amber-200 flex items-start gap-3">
								<p class="flex-1">
									Avant la reprise, chaque cible avait ses propres comptes (bon / pass / bad) :
									{poseConflict.map(c => `${appState.targetName(c.targetId)} ${c.imgGood} / ${c.imgPass} / ${c.imgBad}`).join(' ; ')}.
									Ceux de la première cible ont été gardés : corrigez-les si besoin.
								</p>
								<button type="button" onclick={() => appState.setCheckDismissed(conflictKey, true)} class="btn-secondary text-[10px] shrink-0">C'est réglé</button>
							</div>
						{/if}

						<!-- CIBLES DU CHAMP -->
						<div class="bg-[#1e1e21] p-4 rounded-lg border border-[#333] shrink-0">
							<span class="text-[10px] uppercase font-bold text-surface-400 block border-b border-[#333] pb-1.5 mb-2">Cibles du champ</span>
							<div class="grid grid-cols-[minmax(0,1.6fr)_minmax(0,0.7fr)_auto] gap-x-2 gap-y-1 items-center">
								<span class="text-[10px] text-surface-400">Cible</span>
								<span class="text-[10px] text-surface-400">Hauteur (°)</span>
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
												<option value={NEW_TARGET} class="create-option">+ Nouvelle cible…</option>
											</select>
											{#if target}
												<button type="button" title="Voir la fiche de la cible" onclick={() => appState.openTargetSheet(target.id)} class="btn-secondary px-2 flex items-center">
													<svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 10.5v6" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/><circle cx="12" cy="7.3" r="1.3" fill="currentColor"/></svg>
												</button>
											{/if}
											</div>
										</div>
										{@const calc = computedAltitude(target)}
										<div class="flex gap-1 min-w-0">
											<input type="text" class="form-input min-w-0" bind:value={row.altitude} placeholder={calc ? `calc. ${calc.middle}` : ''} />
											{#if calc}
												<button
													type="button"
													title="Reprendre la hauteur calculée au milieu du créneau ({calc.middle}°, maximum {calc.max}°)"
													onclick={() => (row.altitude = String(calc.middle))}
													class="btn-secondary text-[10px] px-1.5"
												>auto</button>
											{/if}
										</div>
										<button type="button" title="Retirer cette cible" onclick={() => removeTarget(i)} class="text-red-400 hover:text-red-300 px-1">✕</button>
										<!-- Rappel de la cible sur sa propre ligne : la ligne des champs reste alignée -->
										{#if target}
											<span class="col-span-3 -mt-0.5 text-[10px] text-surface-500 truncate">{targetSummary(target)}</span>
										{/if}
										<input
											type="text"
											class="form-input col-span-2 mb-2"
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
										{@const calc = computedAltitude(target)}
										<div>
											<span class="text-sm text-white">{row.altitude || '—'}</span>
											{#if calc}
												<span class="block text-[10px] text-surface-500" title="Calculée : au milieu du créneau · au plus haut">calc. {calc.middle}° · max {calc.max}°</span>
											{/if}
										</div>
										<button
											type="button"
											title="Afficher les images de cette cible"
											onclick={() => (filterTargetId = filterTargetId === row.targetId ? null : row.targetId)}
											class="text-xs px-2 py-0.5 rounded-full border transition-colors {filterTargetId === row.targetId ? 'bg-indigo-500 border-indigo-500 text-white font-bold' : 'border-[#333] text-surface-300 hover:border-indigo-500'}"
										>🖼 {imageCount(row.targetId)}</button>
										{#if row.notes}
											<p class="col-span-3 text-xs text-surface-300 whitespace-pre-wrap -mt-0.5 mb-1.5">Note : {row.notes}</p>
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
						<WeatherReadings {obs} />
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
	/* Entrée « + Nouveau… » des listes : en bleu, pour la distinguer des choix */
	.create-option {
		color: #818cf8;
		font-weight: 700;
	}
	/* Bon / pass / bad : sans flèches, le nombre garde toute la largeur du champ */
	.no-spin {
		-moz-appearance: textfield;
		appearance: textfield;
	}
	.no-spin::-webkit-inner-spin-button,
	.no-spin::-webkit-outer-spin-button {
		-webkit-appearance: none;
		margin: 0;
	}
	/* L'anneau suit la saisie : chaque part glisse vers sa nouvelle taille */
	.ring-slice {
		transition: stroke-dasharray 0.6s cubic-bezier(0.4, 0, 0.2, 1), stroke-dashoffset 0.6s cubic-bezier(0.4, 0, 0.2, 1);
	}
	.session-date {
		width: 11.5rem;
		flex-shrink: 0;
	}
</style>
