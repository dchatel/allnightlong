// src/lib/state.svelte.ts
import { dev } from '$app/environment';
import { getCurrentWindow } from '@tauri-apps/api/window';
import { message, save } from '@tauri-apps/plugin-dialog';
import { convertFileSrc } from '@tauri-apps/api/core';
import { runChecks } from '$lib/checks';
import { slide, fade } from 'svelte/transition';

// En production, le port est annoncé par le backend à son démarrage
let apiUrl = dev ? "http://127.0.0.1:8000/api" : "";

const BACKEND_TIMEOUT_MS = 60000;
const BACKEND_LOG_LINES = 15;

// Jeton unique à ce lancement, transmis au backend au démarrage
export const backendToken = Array.from(crypto.getRandomValues(new Uint8Array(32)))
	.map(byte => byte.toString(16).padStart(2, '0'))
	.join('');

// FastAPI renvoie { detail: "..." } ou, pour une donnée refusée, la liste des champs en cause
async function readApiError(res: Response) {
	const detail = (await res.json().catch(() => null))?.detail;
	if (Array.isArray(detail)) {
		return `Valeur invalide : ${detail.map(error => error.loc.at(-1)).join(', ')}`;
	}
	return detail || `Erreur du serveur (${res.status})`;
}

// Lève une erreur si la requête échoue : le code qui suit un appel peut se fier à la réponse
async function apiFetch(path: string, init: RequestInit = {}) {
	const res = await fetch(`${apiUrl}${path}`, {
		...init,
		headers: { ...init.headers, Authorization: `Bearer ${backendToken}` }
	});
	if (!res.ok) throw new Error(await readApiError(res));
	return res;
}

async function showApiError(title: string, err: unknown) {
	console.error(`${title}:`, err);
	// fetch lève une TypeError quand le serveur est injoignable
	const reason = err instanceof TypeError ? 'Le serveur local ne répond pas.' : (err as Error).message;
	await message(reason, { title, kind: 'error' });
}

export interface Location {
	id?: number;
	label: string;
	lat: number;
	lon: number;
	elevationM: number | null;
	bortle: number | null;
	notes: string;
	// Un lieu est un emplacement d'instrument : hauteur de l'instrument, hauteur minimale, horizon
	instrumentHeight: number;
	minAltitude: number | null;
	horizon: Horizon | null;
}

// Hauteur de l'horizon (°) degré par degré d'azimut (360 valeurs), et obstacle végétal ou non
export interface Horizon {
	alt: number[];
	veg: boolean[];
	source: string;
}

interface HorizonEditor {
	horizon: Horizon | null;
	lat: number;
	lon: number;
	instrumentHeight: number;
	minAltitude: number | null;
	label: string;
	onApply: (horizon: Horizon | null, minAltitude: number | null) => void;
}

// Hauteur de l'horizon dans une direction (azimut en degrés, interpolé entre deux degrés)
export function horizonAt(horizon: Horizon | null | undefined, azimuth: number) {
	if (!horizon) return 0;
	const a = ((azimuth % 360) + 360) % 360;
	const i = Math.floor(a), t = a - i;
	return horizon.alt[i] * (1 - t) + horizon.alt[(i + 1) % 360] * t;
}

interface LocationEditor {
	form: Location;
	// Appelé avec le lieu enregistré, par exemple pour le choisir dans le rapport ouvert
	onSaved?: (location: Location) => void;
}

interface TargetSheet {
	mode: 'view' | 'create';
	targetId?: number;
	form?: any;
	// Appelé avec la cible créée, par exemple pour la choisir dans la ligne du rapport
	onSaved?: (target: any) => void;
}

// Les poses (bon / pass / bad) sont celles du champ, dans l'observation : communes à ses cibles
export interface ObservationTarget {
	targetId: number | null;
	altitude: string;
	notes: string;
}

export interface ObservationImage {
	id?: number;
	path: string;
	kind: string;
	software: string;
	palette: string;
	caption: string;
	// Favorite du champ entier (image sans cible)
	isFavorite: boolean;
	// Cibles visibles sur l'image ; aucune = champ entier
	targetIds: number[];
	// Cibles dont c'est la favorite (une favorite par cible)
	favoriteTargetIds: number[];
	missing?: boolean;
}

