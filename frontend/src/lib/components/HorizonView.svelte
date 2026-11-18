<script lang="ts">
	import type { Snippet } from 'svelte';
	// Horizon d'un lieu, en bande (0–360° d'azimut) ou en dôme (ciel vu de dessus, nord en haut, est à
	// droite, comme une carte). En modification, on trace l'horizon en glissant la souris : chaque degré
	// d'azimut survolé prend la hauteur du pointeur.
	let {
		alt,
		veg = [],
		mode = 'strip',
		editable = false,
		minAltitude = null,
		maxAltitude = 60,
		hoverAz = $bindable(null),
		onedit = undefined,
		onstrokestart = undefined,
		underlay = undefined
	}: {
		alt: number[];
		veg?: boolean[];
		mode?: 'strip' | 'dome';
		editable?: boolean;
		minAltitude?: number | null;
		maxAltitude?: number;
		hoverAz?: number | null;
		// Nouvelles hauteurs (360 valeurs) pendant le tracé
		onedit?: (alt: number[], touched: number[]) => void;
		// Début d'un tracé : l'éditeur mémorise l'état précédent pour « Annuler »
		onstrokestart?: () => void;
		// Dôme : contenu affiché sous le ciel (la carte des alentours), dans un disque de rayon R pixels
		underlay?: Snippet<[number]>;
	} = $props();

	let width = $state(800);
	// Hauteur disponible : en plein écran, le dôme remplit la colonne sans déborder
	let available = $state(0);
	// Ligne réservée à la lecture de l'azimut survolé, pour que rien ne bouge en dessous
	const READOUT = 20;
	// Motif hachuré propre à cette vue : la végétation ne se distingue pas que par la couleur
	const hatchId = `veg-hatch-${Math.random().toString(36).slice(2, 8)}`;
	let size = $derived(mode === 'dome' ? Math.max(200, Math.min(width, available ? available - READOUT : 520)) : width);
	let height = $derived(mode === 'dome' ? size : 220);

	// --- Bande ---
	const PAD = { left: 34, right: 10, top: 10, bottom: 22 };
	let plotW = $derived(Math.max(100, size - PAD.left - PAD.right));
	let plotH = $derived(height - PAD.top - PAD.bottom);
	const sx = (az: number) => PAD.left + (az / 360) * plotW;
	const sy = (a: number) => PAD.top + plotH - (Math.max(0, Math.min(maxAltitude, a)) / maxAltitude) * plotH;

	// --- Dôme : distance au centre proportionnelle à la distance au zénith ---
	let R = $derived(size / 2 - 22);
	let C = $derived(size / 2);
	const dx = (az: number, a: number) => C + (R * (90 - Math.max(0, Math.min(90, a))) / 90) * Math.sin((az * Math.PI) / 180);
	const dy = (az: number, a: number) => C - (R * (90 - Math.max(0, Math.min(90, a))) / 90) * Math.cos((az * Math.PI) / 180);

	// Segments consécutifs de même nature (végétation ou bâti/relief), pour les colorer différemment
	let runs = $derived.by(() => {
		const list: { from: number; to: number; veg: boolean }[] = [];
		for (let i = 0; i < 360; i++) {
			const v = Boolean(veg[i]);
			const last = list.at(-1);
			if (last && last.veg === v) last.to = i + 1;
			else list.push({ from: i, to: i + 1, veg: v });
		}
		return list;
	});

	function stripArea(from: number, to: number) {
		const pts = [`${sx(from)},${sy(0)}`];
		for (let i = from; i < to; i++) pts.push(`${sx(i)},${sy(alt[i])}`, `${sx(i + 1)},${sy(alt[i])}`);
		pts.push(`${sx(to)},${sy(0)}`);
		return pts.join(' ');
	}

	function domeSector(from: number, to: number) {
		const pts: string[] = [];
		for (let i = from; i < to; i++) pts.push(`${dx(i, alt[i])},${dy(i, alt[i])}`, `${dx(i + 1, alt[i])},${dy(i + 1, alt[i])}`);
		for (let i = to; i >= from; i--) pts.push(`${dx(i, 0)},${dy(i, 0)}`);
		return pts.join(' ');
	}

	let outline = $derived(
		mode === 'dome'
			? Array.from({ length: 360 }, (_, i) => `${dx(i, alt[i])},${dy(i, alt[i])} ${dx(i + 1, alt[i])},${dy(i + 1, alt[i])}`).join(' ')
			: Array.from({ length: 360 }, (_, i) => `${sx(i)},${sy(alt[i])} ${sx(i + 1)},${sy(alt[i])}`).join(' ')
	);

	const CARDINALS = [
		[0, 'N'], [45, 'NE'], [90, 'E'], [135, 'SE'], [180, 'S'], [225, 'SO'], [270, 'O'], [315, 'NO'], [360, 'N']
	] as const;

	// --- Pointeur → (azimut, hauteur) ---
	function pointerToSky(e: PointerEvent) {
		const rect = (e.currentTarget as SVGElement).getBoundingClientRect();
		const px = e.clientX - rect.left, py = e.clientY - rect.top;
		if (mode === 'strip') {
			const az = ((px - PAD.left) / plotW) * 360;
			const a = ((PAD.top + plotH - py) / plotH) * maxAltitude;
			return { az: Math.max(0, Math.min(359.999, az)), alt: a };
		}
		const ddx = px - C, ddy = C - py;
		const az = ((Math.atan2(ddx, ddy) * 180) / Math.PI + 360) % 360;
		const a = 90 - (Math.hypot(ddx, ddy) / R) * 90;
		return { az, alt: a };
	}

	let drawing = false;
	let lastAz: number | null = null;

	function paint(az: number, a: number) {
		const value = Math.round(Math.max(0, Math.min(89, a)) * 10) / 10;
		const next = [...alt];
		const touched: number[] = [];
		const end = Math.floor(az);
		// Tous les degrés entre le point précédent et celui-ci, par le plus court chemin autour du cercle
		let start = lastAz == null ? end : Math.floor(lastAz);
		let delta = ((end - start + 540) % 360) - 180;
		if (mode === 'strip') delta = end - start;
		const steps = Math.abs(delta);
		for (let k = 0; k <= steps; k++) {
			const i = (((start + Math.sign(delta) * k) % 360) + 360) % 360;
			next[i] = value;
			touched.push(i);
		}
		lastAz = az;
		onedit?.(next, touched);
	}

	function onDown(e: PointerEvent) {
		const p = pointerToSky(e);
		hoverAz = Math.floor(p.az);
		if (!editable) return;
		drawing = true;
		lastAz = null;
		(e.currentTarget as Element).setPointerCapture(e.pointerId);
		onstrokestart?.();
		paint(p.az, p.alt);
	}
	function onMove(e: PointerEvent) {
		const p = pointerToSky(e);
		hoverAz = Math.floor(p.az);
		if (drawing) paint(p.az, p.alt);
	}
	function onUp() {
		drawing = false;
		lastAz = null;
	}
