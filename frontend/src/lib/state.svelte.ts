// src/lib/state.svelte.ts
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
	bottomView = $state<'list' | 'detail'>('list');
	showMapModal = $state(false);

	// Clone de modification pour la cible active
	targetForm = $state<any>({ name: '' });

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
		return this.activeObservation ? this.activeObservation.imgGood + this.activeObservation.imgPass : 0;
	}
	
	get calculatedDuration() {
		return this.activeObservation ? (this.activeObservation.imgGood * Number(this.activeObservation.subExposure)) / 60 : 0;
	}

	// --- APPELS API (COMMUNICATION AVEC LE PYTHON) ---

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
		this.bottomView = 'list';
		this.activeObservationId = null;
		
		const target = this.targets.find(t => t.id === id);
		if (target) {
			this.targetForm = { ...target };
		}
		
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
			const res = await fetch(`${API_URL}/targets`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(this.targetForm)
			});
			const updatedTarget = await res.json();
			
			// Actualiser la liste locale
			await this.loadTargets();
			this.selectTarget(updatedTarget.id);
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

	async createNewTarget() {
		// Pas de fetch direct, on crée un formulaire vide en mode édition
		this.selectedTargetId = null;
		this.isEditingTarget = true;
		this.targetForm = {
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
	}

	openObservation(id: number) {
		this.activeObservationId = id;
		this.bottomView = 'detail';
	}

	async createNewObservation() {
		if (!this.selectedTargetId) return;
		
		// On génère un nouveau rapport d'observation vierge lié à notre objet en cours
		const newObs = {
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

		try {
			// On l'enregistre immédiatement dans la base SQLite via l'API
			const res = await fetch(`${API_URL}/observations`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(newObs)
			});
			const savedObs = await res.json();
			
			// On actualise la liste et on l'ouvre
			await this.loadObservations(this.selectedTargetId);
			this.openObservation(savedObs.id);
		} catch (err) {
			console.error("Erreur création observation:", err);
		}
	}

	async saveObservation() {
		if (!this.activeObservation) return;
		try {
			await fetch(`${API_URL}/observations`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(this.activeObservation)
			});
			// Svelte 5 met à jour automatiquement car l'objet est lié
			this.bottomView = 'list';
			await this.loadObservations(this.selectedTargetId!);
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
				await this.loadObservations(this.selectedTargetId!);
				this.bottomView = 'list';
				this.activeObservationId = null;
			} catch (err) {
				console.error("Erreur suppression observation:", err);
			}
		}
	}
}

// Export singleton
export const appState = new AppState();