export const IMAGE_KINDS: Record<string, string> = {
	'traitée': 'Traitée',
	'brute': 'Brute',
	'astrométrie': 'Astrométrie',
	'carte': 'Carte du ciel'
};

// Titre d'une image : logiciel et palette, sinon son type
export function imageTitle(image: ObservationImage) {
	return [image.software, image.palette].filter(Boolean).join(' · ') || IMAGE_KINDS[image.kind] || image.kind || 'Image';
}

// Vignette d'une observation.
// Vue depuis une cible : sa favorite, sinon sa première image, sinon la favorite du champ.
// Sinon : la favorite du champ, sinon celle de la première cible qui en a une, sinon la première image
// (une carte du ciel en dernier recours).
export function favoriteImage(obs: any, targetId: number | null = null): ObservationImage | null {
	const images: ObservationImage[] = obs?.images ?? [];
	const field = images.find(i => i.isFavorite);
	if (targetId != null) {
		const own = images.find(i => i.favoriteTargetIds?.includes(targetId)) ?? images.find(i => i.targetIds.includes(targetId));
		if (own) return own;
	}
	if (field) return field;
	for (const row of obs?.targets ?? []) {
		const favorite = images.find(i => i.favoriteTargetIds?.includes(row.targetId));
		if (favorite) return favorite;
	}
	return images.find(i => i.kind !== 'carte') ?? images[0] ?? null;
}

// Chemin local → adresse lisible par la fenêtre de l'application
export function imageSrc(path: string) {
	if (!path) return '';
	if (path.startsWith('http://') || path.startsWith('https://')) return path;
	try {
		return convertFileSrc(path);
	} catch {
		return path;
	}
}

export interface WeatherReading {
	time: string;
	cloudLow: number | null;
	cloudMid: number | null;
	cloudHigh: number | null;
	seeing: number | null;
	index1: number | null;
	index2: number | null;
	jetStream: number | null;
	temp: number | null;
	humidity: number | null;
	dewPoint: number | null;
	source: string;
	edited: boolean;
}

// Résumé d'une capture lu dans un FITS du Seestar (heures en TU)
export interface FitsSummary {
	start: string;
	end: string;
	startExact: boolean;
	object: string;
	filter: string;
	instrument: string;
	sensorTemp: number | null;
	exposure: number;
	frames: number | null;
	preview: string;
	targetIds: number[];
	locationId: number | null;
}

export function emptyObservationTarget(targetId: number | null = null): ObservationTarget {
	return { targetId, altitude: '', notes: '' };
}

const MONTHS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'];

// "2026-11-14 19:30" → "14/11/2026"
export function formatDate(datetime: string | null | undefined) {
	const [y, m, d] = (datetime ?? '').slice(0, 10).split('-');
	return d ? `${d}/${m}/${y}` : '';
}

// "2026-11-14 19:30" → "14/11/2026 19:30"
export function formatDateTime(datetime: string | null | undefined) {
	if (!datetime) return '';
	const time = datetime.slice(11, 16);
	return time ? `${formatDate(datetime)} ${time}` : formatDate(datetime);
}

export function monthLabel(key: string) {
	const [y, m] = key.split('-');
	const name = MONTHS[Number(m) - 1] ?? '';
	return `${name.charAt(0).toUpperCase()}${name.slice(1)} ${y}`;
}

// Coordonnées saisies en texte libreavant les lieux enregistrés : "50,5244 N / 2,6400 E"
export function parseLegacyCoords(text: string | null | undefined): { lat: number; lon: number } | null {
	const numbers = (text ?? '').match(/-?\d+[.,]\d+/g);
	if (!numbers || numbers.length < 2) return null;
	const [lat, lon] = numbers.map(n => Number(n.replace(',', '.')));
	if (Math.abs(lat) > 90 || Math.abs(lon) > 180) return null;
	return { lat, lon };
}

