// Données à vérifier : règles simples qui repèrent des saisies suspectes. Chaque signalement a une clé
// stable, pour qu'un « c'est normal » reste mémorisé tant que la donnée ne change pas de nature.
import { makeObserver, moonIllumination, targetAltitude, targetCoords, utcDate } from '$lib/astro';
import { formatDate, parseLegacyCoords, type ObservationTarget, type WeatherReading } from '$lib/state.svelte';

export interface Check {
	key: string;
	rule: string;
	title: string;
	detail: string;
	observationIds: number[];
}

export const RULES: Record<string, string> = {
	overlap: 'Observations qui se chevauchent',
	poses: 'Compteurs de poses incohérents',
	weather: 'Même relevé météo sur deux nuits',
	moon: 'Phase de Lune notée différente du calcul',
	altitude: 'Hauteur saisie différente du calcul',
	times: 'Heures manquantes ou durée anormale',
	location: 'Observation sans lieu',
	images: 'Observation sans image'
};

const MAX_HOURS = 14;
const MOON_TOLERANCE = 15; // points de %
const ALTITUDE_MARGIN = 5; // degrés autour de la plage calculée

interface Inputs {
	observations: any[];
	targets: any[];
	locations: any[];
	weather: (WeatherReading & { sessionId: number })[];
}

