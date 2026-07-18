// src/lib/state.svelte.ts
import { getCurrentWindow } from '@tauri-apps/api/window';
import { slide, fade } from 'svelte/transition';

const API_URL = "http://127.0.0.1:8000/api";

class AppState {
	// --- TABLES DE DONNÉES RÉACTIVES ---
	targets = $state<any[]>([]);
	observations = $state<any[]>([]);

	// --- ÉTATS DE L'INTERFACE ---
	searchQuery = $state('');
	selectedTargetId = $state<number | null>(null);
	isEditingTarget = $state(false); 
	activeObservationId = $state<number | null>(null);
	isEditingObservation = $state(false);
	showMapModal = $state(false);

	// Clone de modification pour la cible active
	targetForm = $state<any>({ name: '' });
	// Clone de modification pour l'observation active
	observationForm = $state<any>({});

	constructor() {
		// Charger les cibles célestes au démarrage de l'application
		this.loadTargets();
	}

	// --- ÉTATS DÉRIVÉS RÉACTIFS ---
	get filteredTargets() {
		return this.targets.filter(t => 
			t.name.toLowerCase().includes(this.searchQuery.toLowerCase()) || 
			(t.usualName && t.usualName.toLowerCase().includes(this.searchQuery.toLowerCase())) ||
			(t.constellation && t.constellation.toLowerCase().includes(this.searchQuery.toLowerCase()))
		);
	}

	get activeTarget() {
		return this.targets.find(t => t.id === this.selectedTargetId) || null;
	}

	get activeTargetObservations() {
		return this.observations.filter(o => o.targetId === this.selectedTargetId);
	}

	get activeObservation() {
		return this.observations.find(o => o.id === this.activeObservationId) || null;
	}

	get calculatedLightImages() {
		const source = this.isEditingObservation ? this.observationForm : this.activeObservation;
		if (!source) return 0;
		return (Number(source.imgGood) || 0) + (Number(source.imgPass) || 0);
	}
	
	get calculatedDuration() {
		const source = this.isEditingObservation ? this.observationForm : this.activeObservation;
		if (!source) return 0;
		return ((Number(source.imgGood) || 0) * Number(source.subExposure || 0)) / 60;
	}

	// --- APPELS API (COMMUNICATION AVEC LE PYTHON) ---

	async closeApp(){
		try {
			await fetch(`${API_URL}/shutdown`, { method: 'POST' });
		} catch (err) {
			console.log("Déconnexion attendue lors du shutdown.");
		}

		const appWindow = getCurrentWindow();
		await appWindow.close();
	}

	async loadTargets() {
		try {
			const res = await fetch(`${API_URL}/targets`);
			this.targets = await res.json();
			
			// Sélectionner automatiquement le premier élément s'il y en a un
			if (this.targets.length > 0 && this.selectedTargetId === null) {
				this.selectTarget(this.targets[0].id);
			}
		} catch (err) {
			console.error("Erreur chargement cibles depuis l'API:", err);
		}
	}

	async loadObservations(targetId: number) {
		try {
			const res = await fetch(`${API_URL}/targets/${targetId}/observations`);
			this.observations = await res.json();
		} catch (err) {
			console.error("Erreur chargement observations depuis l'API:", err);
		}
	}

	async selectTarget(id: number) {
		this.selectedTargetId = id;
		this.isEditingTarget = false;
		this.closeObservation();

		// Charger les observations réelles de cet objet depuis la base SQLite
		await this.loadObservations(id);
	}

	startEditTarget() {
		if (this.activeTarget) {
			this.targetForm = { ...this.activeTarget };
			this.isEditingTarget = true;
		}
	}