class AppState {
	isBackendReady = $state(false);
	// Motif affiché sur l'écran de démarrage quand le backend ne répond pas
	backendError = $state('');
	backendLog = $state<string[]>([]);
	backendStopped = false;

	// --- TABLES DE DONNÉES RÉACTIVES ---
	targets = $state<any[]>([]);
	observations = $state<any[]>([]);
	locations = $state<Location[]>([]);

	// Fenêtre de création / modification d'un lieu (null = fermée)
	locationEditor = $state<LocationEditor | null>(null);
	// Liste des lieux, et éditeur d'horizon en plein écran
	showLocations = $state(false);
	horizonEditor = $state<HorizonEditor | null>(null);

	// Fiche d'une cible ouverte par-dessus un rapport, en lecture ou en création (null = fermée)
	targetSheet = $state<TargetSheet | null>(null);

	// --- ÉTATS DE L'INTERFACE ---
	leftTab = $state<'targets' | 'observations'>('targets');
	searchQuery = $state('');
	targetSortDescending = $state(false);
	observationSearch = $state('');
	observationSortOldestFirst = $state(false);
	// Mois affiché dans l'onglet Observations ("AAAA-MM"), null = toutes
	observationMonth = $state<string | null>(null);
	selectedTargetId = $state<number | null>(null);
	isEditingTarget = $state(false); 
	activeObservationId = $state<number | null>(null);
	observationOpenedFromTargetId = $state<number | null>(null);
	isEditingObservation = $state(false);
	showMapModal = $state(false);
	showSettings = $state(false);
	showChecks = $state(false);
	// Données à vérifier : signalements marqués « c'est normal », et tous les relevés météo
	dismissedChecks = $state<string[]>([]);
	allWeather = $state<(WeatherReading & { sessionId: number })[]>([]);
	settings = $state({ imagesFolder: '', weatherMarginHours: 1 });

	// Relevés météo par session, et état de leur récupération ("" = rien en cours)
	weatherBySession = $state<Record<number, WeatherReading[]>>({});
	weatherStatus = $state<Record<number, string>>({});

	// Clone de modification pour la cible active
	targetForm = $state<any>({ name: '' });
	// Clone de modification pour l'observation active
	observationForm = $state<any>({});

	constructor() {
	}

	// Lit la ligne "ALLNIGHTLONG_PORT=..." écrite par le backend sur stdout
	readBackendOutput(line: string) {
		const port = line.match(/^ALLNIGHTLONG_PORT=(\d+)/)?.[1];
		if (port) apiUrl = `http://127.0.0.1:${port}/api`;
		this.logBackendOutput(line);
	}

	logBackendOutput(line: string) {
		this.backendLog = [...this.backendLog, line.trimEnd()].slice(-BACKEND_LOG_LINES);
	}

	backendFailed(reason: string) {
		this.backendStopped = true;
		this.backendError = reason;
	}

	async waitForBackend() {
		const start = Date.now();
		let lastError = '';
		while (!this.isBackendReady && !this.backendStopped) {
			try {
				const res = apiUrl ? await apiFetch('/status') : null;
				if (res?.ok) {
					console.log("Backend is ready.");
					await Promise.all([this.loadTargets(), this.loadLocations(), this.loadObservations(), this.loadSettings(), this.loadChecksData()]);
					this.isBackendReady = true;
					break;
				}
			} catch (e) {
				lastError = String(e);
			}
			// Le backend peut encore arriver : un antivirus retarde parfois son lancement
			if (Date.now() - start > BACKEND_TIMEOUT_MS) {
				this.backendError = `Le serveur local ne répond toujours pas. ${lastError}`;
			}
			await new Promise(resolve => setTimeout(resolve, 200));
		}
	}

	// --- ÉTATS DÉRIVÉS RÉACTIFS ---
	get filteredTargets() {
		const query = this.searchQuery.toLowerCase();
		const direction = this.targetSortDescending ? -1 : 1;
		return this.targets
			.filter(t =>
				t.name.toLowerCase().includes(query) ||
				(t.usualName && t.usualName.toLowerCase().includes(query)) ||
				(t.constellation && t.constellation.toLowerCase().includes(query))
			)
			// "numeric" range NGC 925 avant NGC 7000
			.sort((a, b) => direction * a.name.localeCompare(b.name, 'fr', { numeric: true }));
	}

