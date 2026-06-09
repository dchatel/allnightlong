// src/lib/state.svelte.ts
import { slide, fade } from 'svelte/transition';

class AppState {
	// --- TABLES DE DONNÉES EN MÉMOIRE ---
	targets = $state([
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
			imageRef: 'https://images.unsplash.com/photo-1543722530-d2c3201371e7?auto=format&fit=crop&w=400&q=80'
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
			imageRef: 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=400&q=80'
		}
	]);

	observations = $state([
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

	// --- ÉTATS DE L'INTERFACE ---
	searchQuery = $state('');
	selectedTargetId = $state<number | null>(1);
	isEditingTarget = $state(false); 
	activeObservationId = $state<number | null>(null);
	bottomView = $state<'list' | 'detail'>('list');
	showMapModal = $state(false);

	// Clones de modification
	targetForm = $state({ ...this.targets[0] });

	// --- ÉTATS DÉRIVÉS (Getters réactifs) ---
	get filteredTargets() {
		return this.targets.filter(t => 
			t.name.toLowerCase().includes(this.searchQuery.toLowerCase()) || 
			t.usualName.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
			t.constellation.toLowerCase().includes(this.searchQuery.toLowerCase())
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

	// --- LOGIQUE METIER & ACTIONS CRUD ---
	selectTarget(id: number) {
		this.selectedTargetId = id;
		this.isEditingTarget = false;
		this.bottomView = 'list';
		this.activeObservationId = null;
		
		const target = this.targets.find(t => t.id === id);
		if (target) {
			this.targetForm = { ...target };
		}
	}

	startEditTarget() {
		if (this.activeTarget) {
			this.targetForm = { ...this.activeTarget };
			this.isEditingTarget = true;
		}
	}

	saveTarget() {
		const index = this.targets.findIndex(t => t.id === this.selectedTargetId);
		if (index !== -1) {
			this.targets[index] = { ...this.targetForm };
			this.isEditingTarget = false;
		}
	}

	deleteTarget() {
		if (!this.selectedTargetId) return;
		const confirmDelete = confirm("Supprimer cet objet et TOUTES ses observations ?");
		if (confirmDelete) {
			this.observations = this.observations.filter(o => o.targetId !== this.selectedTargetId);
			this.targets = this.targets.filter(t => t.id !== this.selectedTargetId);
			if (this.targets.length > 0) {
				this.selectTarget(this.targets[0].id);
			} else {
				this.selectedTargetId = null;
			}
		}
	}

	createNewTarget() {
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
			imageRef: ''
		};
		this.targets.push(newTarget);
		this.selectTarget(newId);
		this.startEditTarget();
	}

	openObservation(id: number) {
		this.activeObservationId = id;
		this.bottomView = 'detail';
	}

	createNewObservation() {
		if (!this.selectedTargetId) return;
		const newId = Date.now();
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
		this.observations.push(newObs);
		this.openObservation(newId);
	}

	deleteObservation() {
		if (!this.activeObservationId) return;
		const confirmDelete = confirm("Supprimer ce rapport d'observation ?");
		if (confirmDelete) {
			this.observations = this.observations.filter(o => o.id !== this.activeObservationId);
			this.bottomView = 'list';
			this.activeObservationId = null;
		}
	}
}

// On exporte une instance unique (Singleton) pour toute l'app
export const appState = new AppState();