	async saveTarget() {
		try {
			// On clone l'objet pour ne pas modifier l'original en cours de route
			const targetToSave = { ...this.targetForm };
			const wasNewTarget = targetToSave.id && targetToSave.id > 1000000000;
			const tempId = targetToSave.id;

			// Si l'ID est un timestamp temporaire (> 1000000000), on le supprime.
			// SQLite comprendra qu'il s'agit d'une création et va auto-incrémenter l'ID.
			if (wasNewTarget) {
				delete targetToSave.id;
			}

			const res = await fetch(`${API_URL}/targets`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(targetToSave)
			});
			const savedTarget = await res.json();

			// On fusionne le résultat du serveur dans le tableau local, sans recharger
			// toute la base : on vient de faire la modif, on sait ce qu'il y a dedans.
			if (wasNewTarget) {
				// Remplace l'entrée temporaire (ID timestamp) par la vraie entrée SQLite
				const idx = this.targets.findIndex(t => t.id === tempId);
				if (idx !== -1) {
					this.targets[idx] = savedTarget;
				} else {
					this.targets.push(savedTarget);
				}
			} else {
				const idx = this.targets.findIndex(t => t.id === savedTarget.id);
				if (idx !== -1) {
					this.targets[idx] = savedTarget;
				}
			}

			this.selectedTargetId = savedTarget.id;
			this.isEditingTarget = false;
		} catch (err) {
			console.error("Erreur sauvegarde cible:", err);
		}
	}

	async deleteTarget() {
		if (!this.selectedTargetId) return;
		const confirmDelete = confirm("Supprimer définitivement cet objet céleste et toutes ses observations ?");
		if (confirmDelete) {
			try {
				await fetch(`${API_URL}/targets/${this.selectedTargetId}`, { method: 'DELETE' });
				this.selectedTargetId = null;
				await this.loadTargets();
			} catch (err) {
				console.error("Erreur suppression cible:", err);
			}
		}
	}

	createNewTarget() {
		const newId = Date.now(); // Génère un ID temporaire unique (ex: 1781234567890)
		const newTarget = {
			id: newId,
			name: 'Nouvelle Cible',
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
			imageRef: ''
		};
		
		// On l'ajoute temporairement en mémoire et on l'active
		this.targets.push(newTarget);
		this.selectTarget(newId);
		this.startEditTarget(); // Ouvre directement le formulaire d'édition
	}

	cancelEditTarget() {
		this.isEditingTarget = false;

		// Si on annule la création d'un TOUT NOUVEL objet (ID temporaire),
		// on le retire de la mémoire pour éviter les fantômes.
		if (this.selectedTargetId && this.selectedTargetId > 1000000000) {
			this.targets = this.targets.filter(t => t.id !== this.selectedTargetId);
			if (this.targets.length > 0) {
				this.selectTarget(this.targets[0].id);
			} else {
				this.selectedTargetId = null;
			}
		}
		// Sinon (simple modification) : rien à faire. targetForm n'est jamais lu
		// hors édition, donc l'original (target) redevient automatiquement
		// la source affichée — pas de resynchronisation manuelle nécessaire.
	}

	// La modal est ouverte dès qu'une observation est active
	get isObservationModalOpen() {
		return this.activeObservationId !== null;
	}

	openObservation(id: number) {
		this.activeObservationId = id;
		this.isEditingObservation = false;
	}

	closeObservation() {
		// Si on ferme sans sauvegarder la création d'une TOUTE NOUVELLE observation
		// (ID temporaire), on la retire de la mémoire pour éviter les fantômes —
		// même logique que pour les cibles.
		if (this.activeObservationId && this.activeObservationId > 1000000000) {
			this.observations = this.observations.filter(o => o.id !== this.activeObservationId);
		}
		this.activeObservationId = null;
		this.isEditingObservation = false;
	}

	startEditObservation() {
		if (this.activeObservation) {
			this.observationForm = { ...this.activeObservation };
			this.isEditingObservation = true;
		}
	}

	cancelEditObservation() {
		this.isEditingObservation = false;

		// Si on annule la création d'une TOUTE NOUVELLE observation (ID temporaire),
		// on ferme carrément la modal — il n'y a rien à montrer en lecture.
		if (this.activeObservationId && this.activeObservationId > 1000000000) {
			this.closeObservation();
		}
		// Sinon (simple modification) : rien à faire de plus, observationForm n'est
		// jamais lu hors édition, l'original redevient la source affichée.
	}

	async createNewObservation() {
		if (!this.selectedTargetId) return;

		const newId = Date.now(); // ID temporaire, comme pour createNewTarget
		const newObs = {
			id: newId,
			targetId: this.selectedTargetId,
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

		// On l'ajoute temporairement en mémoire et on ouvre directement l'édition,
		// exactement comme createNewTarget — rien n'est envoyé au serveur tant que
		// l'utilisateur n'a pas cliqué "Enregistrer".
		this.observations.push(newObs);
		this.openObservation(newId);
		this.startEditObservation();
	}

	async saveObservation() {
		try {
			const obsToSave = { ...this.observationForm };
			const wasNewObs = obsToSave.id && obsToSave.id > 1000000000;
			const tempId = obsToSave.id;

			if (wasNewObs) {
				delete obsToSave.id;
			}

			const res = await fetch(`${API_URL}/observations`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(obsToSave)
			});
			const savedObs = await res.json();

			if (wasNewObs) {
				const idx = this.observations.findIndex(o => o.id === tempId);
				if (idx !== -1) {
					this.observations[idx] = savedObs;
				} else {
					this.observations.push(savedObs);
				}
			} else {
				const idx = this.observations.findIndex(o => o.id === savedObs.id);
				if (idx !== -1) {
					this.observations[idx] = savedObs;
				}
			}

			this.activeObservationId = savedObs.id;
			this.isEditingObservation = false;
		} catch (err) {
			console.error("Erreur sauvegarde observation:", err);
		}
	}

	async deleteObservation() {
		if (!this.activeObservationId) return;
		const confirmDelete = confirm("Supprimer définitivement ce rapport d'observation ?");
		if (confirmDelete) {
			try {
				await fetch(`${API_URL}/observations/${this.activeObservationId}`, { method: 'DELETE' });
				this.observations = this.observations.filter(o => o.id !== this.activeObservationId);
				this.activeObservationId = null;
				this.isEditingObservation = false;
			} catch (err) {
				console.error("Erreur suppression observation:", err);
			}
		}
	}
}

// Export singleton
export const appState = new AppState();