	// Cibles triées par nom, pour les listes de choix
	get targetsByName() {
		return [...this.targets].sort((a, b) => a.name.localeCompare(b.name, 'fr', { numeric: true }));
	}

	targetName(id: number | null | undefined) {
		return this.targets.find(t => t.id === id)?.name ?? '';
	}

	observationTargetNames(obs: any) {
		return (obs?.targets ?? []).map((t: ObservationTarget) => this.targetName(t.targetId)).filter(Boolean).join(' + ');
	}

	// Les plus récentes d'abord
	get observationsByDate() {
		return [...this.observations].sort((a, b) => String(b.start).localeCompare(String(a.start)));
	}

	// Mois ayant des observations, avec leur nombre et les cibles vues
	get observationMonths() {
		const months = new Map<string, any[]>();
		for (const obs of this.observationsByDate) {
			const key = String(obs.start).slice(0, 7);
			months.set(key, [...(months.get(key) ?? []), obs]);
		}
		return [...months].map(([key, list]) => ({
			key,
			label: monthLabel(key),
			count: list.length,
			preview: [...new Set(list.flatMap(o => o.targets.map((t: ObservationTarget) => this.targetName(t.targetId))))].join(', ')
		}));
	}

	// Onglet Observations : mois choisi, recherche (cible, lieu, filtre, notes) et ordre
	get visibleObservations() {
		const query = this.observationSearch.toLowerCase().trim();
		const list = this.observationsByDate.filter(obs =>
			(!this.observationMonth || String(obs.start).startsWith(this.observationMonth)) &&
			(!query || [this.observationTargetNames(obs), this.locationText(obs), obs.filter, obs.notes, formatDate(obs.start)]
				.some(text => String(text ?? '').toLowerCase().includes(query)))
		);
		return this.observationSortOldestFirst ? list.reverse() : list;
	}

	get activeTarget() {
		return this.targets.find(t => t.id === this.selectedTargetId) || null;
	}

	get activeTargetObservations() {
		return this.observationsByDate.filter(o => o.targets.some((t: ObservationTarget) => t.targetId === this.selectedTargetId));
	}

	get activeObservation() {
		return this.observations.find(o => o.id === this.activeObservationId) || null;
	}

	// --- APPELS API (COMMUNICATION AVEC LE PYTHON) ---

	async closeApp(){
		try {
			await apiFetch('/shutdown', { method: 'POST' });
		} catch (err) {
			console.log("Déconnexion attendue lors du shutdown.");
		}

		const appWindow = getCurrentWindow();
		await appWindow.close();
	}

	// --- PRÉ-REMPLISSAGE DEPUIS UN FITS ---