</script>

<div bind:clientWidth={width} bind:clientHeight={available} class="w-full relative" class:h-full={mode === 'dome'}>
	{#if mode === 'dome' && underlay}
		<div class="absolute z-0 isolate rounded-full overflow-hidden pointer-events-none" style="left: {C - R}px; top: {C - R}px; width: {2 * R}px; height: {2 * R}px">
			{@render underlay(R)}
		</div>
	{/if}
	<svg
		width={size}
		{height}
		class="block select-none touch-none relative z-10"
		class:cursor-crosshair={editable}
		role="img"
		aria-label={mode === 'dome' ? 'Horizon vu de dessus' : 'Horizon sur 360°'}
		onpointerdown={onDown}
		onpointermove={onMove}
		onpointerup={onUp}
		onpointerleave={() => { if (!drawing) hoverAz = null; }}
	>
		<defs>
			<pattern id={hatchId} width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
				<rect width="6" height="6" fill="#2f4a36" />
				<line x1="0" y1="0" x2="0" y2="6" stroke="#8fc79b" stroke-width="2" />
			</pattern>
		</defs>
		{#if mode === 'strip'}
			<rect x={PAD.left} y={PAD.top} width={plotW} height={plotH} class="sky" />
			{#each [0, 15, 30, 45, 60].filter(v => v <= maxAltitude) as v (v)}
				<line x1={PAD.left} x2={PAD.left + plotW} y1={sy(v)} y2={sy(v)} class="grid" />
				<text x={PAD.left - 5} y={sy(v) + 3} class="axis" text-anchor="end">{v}°</text>
			{/each}
			{#each CARDINALS as [az, label] (az)}
				<line x1={sx(az)} x2={sx(az)} y1={PAD.top} y2={PAD.top + plotH} class="grid" />
				<text x={sx(az)} y={height - 6} class="cardinal" text-anchor="middle">{label}</text>
			{/each}
			{#each runs as r (r.from)}
				<polygon points={stripArea(r.from, r.to)} fill={r.veg ? `url(#${hatchId})` : '#4b4b55'} />
			{/each}
			<polyline points={outline} class="horizon-line" />
			{#if minAltitude != null}
				<line x1={PAD.left} x2={PAD.left + plotW} y1={sy(minAltitude)} y2={sy(minAltitude)} class="min" />
			{/if}
			{#if hoverAz != null}
				<line x1={sx(hoverAz + 0.5)} x2={sx(hoverAz + 0.5)} y1={PAD.top} y2={PAD.top + plotH} class="cursor" />
			{/if}
		{:else}
			<circle cx={C} cy={C} r={R} class="sky" fill-opacity={underlay ? 0.25 : 1} />
			{#each runs as r (r.from)}
				<polygon points={domeSector(r.from, r.to)} fill={r.veg ? `url(#${hatchId})` : '#4b4b55'} fill-opacity={underlay ? 0.6 : 1} />
			{/each}
			{#each [30, 60] as v (v)}
				<circle cx={C} cy={C} r={(R * (90 - v)) / 90} class="grid" fill="none" />
				<text x={C + 3} y={C - (R * (90 - v)) / 90 + 11} class="axis">{v}°</text>
			{/each}
			<circle cx={C} cy={C} r={R} class="grid" fill="none" />
			<polygon points={outline} class="horizon-line" fill="none" />
			{#if underlay}
				<!-- Emplacement de l'instrument, au centre de la photo -->
				<circle cx={C} cy={C} r="4.5" fill="#e11d48" stroke="#fff" stroke-width="1.5" />
			{/if}
			{#if minAltitude != null}
				<circle cx={C} cy={C} r={(R * (90 - minAltitude)) / 90} class="min" fill="none" />
			{/if}
			{#each CARDINALS.slice(0, 8) as [az, label] (az)}
				<text x={dx(az, -6)} y={dy(az, -6) + 4} class="cardinal" text-anchor="middle">{label}</text>
			{/each}
			{#if hoverAz != null}
				<line x1={C} y1={C} x2={dx(hoverAz + 0.5, 0)} y2={dy(hoverAz + 0.5, 0)} class="cursor" />
			{/if}
		{/if}
	</svg>
	{#if editable}
		<span class="block text-[11px] text-surface-300 leading-5" style="height: {READOUT}px">
			{#if hoverAz != null}Azimut {hoverAz}° : horizon à {alt[hoverAz]?.toFixed(1)}°{veg[hoverAz] ? ' (végétation)' : ''}{/if}
		</span>
	{/if}
</div>

<style>
	.sky { fill: #101a2c; }
	.horizon-line { fill: none; stroke: #e4e4e7; stroke-width: 1.2; }
	.grid { stroke: #ffffff18; stroke-width: 1; }
	.axis { fill: #8b8b94; font-size: 10px; }
	.cardinal { fill: #c4c4cc; font-size: 11px; font-weight: 700; }
	.min { stroke: #c98500; stroke-width: 1.2; stroke-dasharray: 5 4; }
	.cursor { stroke: #a5b4fc; stroke-width: 1.2; }
</style>
