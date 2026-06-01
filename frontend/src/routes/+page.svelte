<script lang="ts">
	import { slide, fade } from 'svelte/transition'; // [3]

	// ================= 1. DONNÉES DE TEST EN MÉMOIRE =================
	let targets = $state([
		{ 
			id: 1, 
			name: 'M42', 
			usualName: "Nébuleuse d'Orion", 
			constellation: 'Ori',
			otherDesignations: 'NGC 1976',
			type: 'Nébuleuse en émission',
			group: 'Nuage d\'Orion',
			magnitude: '4.0',
			colorIndex: '0.0',
			surfBrightness: '11.0',
			size: '85\' x 60\'',
			ra: '05h 35m 17s',
			dec: '-05° 23\' 28"',
			imageRef: 'https://images.unsplash.com/photo-1543722530-d2c3201371e7?auto=format&fit=crop&w=400&q=80', // Photo de référence
			skyMap: 'https://images.unsplash.com/photo-1506318137071-a8e063b4bec0?auto=format&fit=crop&w=400&q=80' // Carte du ciel
		},
		{ 
			id: 2, 
			name: 'M31', 
			usualName: "Galaxie d'Andromède", 
			constellation: 'And',
			otherDesignations: 'NGC 224',
			type: 'Galaxie spirale',
			group: 'Groupe Local',
			magnitude: '3.4',
			colorIndex: '0.6',
			surfBrightness: '13.5',
			size: '190\' x 60\'',
			ra: '00h 42m 44s',
			dec: '+41° 16\' 09"',
			imageRef: 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=400&q=80',
			skyMap: ''
		}
	]);

	let observations = $state([
		{
			id: 101,
			targetId: 1,
			date: '2026-02-15',
			obsStart: '21:30',
			obsEnd: '23:15',
			location: 'Jardin - Béthune',
			altitude: '45',
			sensor: 'Seestar S50 (IMX462)',
			filter: 'IRCUT',
			sensorTemp: '12.5',
			subExposure: '10',
			imgTotal: 150,
			imgGood: 120,
			imgPass: 10,
			imgBad: 20,
			otherObjects: 'M43, Running Man Nebula (NGC 1977) à proximité immédiate.',
			imageRaw: 'https://images.unsplash.com/photo-1543722530-d2c3201371e7?auto=format&fit=crop&w=500&q=80',
			imageProcessed: ''
		}
	]);

	// ================= 2. ÉTATS DE L'UI =================
	let searchQuery = $state('');
	let selectedTargetId = $state<number | null>(1);
	let isEditingTarget = $state(false); 
	let activeObservationId = $state<number | null>(null);
	let bottomView = $state<'list' | 'detail'>('list');

	// Clones d'édition
	let targetForm = $state({ ...targets[0] });

	// ================= 3. ÉTATS DÉRIVÉS =================
	let filteredTargets = $derived(
		targets.filter(t => 
			t.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
			t.usualName.toLowerCase().includes(searchQuery.toLowerCase()) ||
			t.constellation.toLowerCase().includes(searchQuery.toLowerCase())
		)
	);

	let activeTarget = $derived(
		targets.find(t => t.id === selectedTargetId) || null
	);

	let activeTargetObservations = $derived(
		observations.filter(o => o.targetId === selectedTargetId)
	);

	let activeObservation = $derived(
		observations.find(o => o.id === activeObservationId) || null
	);

	let calculatedLightImages = $derived(
		activeObservation ? activeObservation.imgGood + activeObservation.imgPass : 0
	);
	
	let calculatedDuration = $derived(
		activeObservation ? (activeObservation.imgGood * Number(activeObservation.subExposure)) / 60 : 0
	);

	// ================= 4. CRUD ACTIONS =================
	function selectTarget(id: number) {
		selectedTargetId = id;
		isEditingTarget = false;
		bottomView = 'list';
		activeObservationId = null;
		
		const target = targets.find(t => t.id === id);
		if (target) {
			targetForm = { ...target };
		}
	}

	function startEditTarget() {
		if (activeTarget) {
			targetForm = { ...activeTarget };
			isEditingTarget = true;
		}
	}

	function saveTarget() {
		const index = targets.findIndex(t => t.id === selectedTargetId);
		if (index !== -1) {
			targets[index] = { ...targetForm };
			isEditingTarget = false;
		}
	}

	function deleteTarget() {
		if (!selectedTargetId) return;
		const confirmDelete = confirm("Voulez-vous vraiment supprimer cet objet et TOUTES ses observations liées ?");
		if (confirmDelete) {
			observations = observations.filter(o => o.targetId !== selectedTargetId);
			targets = targets.filter(t => t.id !== selectedTargetId);
			if (targets.length > 0) {
				selectTarget(targets[0].id);
			} else {
				selectedTargetId = null;
			}
		}
	}

	function createNewTarget() {
		const newId = Date.now();
		const newTarget = {
			id: newId,
			name: 'Nouvel Objet',
			usualName: '',
			constellation: 'Ori',
			otherDesignations: '',
			type: '',
			group: '',
			magnitude: '',
			colorIndex: '',
			surfBrightness: '',
			size: '',
			ra: '',
			dec: '',
			imageRef: '',
			skyMap: ''
		};
		targets.push(newTarget);
		selectTarget(newId);
		startEditTarget();
	}

	function openObservation(id: number) {
		activeObservationId = id;
		bottomView = 'detail';
	}

	function createNewObservation() {
		if (!selectedTargetId) return;
		const newId = Date.now();
		const newObs = {
			id: newId,
			targetId: selectedTargetId,
			date: new Date().toISOString().split('T')[0],
			obsStart: '',
			obsEnd: '',
			location: 'Jardin',
			altitude: '',
			sensor: 'Seestar S50 (IMX462)',
			filter: 'IRCUT',
			sensorTemp: '',
			subExposure: '10',
			imgTotal: 0,
			imgGood: 0,
			imgPass: 0,
			imgBad: 0,
			otherObjects: '',
			imageRaw: '',
			imageProcessed: ''
		};
		observations.push(newObs);
		openObservation(newId);
	}

	function deleteObservation() {
		if (!activeObservationId) return;
		const confirmDelete = confirm("Supprimer ce rapport d'observation ?");
		if (confirmDelete) {
			observations = observations.filter(o => o.id !== activeObservationId);
			bottomView = 'list';
			activeObservationId = null;
		}
	}

	// État pour afficher ou non la grande carte céleste
	let showMapModal = $state(false);

	// Action Svelte pour démarrer l'atlas interactif Aladin Lite v3
	function initAladin(node: HTMLElement) {
		const A = (window as any).A; // Récupère l'API globale d'Aladin
		if (!A) return;

		A.init.then(() => {
			// Initialise l'atlas dans notre div Svelte
			A.aladin(node, {
				survey: 'P/DSS2/color', // Image couleur du ciel profond (Digitized Sky Survey)
				target: activeTarget ? `${activeTarget.name}` : 'M42', // Centre sur le nom de l'objet
				fov: 1.5, // Champ de vision initial en degrés
				showFullscreenControl: false, // On gère le plein écran nous-mêmes
				showLayersControl: true // Permet à l'utilisateur de changer de filtre/longueur d'onde !
			});
		});
	}