export function runChecks({ observations, targets, locations, weather }: Inputs): Check[] {
	const checks: Check[] = [];
	const targetById = new Map(targets.map(t => [t.id, t]));
	const names = (obs: any) => obs.targets.map((r: ObservationTarget) => targetById.get(r.targetId)?.name).filter(Boolean).join(' + ');
	const label = (obs: any) => `${formatDate(obs.start)} — ${names(obs) || 'sans cible'}`;
	const hasTime = (text: string) => (text ?? '').length > 10;

	function observerOf(obs: any) {
		const location = locations.find(l => l.id === obs.locationId);
		const point = location ?? parseLegacyCoords(obs.legacyLocation);
		return point ? makeObserver(point.lat, point.lon, location?.elevationM) : null;
	}

	for (const obs of observations) {
		// --- Heures
		if (!hasTime(obs.start)) {
			checks.push({ key: `times:notime:${obs.id}`, rule: 'times', title: label(obs), detail: "Heure de début inconnue : la nuit, la météo et la hauteur des cibles restent approximatives.", observationIds: [obs.id] });
		} else if (!hasTime(obs.end)) {
			checks.push({ key: `times:noend:${obs.id}`, rule: 'times', title: label(obs), detail: 'Heure de fin inconnue.', observationIds: [obs.id] });
		} else {
			const hours = (utcDate(obs.end).getTime() - utcDate(obs.start).getTime()) / 3_600_000;
			if (hours > MAX_HOURS) {
				checks.push({ key: `times:long:${obs.id}`, rule: 'times', title: label(obs), detail: `Durée de ${hours.toFixed(1)} h : une erreur de date est probable.`, observationIds: [obs.id] });
			}
		}

		if (!obs.locationId) {
			checks.push({ key: `location:${obs.id}`, rule: 'location', title: label(obs), detail: obs.legacyLocation ? `Ancienne saisie : ${obs.legacyLocation}` : 'Aucun lieu.', observationIds: [obs.id] });
		}
		if (!(obs.images ?? []).length) {
			checks.push({ key: `images:${obs.id}`, rule: 'images', title: label(obs), detail: 'Aucune image rattachée à ce rapport.', observationIds: [obs.id] });
		}

		// --- Poses : bon + pass = total (convention récente) ou bon + pass + bad = total (premières fiches)
		for (const row of obs.targets as ObservationTarget[]) {
			const { imgGood: g, imgPass: p, imgBad: b } = row;
			if (!obs.imgTotal || !(g || p || b)) continue;
			if (g + p === obs.imgTotal || g + p + b === obs.imgTotal) continue;
			checks.push({
				key: `poses:${obs.id}:${row.targetId}`, rule: 'poses', title: label(obs),
				detail: `${targetById.get(row.targetId)?.name ?? 'Cible'} : bon ${g} + pass ${p} = ${g + p}, avec bad ${b} : ${g + p + b} ; total des poses ${obs.imgTotal}.`,
				observationIds: [obs.id]
			});
		}

		const observer = observerOf(obs);
		if (!observer || !hasTime(obs.start)) continue;
		const t0 = utcDate(obs.start).getTime();
		const t1 = hasTime(obs.end) ? utcDate(obs.end).getTime() : t0;

		// --- Lune : « Lune phase 85% », « Lune : Premier croissant, 30% »
		const noted = (obs.notes ?? '').match(/lune[^%\n]{0,40}?(\d{1,3})\s*%/i);
		if (noted) {
			const computed = Math.round(moonIllumination(new Date((t0 + t1) / 2)));
			const value = Number(noted[1]);
			if (Math.abs(value - computed) > MOON_TOLERANCE) {
				checks.push({ key: `moon:${obs.id}`, rule: 'moon', title: label(obs), detail: `Note : ${value} % ; calcul : ${computed} % au milieu du créneau. Note recopiée d'une autre nuit ?`, observationIds: [obs.id] });
			}
		}

		// --- Hauteur saisie hors de la plage calculée pendant le créneau
		for (const row of obs.targets as ObservationTarget[]) {
			const entered = (row.altitude ?? '').replace(/,/g, '.').match(/-?\d+(?:\.\d+)?/g)?.map(Number) ?? [];
			const coords = targetCoords(targetById.get(row.targetId));
			if (!entered.length || !coords) continue;
			let min = 90, max = -90;
			for (let t = t0; t <= t1; t += 10 * 60_000) {
				const alt = targetAltitude(coords, new Date(t), observer);
				min = Math.min(min, alt);
				max = Math.max(max, alt);
			}
			const outside = entered.filter(v => v < min - ALTITUDE_MARGIN || v > max + ALTITUDE_MARGIN);
			if (outside.length) {
				checks.push({
					key: `altitude:${obs.id}:${row.targetId}`, rule: 'altitude', title: label(obs),
					detail: `${targetById.get(row.targetId)?.name} : ${row.altitude}° saisi ; calcul : de ${Math.round(min)}° à ${Math.round(max)}° pendant le créneau.`,
					observationIds: [obs.id]
				});
			}
		}
	}

	// --- Chevauchements : même lieu, même instrument, créneaux qui se recouvrent
	const timed = observations.filter(o => hasTime(o.start) && hasTime(o.end) && o.locationId);
	for (let i = 0; i < timed.length; i++) {
		for (let j = i + 1; j < timed.length; j++) {
			const a = timed[i], b = timed[j];
			if (a.locationId !== b.locationId || (a.instrument ?? '') !== (b.instrument ?? '')) continue;
			if (utcDate(a.start) < utcDate(b.end) && utcDate(b.start) < utcDate(a.end)) {
				const [x, y] = [a.id, b.id].sort((m, n) => m - n);
				checks.push({
					key: `overlap:${x}-${y}`, rule: 'overlap', title: `${label(a)} / ${label(b)}`,
					detail: 'Les deux créneaux se recouvrent au même lieu, avec le même instrument (aucun instrument précisé compte comme le même).',
					observationIds: [a.id, b.id]
				});
			}
		}
	}

	// --- Relevé météo identique sur deux nuits (au moins quatre valeurs renseignées)
	const fields: (keyof WeatherReading)[] = ['cloudLow', 'cloudMid', 'cloudHigh', 'seeing', 'index1', 'index2', 'jetStream', 'temp', 'humidity'];
	const seen = new Map<string, WeatherReading & { sessionId: number }>();
	for (const r of weather) {
		if (r.source === 'open-meteo') continue;
		const values = fields.map(f => r[f]);
		if (values.filter(v => v != null).length < 4) continue;
		const signature = values.join('|');
		const first = seen.get(signature);
		if (first && first.sessionId !== r.sessionId) {
			const obsA = observations.filter(o => o.sessionId === first.sessionId);
			const obsB = observations.filter(o => o.sessionId === r.sessionId);
			checks.push({
				key: `weather:${first.sessionId}@${first.time}|${r.sessionId}@${r.time}`, rule: 'weather',
				title: `${obsA.map(label).join(', ')} / ${obsB.map(label).join(', ')}`,
				detail: `Relevé du ${first.time} TU identique à celui du ${r.time} TU : copie probable.`,
				observationIds: [...obsA, ...obsB].map(o => o.id)
			});
		}
		if (!first) seen.set(signature, r);
	}

	return checks;
}
