// Éphémérides calculées localement (astronomy-engine, sans connexion) : nuit, crépuscules, hauteur
// des cibles et de la Lune pour un lieu. Toutes les heures manipulées ici sont en TU.
import {
	Body,
	Equator,
	Horizon,
	HorizonFromVector,
	Illumination,
	Observer,
	RotateVector,
	Rotation_EQJ_HOR,
	SearchAltitude,
	SearchRiseSet,
	Spherical,
	VectorFromSphere
} from 'astronomy-engine';

export { Observer };

// "05 35 16.47 / 83.81", "05h 35m 17s" ou "+41 38 38,032" → heures (AD) ou degrés (Dec)
export function parseSexagesimal(value: string | null | undefined): number | null {
	const sexagesimal = (value ?? '').split('/')[0].replace(/,/g, '.');
	const [first, minutes = 0, seconds = 0] = (sexagesimal.match(/\d+(?:\.\d+)?/g) ?? []).map(Number);
	if (first === undefined) return null;
	const absolute = first + minutes / 60 + seconds / 3600;
	return sexagesimal.trim().startsWith('-') ? -absolute : absolute;
}

// Coordonnées J2000 d'une cible de la base (AD en heures, Dec en degrés)
export function targetCoords(target: { ra?: string; dec?: string } | null | undefined) {
	const ra = parseSexagesimal(target?.ra);
	const dec = parseSexagesimal(target?.dec);
	return ra === null || dec === null ? null : { ra, dec };
}

export function makeObserver(lat: number, lon: number, elevationM: number | null | undefined) {
	return new Observer(lat, lon, elevationM ?? 0);
}

export interface NightEvents {
	sunset: Date | null;
	sunrise: Date | null;
	// Le Soleil passe sous -6°, -12° et -18° (crépuscules civil, nautique, astronomique)
	civilDusk: Date | null;
	civilDawn: Date | null;
	nauticalDusk: Date | null;
	nauticalDawn: Date | null;
	astroDusk: Date | null;
	astroDawn: Date | null;
}

// Nuit commençant le soir de nightDate ("AAAA-MM-JJ"). Un événement absent (nuit d'été sans nuit
// astronomique, par exemple) vaut null.
export function nightEvents(nightDate: string, observer: Observer): NightEvents {
	// Midi solaire du lieu : on cherche le coucher après, le lever le lendemain
	const noon = new Date(`${nightDate}T12:00:00Z`);
	noon.setUTCMinutes(noon.getUTCMinutes() - Math.round((observer.longitude / 15) * 60));
	const down = (altitude: number) => SearchAltitude(Body.Sun, observer, -1, noon, 1, altitude)?.date ?? null;
	const sunset = SearchRiseSet(Body.Sun, observer, -1, noon, 1)?.date ?? null;
	const from = sunset ?? noon;
	const up = (altitude: number) => SearchAltitude(Body.Sun, observer, +1, from, 1, altitude)?.date ?? null;
	return {
		sunset,
		sunrise: SearchRiseSet(Body.Sun, observer, +1, from, 1)?.date ?? null,
		civilDusk: down(-6),
		civilDawn: up(-6),
		nauticalDusk: down(-12),
		nauticalDawn: up(-12),
		astroDusk: down(-18),
		astroDawn: up(-18)
	};
}

// Hauteur (degrés, réfraction comprise) d'un objet de coordonnées J2000 : précession et nutation
// sont prises en compte par la rotation EQJ → horizon du lieu.
export function targetAltitude(coords: { ra: number; dec: number }, date: Date, observer: Observer) {
	const vector = VectorFromSphere(new Spherical(coords.dec, coords.ra * 15, 1), date);
	const local = RotateVector(Rotation_EQJ_HOR(date, observer), vector);
	return HorizonFromVector(local, 'normal').lat;
}

// Hauteur et azimut (degrés depuis le nord, vers l'est) : pour savoir derrière quel obstacle passe la cible
export function targetHorizontal(coords: { ra: number; dec: number }, date: Date, observer: Observer) {
	const vector = VectorFromSphere(new Spherical(coords.dec, coords.ra * 15, 1), date);
	const local = RotateVector(Rotation_EQJ_HOR(date, observer), vector);
	const sphere = HorizonFromVector(local, 'normal');
	return { alt: sphere.lat, az: sphere.lon };
}

export function sunAltitude(date: Date, observer: Observer) {
	const eq = Equator(Body.Sun, date, observer, true, true);
	return Horizon(date, observer, eq.ra, eq.dec, 'normal').altitude;
}

export function moonAltitude(date: Date, observer: Observer) {
	const eq = Equator(Body.Moon, date, observer, true, true);
	return Horizon(date, observer, eq.ra, eq.dec, 'normal').altitude;
}

// Partie éclairée du disque lunaire, en %
export function moonIllumination(date: Date) {
	return Illumination(Body.Moon, date).phase_fraction * 100;
}

// "AAAA-MM-JJ HH:MM" (TU) → Date
export function utcDate(text: string) {
	return new Date(text.replace(' ', 'T') + (text.length > 10 ? ':00Z' : 'T00:00:00Z'));
}