	async readFits(path: string): Promise<FitsSummary | null> {
		try {
			const res = await apiFetch('/fits/read', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ path })
			});
			return await res.json();
		} catch (err) {
			await showApiError('Lecture du FITS impossible', err);
			return null;
		}
	}

	// --- DONNÉES À VÉRIFIER ---

	async loadChecksData() {
		try {
			const [dismissed, weather] = await Promise.all([apiFetch('/checks/dismissed'), apiFetch('/weather')]);
			this.dismissedChecks = await dismissed.json();
			this.allWeather = await weather.json();
		} catch (err) {
			console.warn('Données à vérifier non chargées :', err);
		}
	}

	get checks() {
		return runChecks({ observations: this.observations, targets: this.targets, locations: this.locations, weather: this.allWeather });
	}

	get openChecks() {
		return this.checks.filter(c => !this.dismissedChecks.includes(c.key));
	}

	async setCheckDismissed(key: string, dismissed: boolean) {
		try {
			const res = await apiFetch('/checks/dismissed', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ key, dismissed })
			});
			this.dismissedChecks = await res.json();
		} catch (err) {
			await showApiError('Enregistrement impossible', err);
		}
	}

	// Depuis l'écran des vérifications : le rapport s'ouvre, l'écran se ferme
	openObservationFromChecks(id: number) {
		this.showChecks = false;
		this.openObservation(id);
	}

	// --- RÉGLAGES ---

	async loadSettings() {
		try {
			const res = await apiFetch('/settings');
			this.settings = await res.json();
		} catch (err) {
			await showApiError('Chargement des réglages impossible', err);
		}
	}

	async saveSettings(settings: { imagesFolder: string; weatherMarginHours: number }) {
		try {
			const res = await apiFetch('/settings', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(settings)
			});
			this.settings = await res.json();
			this.showSettings = false;
			// Les chemins d'images ont pu changer de forme : on relit ce qui les affiche
			await Promise.all([this.loadTargets(), this.loadObservations()]);
		} catch (err) {
			await showApiError('Enregistrement des réglages impossible', err);
		}
	}

	// --- MÉTÉO ---

	async loadWeather(sessionId: number | null | undefined) {
		if (!sessionId || this.weatherBySession[sessionId]) return;
		try {
			const res = await apiFetch(`/sessions/${sessionId}/weather`);
			this.weatherBySession[sessionId] = await res.json();
		} catch (err) {
			console.warn('Météo non chargée :', err);
		}
	}

	// Récupération Open-Meteo, sans jamais bloquer ni interrompre la saisie : une erreur
	// (pas de connexion, pas de lieu) est seulement affichée sous les relevés.
	async fetchWeather(sessionId: number | null | undefined, refresh = false) {
		if (!sessionId) return;
		this.weatherStatus[sessionId] = 'loading';
		try {
			const res = await apiFetch(`/sessions/${sessionId}/weather/fetch?refresh=${refresh}`, { method: 'POST' });
			this.weatherBySession[sessionId] = await res.json();
			this.weatherStatus[sessionId] = '';
		} catch (err) {
			const reason = err instanceof TypeError ? 'Le serveur local ne répond pas.' : (err as Error).message;
			this.weatherStatus[sessionId] = `Météo non récupérée : ${reason}`;
		}
	}

	// Relevés modifiés dans la grille : remplacent ceux de la session
	async saveWeather(sessionId: number, readings: WeatherReading[]) {
		try {
			const res = await apiFetch(`/sessions/${sessionId}/weather/readings`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(readings)
			});
			this.weatherBySession[sessionId] = await res.json();
			return true;
		} catch (err) {
			await showApiError('Enregistrement de la météo impossible', err);
			return false;
		}
	}

	// Lignes au format meteoblue des notes → relevés (l'heure est rattachée à la nuit donnée)
	async parseMeteoblue(text: string, nightDate: string): Promise<WeatherReading[]> {
		try {
			const res = await apiFetch('/weather/parse-meteoblue', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ text, nightDate })
			});
			return await res.json();
		} catch (err) {
			await showApiError('Lecture de la ligne meteoblue impossible', err);
			return [];
		}
	}

	async exportDatabase() {
		const path = await save({
			title: 'Exporter la base de données',
			defaultPath: `allnightlong-${new Date().toISOString().split('T')[0]}.db`,
			filters: [{ name: 'Base AllNightLong', extensions: ['db'] }]
		});
		if (!path) return;

		try {
			await apiFetch('/export', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ path })
			});

			await message(
				"Vos cibles et observations sont sauvegardées.\n\nLes images ne sont pas incluses : la base ne contient que leur emplacement sur le disque.",
				{ title: 'Export terminé', kind: 'info' }
			);
		} catch (err) {
			await showApiError('Export impossible', err);
		}
	}

	async loadTargets() {
		try {
			const res = await apiFetch('/targets');
			this.targets = await res.json();
			
			// Sélectionner automatiquement le premier élément s'il y en a un
			if (this.targets.length > 0 && this.selectedTargetId === null) {
				this.selectTarget((this.filteredTargets[0] ?? this.targets[0]).id);
			}
		} catch (err) {
			await showApiError('Chargement des cibles impossible', err);
		}
	}

	// --- FICHE CIBLE PAR-DESSUS UN RAPPORT ---

	openTargetSheet(targetId: number) {
		this.targetSheet = { mode: 'view', targetId };
	}

	openTargetCreator(onSaved?: (target: any) => void) {
		this.targetSheet = {
			mode: 'create',
			form: {
				name: '', usualName: '', constellation: '', otherDesignations: '', type: '', group: '',
				magnitude: '', colorIndex: '', surfBrightness: '', size: '', ra: '', dec: '', imageRef: '', notes: ''
			},
			onSaved
		};
	}

	closeTargetSheet() {
		this.targetSheet = null;
	}

	async createTargetFromSheet() {
		const sheet = this.targetSheet;
		if (!sheet?.form) return;
		const form = $state.snapshot(sheet.form);
		if (!form.name.trim()) {
			await message('Indiquez au moins le nom de la cible.', { title: 'Nom manquant', kind: 'warning' });
			return;
		}
		try {
			const res = await apiFetch('/targets', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ ...form, name: form.name.trim() })
			});
			const saved = await res.json();
			this.targets.push(saved);
			sheet.onSaved?.(saved);
			this.targetSheet = null;
		} catch (err) {
			await showApiError('Création de la cible impossible', err);
		}
	}

	// Quitte le rapport pour la fiche complète, dans l'onglet Cibles
	showTargetInTargetsTab(targetId: number) {
		this.targetSheet = null;
		this.leftTab = 'targets';
		this.selectTarget(targetId);
	}

	// --- LIEUX ---

	async loadLocations() {
		try {
			const res = await apiFetch('/locations');
			this.locations = await res.json();
		} catch (err) {
			await showApiError('Chargement des lieux impossible', err);
		}
	}

	locationById(id: number | null | undefined) {
		return id == null ? null : this.locations.find(l => l.id === id) ?? null;
	}

	// Libellé du lieu enregistré, sinon l'ancienne saisie en texte libre
	locationText(obs: any) {
		return this.locationById(obs?.locationId)?.label || obs?.legacyLocation || '';
	}

	// Lieu proposé pour un nouveau rapport : celui du rapport le plus récent qui en a un
	get defaultLocationId() {
		const latest = this.observationsByDate.find(o => this.locationById(o.locationId));
		return latest?.locationId ?? (this.locations.length === 1 ? this.locations[0].id : null);
	}

	openLocationEditor(location: Partial<Location> = {}, onSaved?: (location: Location) => void) {
		this.locationEditor = {
			form: { label: '', lat: NaN, lon: NaN, elevationM: null, bortle: null, notes: '', instrumentHeight: 1, minAltitude: null, horizon: null, ...location },
			onSaved
		};
	}

	closeLocationEditor() {
		this.locationEditor = null;
	}

	async saveLocation(location: Location) {
		try {
			const res = await apiFetch('/locations', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(location)
			});
			const saved: Location = await res.json();
			const others = this.locations.filter(l => l.id !== saved.id);
			this.locations = [...others, saved].sort((a, b) => a.label.localeCompare(b.label, 'fr'));
			this.locationEditor?.onSaved?.(saved);
			this.locationEditor = null;
		} catch (err) {
			await showApiError('Enregistrement du lieu impossible', err);
		}
	}

	// Horizon calculé depuis le LiDAR HD de l'IGN (quelques secondes ; France uniquement)
	async lidarHorizon(lat: number, lon: number, instrumentHeight: number): Promise<Horizon | null> {
		try {
			const res = await apiFetch('/geo/lidar-horizon', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ lat, lon, instrumentHeight })
			});
			return await res.json();
		} catch (err) {
			await showApiError('Calcul de l’horizon impossible', err);
			return null;
		}
	}

	// Services en ligne (adresse, recherche, altitude), appelés via le backend.
	// Une panne réseau ne doit jamais bloquer la saisie : l'appelant reçoit null.
	async geo(path: string, params: Record<string, string | number>) {
		try {
			const query = new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)]));
			const res = await apiFetch(`/geo/${path}?${query}`);
			return await res.json();
		} catch (err) {
			console.warn(`Service en ligne indisponible (${path}) :`, err);
			return null;
		}
	}

	async loadObservations() {
		try {
			const res = await apiFetch('/observations');
			this.observations = await res.json();
		} catch (err) {
			await showApiError('Chargement des observations impossible', err);
		}
	}

	async selectTarget(id: number) {
		this.selectedTargetId = id;
		this.isEditingTarget = false;
		this.closeObservation();
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

			const res = await apiFetch('/targets', {
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
			await showApiError('Enregistrement impossible', err);
		}
	}

	async deleteTarget() {
		if (!this.selectedTargetId) return;
		const confirmDelete = confirm("Supprimer définitivement cet objet céleste et toutes ses observations ?");
		if (confirmDelete) {
			try {
				await apiFetch(`/targets/${this.selectedTargetId}`, { method: 'DELETE' });
				this.selectedTargetId = null;
				await Promise.all([this.loadTargets(), this.loadObservations()]);
			} catch (err) {
				await showApiError('Suppression impossible', err);
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
				this.selectTarget((this.filteredTargets[0] ?? this.targets[0]).id);
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

	// fromTargetId : rapport ouvert depuis cette cible, sa galerie s'ouvre filtrée sur elle
	openObservation(id: number, fromTargetId: number | null = null) {
		this.observationOpenedFromTargetId = fromTargetId;
		this.activeObservationId = id;
		this.isEditingObservation = false;
		this.loadWeather(this.activeObservation?.sessionId);
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
			// Copie profonde : le tableau des cibles est modifié ligne par ligne
			this.observationForm = $state.snapshot(this.activeObservation);
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

	// Depuis une fiche cible, le rapport part avec cette cible ; depuis l'onglet Observations, sans cible
	async createNewObservation(targetId: number | null = this.leftTab === 'targets' ? this.selectedTargetId : null) {
		const newId = Date.now(); // ID temporaire, comme pour createNewTarget
		const newObs = {
			id: newId,
			start: '',
			end: '',
			locationId: this.defaultLocationId,
			bortle: null,
			instrument: '',
			sensor: 'Seestar S50 (IMX462)',
			filter: 'IRCUT',
			sensorTemp: '',
			subExposure: '10',
			imgTotal: 0,
			imgGood: 0,
			imgPass: 0,
			imgBad: 0,
			notes: '',
			images: [],
legacyLocation: '',
			targets: targetId ? [emptyObservationTarget(targetId)] : []
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
			const obsToSave = $state.snapshot(this.observationForm);
			// Lignes ajoutées mais sans cible choisie : ignorées plutôt que refusées
			obsToSave.targets = obsToSave.targets.filter((t: ObservationTarget) => t.targetId);
			// Un champ numérique vidé vaut null : compté comme 0
			for (const key of ['imgTotal', 'imgGood', 'imgPass', 'imgBad']) obsToSave[key] = Number(obsToSave[key]) || 0;
			const wasNewObs = obsToSave.id && obsToSave.id > 1000000000;
			const tempId = obsToSave.id;

			if (wasNewObs) {
				delete obsToSave.id;
			}

			const res = await apiFetch('/observations', {
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
			// Météo du créneau : seules les heures manquantes sont demandées, en arrière-plan
			this.fetchWeather(savedObs.sessionId);
		} catch (err) {
			await showApiError('Enregistrement impossible', err);
		}
	}

	async deleteObservation() {
		if (!this.activeObservationId) return;
		const confirmDelete = confirm("Supprimer définitivement ce rapport d'observation ?");
		if (confirmDelete) {
			try {
				await apiFetch(`/observations/${this.activeObservationId}`, { method: 'DELETE' });
				this.observations = this.observations.filter(o => o.id !== this.activeObservationId);
				this.activeObservationId = null;
				this.isEditingObservation = false;
			} catch (err) {
				await showApiError('Suppression impossible', err);
			}
		}
	}
}

// Export singleton
export const appState = new AppState();