</script>

<div class="flex h-full w-full bg-[#121214] overflow-hidden">
	
	<!-- ================= SIDEBAR (GAUCHE) : LISTE DES CIBLES ================= -->
	<aside class="w-80 border-r border-[#2a2a2d] flex flex-col bg-[#161619] h-full shrink-0">
		<div class="p-4 border-b border-[#2a2a2d] flex space-x-2">
			<input 
				type="text" 
				placeholder="Rechercher un objet..." 
				class="bg-[#202024] border border-[#333] rounded px-3 py-1.5 text-sm flex-1 text-white focus:outline-none focus:border-primary-500"
				bind:value={searchQuery}
			/>
			<button 
				onclick={createNewTarget}
				class="bg-surface-700 hover:bg-surface-600 border border-[#444] text-white px-3.5 py-1.5 rounded text-sm font-bold transition-colors"
				title="Ajouter un objet céleste"
			>
				+
			</button>
		</div>

		<div class="flex-1 overflow-y-auto">
			{#if filteredTargets.length === 0}
				<div class="p-8 text-center text-sm text-surface-400 opacity-50">Aucun objet</div>
			{:else}
				<div class="divide-y divide-[#2a2a2d]/50">
					{#each filteredTargets as target}
						<button 
							onclick={() => selectTarget(target.id)}
							class="w-full text-left p-4 hover:bg-[#202024] transition-colors flex flex-col relative"
							class:active-item={selectedTargetId === target.id}
						>
							<div class="flex justify-between items-baseline mb-1">
								<span class="font-bold text-white text-base">{target.name}</span>
								<span class="text-xs text-surface-400 uppercase tracking-widest">{target.constellation}</span>
							</div>
							<div class="text-xs text-surface-400 truncate">{target.usualName || 'Pas de nom usuel'}</div>
						</button>
					{/each}
				</div>
			{/if}
		</div>
	</aside>

	<!-- ================= ZONE PRINCIPALE (HAUT FIXE / BAS GLISSANT INDÉPENDANT) ================= -->
	<!-- Remarque : "flex flex-col h-full overflow-hidden" fige la zone de droite [3] -->
	<main class="flex-1 h-full flex flex-col bg-[#121214] p-8 space-y-6 overflow-hidden">
		{#if activeTarget}
			
			<!-- ================= A. CARTE D'IDENTITÉ DE L'OBJET (STATIQUE / SHRINK-0) ================= -->
			<!-- "shrink-0" empêche cette carte du haut de se faire écraser ou de scroller [3] -->
			<!-- ================= A. CARTE D'IDENTITÉ DE L'OBJET (STATIQUE / SHRINK-0) ================= -->
			<section class="bg-[#1a1a1d] p-6 rounded-lg border border-[#333] shadow-xl shrink-0">
				<div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
					
					<!-- Caractéristiques textuelles (75% de la largeur désormais) -->
					<div class="lg:col-span-9 space-y-4">
						<div class="flex justify-between items-center border-b border-[#333] pb-3">
							<div class="flex items-baseline space-x-4">
								{#if isEditingTarget}
									<input type="text" class="form-input text-xl font-bold text-white w-40" bind:value={targetForm.name} />
									<input type="text" class="form-input text-sm text-surface-400 w-60" bind:value={targetForm.usualName} placeholder="Nom usuel" />
								{:else}
									<h1 class="text-2xl font-black text-white">{activeTarget.name}</h1>
									<span class="text-sm text-surface-400 font-semibold">{activeTarget.usualName}</span>
								{/if}
							</div>
							
							<div class="flex space-x-2">
								{#if isEditingTarget}
									<button onclick={saveTarget} class="btn-primary">Enregistrer</button>
									<button onclick={() => isEditingTarget = false} class="btn-secondary">Annuler</button>
									<button onclick={deleteTarget} class="btn-danger">Supprimer</button>
								{:else}
									<button onclick={startEditTarget} class="btn-secondary text-xs">Modifier la cible</button>
								{/if}
							</div>
						</div>

						<div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
							<div>
								<span class="text-surface-400 block mb-1">Constellation</span>
								<input type="text" class="form-input" disabled={!isEditingTarget} bind:value={targetForm.constellation} />
							</div>
							<div>
								<span class="text-surface-400 block mb-1">Désignations</span>
								<input type="text" class="form-input" disabled={!isEditingTarget} bind:value={targetForm.otherDesignations} />
							</div>
							<div>
								<span class="text-surface-400 block mb-1">Type d'objet</span>
								<input type="text" class="form-input" disabled={!isEditingTarget} bind:value={targetForm.type} />
							</div>
							<div>
								<span class="text-surface-400 block mb-1">Magnitude (Mag)</span>
								<input type="text" class="form-input" disabled={!isEditingTarget} bind:value={targetForm.magnitude} />
							</div>
							<div>
								<span class="text-surface-400 block mb-1">Brillance surf.</span>
								<input type="text" class="form-input" disabled={!isEditingTarget} bind:value={targetForm.surfBrightness} />
							</div>
							<div>
								<span class="text-surface-400 block mb-1">Taille</span>
								<input type="text" class="form-input" disabled={!isEditingTarget} bind:value={targetForm.size} />
							</div>
							<div>
								<span class="text-surface-400 block mb-1">Coordonnées AD (ra)</span>
								<input type="text" class="form-input" disabled={!isEditingTarget} bind:value={targetForm.ra} />
							</div>
							<div>
								<span class="text-surface-400 block mb-1">Coordonnées DEC (dec)</span>
								<input type="text" class="form-input" disabled={!isEditingTarget} bind:value={targetForm.dec} />
							</div>
						</div>
					</div>

					<!-- Image unique de l'objet (25% de la largeur) — LE NÉCESSAIRE + L'EXPÉRIENCE -->
					<div class="lg:col-span-3 relative h-44 lg:h-auto">
						{#if isEditingTarget}
							<!-- En mode Édition : Uniquement le champ pour l'image de référence -->
							<div class="lg:absolute lg:inset-0 h-full lg:h-auto border border-[#333] p-2.5 rounded bg-[#1e1e21] flex flex-col w-full">
								<span class="text-[10px] uppercase font-bold text-surface-400 mb-1.5 block">Image de référence</span>
								<div class="flex-1 border border-dashed border-[#444] rounded flex items-center justify-center overflow-hidden">
									<input type="text" class="form-input text-[10px] m-1" bind:value={targetForm.imageRef} placeholder="Lien de l'image (URL)" />
								</div>
							</div>
						{:else}
							<!-- En mode Visualisation : L'image cliquable pour ouvrir l'atlas -->
							<button 
								onclick={() => showMapModal = true}
								class="lg:absolute lg:inset-0 h-full lg:h-auto border border-[#333] p-2.5 rounded bg-[#1e1e21] flex flex-col w-full text-left group hover:border-indigo-500 transition-colors cursor-pointer"
								title="Cliquez pour explorer la carte céleste"
							>
								<span class="text-[10px] uppercase font-bold text-surface-400 mb-1.5 block">Image de référence</span>
								<div class="flex-1 rounded flex items-center justify-center overflow-hidden relative bg-black/30">
									{#if activeTarget.imageRef}
										<img src={activeTarget.imageRef} alt="Illustration" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
										<!-- Effet au survol style Windows/WinUI -->
										<div class="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 flex flex-col justify-center items-center transition-opacity">
											<span class="text-xl mb-1">🌌</span>
											<span class="text-[9px] text-white font-bold tracking-wider uppercase">Explorer la carte céleste</span>
										</div>
									{:else}
										<div class="text-center p-2 flex flex-col items-center">
											<svg class="w-6 h-6 text-[#444] group-hover:text-indigo-400 transition-colors mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
											<span class="text-[10px] text-[#777] group-hover:text-indigo-300 transition-colors font-bold">Aucune image</span>
											<span class="text-[8px] text-[#555]">Cliquez pour explorer la carte</span>
										</div>
									{/if}
								</div>
							</button>
						{/if}
					</div>

				</div>
			</section>

			<!-- ================= B. ZONE BASSE HYBRIDE (DÉFILEMENT INDÉPENDANT / FLEX-1 MIN-H-0 OVERFLOW-Y-AUTO) ================= -->
			<!-- C'est ici que l'expérience de défilement ciblé prend vie [3] -->
			<div class="flex-1 min-h-0 bg-[#161619] border border-[#2a2a2d] rounded-xl p-6 shadow-2xl flex flex-col overflow-hidden">
				
				<!-- CAS 1 : TABLEAU DE L'HISTORIQUE -->
				{#if bottomView === 'list'}
					<div in:fade={{ duration: 150 }} out:slide={{ duration: 150 }} class="flex flex-col h-full space-y-6">
						<div class="flex justify-between items-center shrink-0">
							<h2 class="text-sm font-bold uppercase tracking-widest text-surface-400">Historique des Observations ({activeTargetObservations.length})</h2>
							<button onclick={createNewObservation} class="btn-primary text-xs">+ Nouvelle observation</button>
						</div>

						{#if activeTargetObservations.length === 0}
							<div class="text-center py-16 text-surface-400/50">
								<p class="text-3xl mb-2">🔭</p>
								<p class="text-sm">Aucun rapport pour cet objet céleste.</p>
							</div>
						{:else}
							<div class="flex-1 min-h-0 overflow-auto pr-1">
								<table class="w-full text-left border-collapse text-sm">
									<thead>
										<tr class="border-b border-[#333] text-surface-400 text-xs uppercase tracking-wider">
											<th class="py-3 px-4">Date</th>
											<th class="py-3 px-4">Localisation</th>
											<th class="py-3 px-4">Durée de pose</th>
											<th class="py-3 px-4">Notes rapides</th>
											<th class="py-3 px-4 text-right">Action</th>
										</tr>
									</thead>
									<tbody class="divide-y divide-[#2a2a2d]">
										{#each activeTargetObservations as obs}
											<tr class="hover:bg-[#202024]/50 transition-colors cursor-pointer" onclick={() => openObservation(obs.id)}>
												<td class="py-3.5 px-4 font-bold text-white">📅 {obs.date}</td>
												<td class="py-3.5 px-4 text-surface-400">{obs.location || 'Non spécifiée'}</td>
												<td class="py-3.5 px-4 text-surface-400">
													{((obs.imgGood * Number(obs.subExposure)) / 60).toFixed(1)} minutes
												</td>
												<td class="py-3.5 px-4 text-surface-400 truncate max-w-xs">{obs.otherObjects || 'Aucune note'}</td>
												<td class="py-3.5 px-4 text-right">
													<span class="text-xs text-indigo-400 font-bold hover:underline">Ouvrir la fiche →</span>
												</td>
											</tr>
										{/each}
									</tbody>
								</table>
							</div>
						{/if}
					</div>
				
				<!-- CAS 2 : FORMULAIRE DÉTAILLÉ -->
				{:else if bottomView === 'detail' && activeObservation}
					<div in:slide={{ duration: 150 }} out:fade={{ duration: 150 }} class="flex flex-col h-full space-y-6">
						
						<!-- Header d'édition -->
						<div class="flex justify-between items-center border-b border-[#333] pb-4 shrink-0">
							<div class="flex items-center space-x-3">
								<button onclick={() => bottomView = 'list'} class="btn-secondary text-xs">← Retour à l'historique</button>
								<h2 class="text-sm font-bold uppercase tracking-widest text-surface-100">Rapport du {activeObservation.date}</h2>
							</div>
							<div class="flex space-x-2">
								<button onclick={() => bottomView = 'list'} class="btn-primary text-xs">Sauvegarder</button>
								<button onclick={deleteObservation} class="btn-danger text-xs">Supprimer ce rapport</button>
							</div>
						</div>

						<div class="flex-1 min-h-0 overflow-y-auto pr-2 grid grid-cols-1 xl:grid-cols-12 gap-8">
							
							<!-- Formulaire de saisie (65% de l'écran) -->
							<div class="xl:col-span-8 space-y-6">
								
								<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
									
									<!-- COLONNE 1 : SESSION GÉNÉRALE -->
									<div class="space-y-4 bg-[#1e1e21] p-4 rounded-lg border border-[#333]">
										<span class="text-[10px] uppercase font-bold text-surface-400 block border-b border-[#333] pb-1.5">1. Session</span>
										<div>
											<label class="block text-[10px] text-surface-400 mb-1">Date
												<input type="date" class="form-input" bind:value={activeObservation.date} />
											</label>
										</div>
										<div class="grid grid-cols-2 gap-2">
											<div>
												<label class="block text-[10px] text-surface-400 mb-1">Début
													<input type="time" class="form-input" bind:value={activeObservation.obsStart} />
												</label>
											</div>
											<div>
												<label class="block text-[10px] text-surface-400 mb-1">Fin
													<input type="time" class="form-input" bind:value={activeObservation.obsEnd} />
												</label>
											</div>
										</div>
										<div>
											<label class="block text-[10px] text-surface-400 mb-1">Localisation
												<input type="text" class="form-input" bind:value={activeObservation.location} placeholder="ex: Jardin" />
											</label>
										</div>
										<div>
											<label class="block text-[10px] text-surface-400 mb-1">Hauteur de cible (°)
												<input type="text" class="form-input" bind:value={activeObservation.altitude} placeholder="ex: 45" />
											</label>
										</div>
									</div>

									<!-- COLONNE 2 : HARDWARE & CAPTURE -->
									<div class="space-y-4 bg-[#1e1e21] p-4 rounded-lg border border-[#333]">
										<span class="text-[10px] uppercase font-bold text-surface-400 block border-b border-[#333] pb-1.5">2. Matériel & Pose</span>
										<div>
											<label class="block text-[10px] text-surface-400 mb-1">Capteur
												<input type="text" class="form-input" bind:value={activeObservation.sensor} />
											</label>
										</div>
										<div>
											<label class="block text-[10px] text-surface-400 mb-1">Filtre
												<input type="text" class="form-input" bind:value={activeObservation.filter} placeholder="ex: LP, IRCUT" />
											</label>
										</div>
										<div>
											<label class="block text-[10px] text-surface-400 mb-1">Temp. Capteur (°C)
												<input type="text" class="form-input" bind:value={activeObservation.sensorTemp} placeholder="ex: 15.4" />
											</label>
										</div>
										<div>
											<label class="block text-[10px] text-surface-400 mb-1">Temps de pose indiv. (s)
												<input type="text" class="form-input" bind:value={activeObservation.subExposure} placeholder="ex: 10 ou 20" />
											</label>
										</div>
									</div>

									<!-- COLONNE 3 : STATISTIQUES IMAGES -->
									<div class="space-y-4 bg-[#1e1e21] p-4 rounded-lg border border-[#333]">
										<span class="text-[10px] uppercase font-bold text-surface-400 block border-b border-[#333] pb-1.5">3. Images</span>
										<div class="grid grid-cols-2 gap-2">
											<div>
												<label class="block text-[10px] text-surface-400 mb-1">Total
													<input type="number" class="form-input" bind:value={activeObservation.imgTotal} />
												</label>
											</div>
											<div>
												<label class="block text-[10px] text-indigo-400 mb-1 font-bold">Lights
													<input type="text" class="form-input text-indigo-400 font-bold bg-[#1a1a1d]" disabled value={calculatedLightImages} />
												</label>
											</div>
										</div>
										<div class="grid grid-cols-3 gap-1 text-[9px]">
											<div>
												<label class="block text-[9px] text-green-400 mb-1">Bon
													<input type="number" class="form-input px-1" bind:value={activeObservation.imgGood} />
												</label>
											</div>
											<div>
												<label class="block text-[9px] text-yellow-500 mb-1">Pass
													<input type="number" class="form-input px-1" bind:value={activeObservation.imgPass} />
												</label>
											</div>
											<div>
												<label class="block text-[9px] text-red-500 mb-1">Bad
													<input type="number" class="form-input px-1" bind:value={activeObservation.imgBad} />
												</label>
											</div>
										</div>
										<div class="border-t border-[#333] pt-2">
											<span class="text-[10px] text-surface-400 block mb-1">Durée totale :</span>
											<span class="text-sm font-black text-white">{calculatedDuration.toFixed(1)} min</span>
										</div>
									</div>

								</div>

								<!-- AUTRES OBGETS DANS LE CHAMP -->
								<div class="col-span-3">
									<label class="block text-xs text-surface-400 mb-1">Autres objets dans le champ / Notes
										<textarea 
											class="form-input h-24 resize-none py-2" 
											bind:value={activeObservation.otherObjects}
											placeholder="Notes..."
										></textarea>
									</label>
								</div>

							</div>

							<!-- Les images Seestar (35% de l'écran) -->
							<div class="xl:col-span-4 space-y-4">
								
								<div class="border border-[#333] p-3 rounded bg-[#1a1a1d] flex flex-col h-60">
									<span class="text-[10px] uppercase font-bold text-surface-400 mb-2">Image Brute (Seestar)</span>
									<div class="flex-1 border border-dashed border-[#444] rounded flex flex-col items-center justify-center overflow-hidden relative group">
										{#if activeObservation.imageRaw}
											<img src={activeObservation.imageRaw} alt="Brute" class="w-full h-full object-cover" />
										{:else}
											<span class="text-[10px] text-[#555] font-bold">Lier JPEG Seestar</span>
										{/if}
									</div>
								</div>

								<div class="border border-[#333] p-3 rounded bg-[#1a1a1d] flex flex-col h-60">
									<span class="text-[10px] uppercase font-bold text-surface-400 mb-2">Image finale traitée</span>
									<div class="flex-1 border border-dashed border-[#444] rounded flex flex-col items-center justify-center overflow-hidden relative group">
										{#if activeObservation.imageProcessed}
											<img src={activeObservation.imageProcessed} alt="Traitée" class="w-full h-full object-cover" />
										{:else}
											<span class="text-[10px] text-[#555] font-bold">Lier image finale</span>
										{/if}
									</div>
								</div>

							</div>

						</div>

					</div>
				{/if}

			</div>
		{:else}
			<div class="h-full w-full flex flex-col justify-center items-center p-8 opacity-40">
				<span class="text-6xl mb-4">🌌</span>
				<p class="text-sm">Sélectionnez ou créez un objet céleste pour commencer à rédiger</p>
			</div>
		{/if}
	</main>

</div>

<!-- ================= MODALE : CARTE CÉLESTE INTERACTIVE (OVERLAY) ================= -->
{#if showMapModal && activeTarget}
	<!-- Fond semi-transparent avec flou d'arrière-plan style WinUI -->
	<div 
		transition:fade={{ duration: 150 }}
		class="fixed inset-0 bg-black/85 backdrop-blur-md z-50 flex items-center justify-center p-8"
	>
		<!-- Fenêtre de la carte -->
		<div 
			transition:slide={{ duration: 200 }}
			class="bg-[#161619] border border-[#333] rounded-2xl w-[90vw] h-[85vh] flex flex-col overflow-hidden shadow-2xl"
		>
			<!-- Barre d'outils supérieure de la carte -->
			<div class="h-14 border-b border-[#333] bg-[#1a1a1d] px-6 flex items-center justify-between shrink-0 select-none">
				<div class="flex items-center space-x-3">
					<span class="text-xl">🌌</span>
					<h2 class="text-sm font-bold uppercase tracking-widest text-white">
						Carte Céleste Interactive — {activeTarget.name} ({activeTarget.usualName || 'Identité inconnue'})
					</h2>
				</div>
				<button 
					onclick={() => showMapModal = false}
					class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-surface-800 text-surface-400 hover:text-white transition-colors text-lg"
					title="Fermer la carte"
				>
					✕
				</button>
			</div>

			<!-- L'Atlas Aladin Lite v3 (WebGL2) -->
			<!-- use:initAladin appelle notre fonction d'initialisation dès que la div apparaît -->
			<div 
				use:initAladin 
				class="flex-1 w-full bg-black"
			></div>
		</div>
	</div>
{/if}

<style>
	/* Styles globaux pour notre formulaire */
	.form-input {
		width: 100%;
		background-color: #202024;
		border: 1px solid #333;
		border-radius: 4px;
		padding: 6px 10px;
		font-size: 0.82rem;
		color: #e2e8f0;
		transition: border-color 0.15s;
	}

	.form-input:focus {
		outline: none;
		border-color: #6366f1;
	}

	.form-input:disabled {
		background-color: transparent;
		border-color: transparent;
		padding-left: 0;
		color: #fff;
		cursor: default;
	}

	/* Boutons */
	.btn-primary {
		background-color: #6366f1;
		color: white;
		border: none;
		padding: 6px 12px;
		font-size: 0.75rem;
		font-weight: bold;
		border-radius: 4px;
		cursor: pointer;
		transition: background 0.15s;
	}
	.btn-primary:hover { background-color: #4f46e5; }

	.btn-secondary {
		background-color: #202024;
		color: #e2e8f0;
		border: 1px solid #444;
		padding: 6px 12px;
		font-size: 0.75rem;
		font-weight: bold;
		border-radius: 4px;
		cursor: pointer;
		transition: background 0.15s;
	}
	.btn-secondary:hover { background-color: #2a2a2d; }

	.btn-danger {
		background-color: #e81123;
		color: white;
		border: none;
		padding: 6px 12px;
		font-size: 0.75rem;
		font-weight: bold;
		border-radius: 4px;
		cursor: pointer;
	}
	.btn-danger:hover { background-color: #b10a17; }

	/* Sélection active barre latérale */
	.active-item {
		background-color: #202024;
		border-left: 3px solid #6366f1;
	}
</style>