<script lang="ts">
	import type { WeatherReading } from '$lib/state.svelte';

	// Météo de la nuit : des graphes encadrés, empilés sur le même axe du temps (TU), un par unité.
	// Jamais deux échelles dans un même graphe : les courbes qui s'y croisent se comparent vraiment.
	// rangeStart / rangeEnd : plage horaire commune avec le graphe de hauteur (ms) ; hoverTime : heure
	// survolée, partagée avec lui pour que les deux lignes verticales se suivent.
	let {
		readings,
		windowStart = '',
		windowEnd = '',
		rangeStart = null,
		rangeEnd = null,
		hoverTime = $bindable(null)
	}: {
		readings: WeatherReading[];
		windowStart?: string;
		windowEnd?: string;
		rangeStart?: number | null;
		rangeEnd?: number | null;
		hoverTime?: number | null;
	} = $props();

	type Field = keyof WeatherReading;
	interface Series { field: Field; label: string; color: string; digits: number; dashed?: boolean }
	interface Panel { key: string; title: string; unit: string; fixed?: [number, number]; series: Series[] }

	// Couleurs validées sur le fond sombre : un seul bleu, du plus clair (bas) au plus foncé (hauts),
	// pour les couches de nuages ; l'humidité, sur la même échelle en %, est en pointillés.
	const PANELS: Panel[] = [
		{ key: 'percent', title: 'Nuages et humidité', unit: '%', fixed: [0, 100], series: [
			{ field: 'cloudLow', label: 'Nuages bas', color: '#9ec5f4', digits: 0 },
			{ field: 'cloudMid', label: 'Nuages moyens', color: '#5598e7', digits: 0 },
			{ field: 'cloudHigh', label: 'Nuages hauts', color: '#256abf', digits: 0 },
			{ field: 'humidity', label: 'Humidité', color: '#9085e9', digits: 0, dashed: true }
		] },
		{ key: 'temp', title: 'Température et point de rosée', unit: '°C', series: [
			{ field: 'temp', label: 'Température', color: '#d95926', digits: 1 },
			{ field: 'dewPoint', label: 'Point de rosée', color: '#199e70', digits: 1, dashed: true }
		] },
		{ key: 'seeing', title: 'Seeing (meteoblue)', unit: '″', series: [
			{ field: 'seeing', label: 'Seeing', color: '#d55181', digits: 2 }
		] },
		{ key: 'jet', title: 'Jet stream', unit: 'm/s', series: [
			{ field: 'jetStream', label: 'Jet stream', color: '#c98500', digits: 0 }
		] }
	];

	const HEADER_H = 22;
	const PLOT_H = 76;
	const PAD_B = 8;
	const GAP = 8;
	const AXIS_H = 18;
	const LEFT = 44;
	const RIGHT = 16;

	let width = $state(600);
	// Courbes masquées (le jet stream l'est d'abord) et courbe mise en avant au survol de sa puce
	let hidden = $state<Partial<Record<Field, boolean>>>({ jetStream: true });
	let focused = $state<Field | null>(null);

	const toMs = (time: string) => new Date(time.replace(' ', 'T') + 'Z').getTime();
	let points = $derived(
		readings
			.map(r => ({ r, t: toMs(r.time) }))
			.filter(p => (rangeStart == null || p.t >= rangeStart) && (rangeEnd == null || p.t <= rangeEnd))
			.sort((a, b) => a.t - b.t)
	);

	const hasData = (field: Field) => readings.some(r => r[field] != null);
	let allSeries = $derived(PANELS.flatMap(p => p.series.map(s => ({ ...s, unit: p.unit }))).filter(s => hasData(s.field)));
	let shown = $derived(
		PANELS.map(p => ({ ...p, series: p.series.filter(s => hasData(s.field) && !hidden[s.field]) })).filter(p => p.series.length)
	);

	let t0 = $derived(rangeStart ?? Math.min(...points.map(p => p.t), windowStart ? toMs(windowStart) : Infinity));
	let t1 = $derived(rangeEnd ?? Math.max(...points.map(p => p.t), windowEnd ? toMs(windowEnd) : -Infinity));
	let plotW = $derived(Math.max(100, width - LEFT - RIGHT));
	const x = (t: number) => LEFT + (t1 > t0 ? ((t - t0) / (t1 - t0)) * plotW : plotW / 2);

	const BLOCK_H = HEADER_H + PLOT_H + PAD_B;
	let height = $derived(shown.length * (BLOCK_H + GAP) - GAP + AXIS_H);
	const blockTop = (i: number) => i * (BLOCK_H + GAP);
	const plotTop = (i: number) => blockTop(i) + HEADER_H;

	function domain(panel: Panel): [number, number] {
		if (panel.fixed) return panel.fixed;
		const values = panel.series.flatMap(s => readings.map(r => r[s.field] as number | null)).filter((v): v is number => v != null);
		let lo = Math.min(...values), hi = Math.max(...values);
		if (hi - lo < 2) { lo -= 1; hi += 1; }
		const pad = (hi - lo) * 0.12;
		return [Math.floor(lo - pad), Math.ceil(hi + pad)];
	}
	const y = (v: number, [lo, hi]: [number, number], top: number) => top + PLOT_H - ((v - lo) / (hi - lo)) * PLOT_H;

	// Points connus d'une grandeur. La ligne passe par-dessus les heures sans valeur (relevés meteoblue
	// toutes les 2 h mêlés aux relevés horaires) ; chaque point est marqué quand la série est clairsemée.
	function seriesPoints(field: Field, dom: [number, number], top: number) {
		return points
			.filter(p => p.r[field] != null)
			.map(p => ({ x: x(p.t), y: y(p.r[field] as number, dom, top) }));
	}

	// Heures pleines de l'axe, espacées selon la largeur disponible
	let ticks = $derived.by(() => {
		if (!(t1 > t0)) return [];
		const hours = (t1 - t0) / 3_600_000;
		const step = [1, 2, 3, 4, 6].find(s => (plotW / hours) * s >= 46) ?? 6;
		const first = Math.ceil(t0 / 3_600_000) * 3_600_000;
		const list: number[] = [];
		for (let t = first; t <= t1; t += 3_600_000) {
			if (new Date(t).getUTCHours() % step === 0) list.push(t);
		}
		return list;
	});
	const hourLabel = (t: number) => `${String(new Date(t).getUTCHours()).padStart(2, '0')}h`;

	function onMove(e: MouseEvent) {
		const rect = (e.currentTarget as SVGElement).getBoundingClientRect();
		const t = t0 + ((e.clientX - rect.left - LEFT) / plotW) * (t1 - t0);
		hoverTime = t >= t0 && t <= t1 ? t : null;
	}

	// Relevé le plus proche de l'heure survolée (ici ou sur le graphe de hauteur), à 45 min près
	let hovered = $derived.by(() => {
		if (hoverTime == null || points.length === 0) return null;
		const best = points.reduce((a, b) => (Math.abs(b.t - hoverTime!) < Math.abs(a.t - hoverTime!) ? b : a));
		return Math.abs(best.t - hoverTime) <= 45 * 60_000 ? best : null;
	});
	const format = (v: unknown, digits: number) => (v == null ? '—' : (v as number).toFixed(digits));
	// Une courbe mise en avant : les autres s'estompent
	const opacity = (field: Field) => (focused && focused !== field ? 0.15 : 1);
</script>

{#if readings.length === 0}
	<p class="text-xs text-surface-500">Aucun relevé pour cette nuit.</p>
{:else}
	<!-- Une puce par courbe : clic pour l'afficher ou la masquer, survol pour la mettre en avant -->
	<div class="flex flex-wrap gap-1.5 mb-3">
		{#each allSeries as s (s.field)}
			<button
				type="button"
				onclick={() => (hidden[s.field] = !hidden[s.field])}
				onmouseenter={() => (focused = hidden[s.field] ? null : s.field)}
				onmouseleave={() => (focused = null)}
				class="chip"
				class:chip-off={hidden[s.field]}
				title={hidden[s.field] ? 'Afficher cette courbe' : 'Masquer cette courbe'}
			>
				<svg width="16" height="6" aria-hidden="true">
					<line x1="1" y1="3" x2="15" y2="3" stroke={s.color} stroke-width="2.5" stroke-linecap="round" stroke-dasharray={s.dashed ? '3 3' : undefined} />
				</svg>
				{s.label}
			</button>
		{/each}
	</div>

	<div class="relative" bind:clientWidth={width}>
		<svg
			{width}
			{height}
			role="img"
			aria-label="Météo de la nuit"
			onmousemove={onMove}
			onmouseleave={() => (hoverTime = null)}
			class="block select-none"
		>
			{#each shown as panel, i (panel.key)}
				{@const top = plotTop(i)}
				{@const dom = domain(panel)}
				<!-- Cadre du graphe -->
				<rect x="0.5" y={blockTop(i) + 0.5} width={width - 1} height={BLOCK_H - 1} rx="6" class="frame" />
				<text x="10" y={blockTop(i) + 15} class="title">{panel.title} ({panel.unit})</text>

				<!-- Créneau de l'observation -->
				{#if windowStart && windowEnd}
					<rect x={x(toMs(windowStart))} y={top} width={Math.max(0, x(toMs(windowEnd)) - x(toMs(windowStart)))} height={PLOT_H} class="window" />
				{/if}

				<!-- Grille discrète : bas, milieu, haut -->
				{#each [dom[0], (dom[0] + dom[1]) / 2, dom[1]] as v (v)}
					<line x1={LEFT} x2={LEFT + plotW} y1={y(v, dom, top)} y2={y(v, dom, top)} class="grid" />
					<text x={LEFT - 6} y={y(v, dom, top) + 3} class="axis" text-anchor="end">{Math.round(v)}</text>
				{/each}

				{#each panel.series as s (s.field)}
					{@const pts = seriesPoints(s.field, dom, top)}
					<g opacity={opacity(s.field)} style="transition: opacity 0.15s">
						{#if pts.length > 1}
							<polyline
								points={pts.map(p => `${p.x},${p.y}`).join(' ')}
								fill="none"
								stroke={s.color}
								stroke-width={focused === s.field ? 3 : 2}
								stroke-dasharray={s.dashed ? '5 4' : undefined}
								stroke-linejoin="round"
								stroke-linecap="round"
							/>
						{/if}
						{#if pts.length < points.length || pts.length === 1}
							{#each pts as p, k (k)}
								<circle cx={p.x} cy={p.y} r="3" fill={s.color} stroke="#1e1e21" stroke-width="1.5" />
							{/each}
						{/if}
						{#if hovered && hovered.r[s.field] != null}
							<circle cx={x(hovered.t)} cy={y(hovered.r[s.field] as number, dom, top)} r="4" fill={s.color} stroke="#1e1e21" stroke-width="2" />
						{/if}
					</g>
				{/each}
			{/each}

			<!-- Axe du temps -->
			{#each ticks as t (t)}
				<text x={x(t)} y={height - 4} class="axis" text-anchor="middle">{hourLabel(t)}</text>
			{/each}

			{#if hoverTime != null}
				<line x1={x(hoverTime)} x2={x(hoverTime)} y1={HEADER_H} y2={height - AXIS_H} class="crosshair" />
			{/if}
		</svg>

		{#if hovered}
			<!-- Toutes les valeurs de l'heure survolée -->
			<div class="tooltip" style="left: {Math.min(x(hovered.t) + 12, width - 190)}px; top: 4px">
				<div class="font-bold text-white mb-1">{hovered.r.time.slice(11, 16)} TU</div>
				{#each shown as panel (panel.key)}
					{#each panel.series as s (s.field)}
						<div class="flex items-center gap-2">
							<svg width="12" height="4" aria-hidden="true">
								<line x1="1" y1="2" x2="11" y2="2" stroke={s.color} stroke-width="2" stroke-dasharray={s.dashed ? '2 2' : undefined} />
							</svg>
							<span class="flex-1 text-surface-300">{s.label}</span>
							<span class="text-white tabular-nums">{format(hovered.r[s.field], s.digits)} {panel.unit}</span>
						</div>
					{/each}
				{/each}
				<div class="text-surface-500 mt-1">{hovered.r.source === 'open-meteo' ? 'Open-Meteo' : hovered.r.source}{hovered.r.edited ? ' · corrigé' : ''}</div>
			</div>
		{/if}
	</div>
{/if}

<style>
	.frame { fill: #19191c; stroke: #333; stroke-width: 1; }
	.title { fill: #e4e4e7; font-size: 11px; font-weight: 700; }
	.axis { fill: #8b8b94; font-size: 10px; }
	.grid { stroke: #2a2a2e; stroke-width: 1; }
	.window { fill: rgb(99 102 241 / 0.12); }
	.crosshair { stroke: #a1a1aa; stroke-width: 1; stroke-dasharray: 3 3; }
	.tooltip {
		position: absolute;
		width: 178px;
		padding: 8px 10px;
		font-size: 11px;
		background: #17171a;
		border: 1px solid #3f3f46;
		border-radius: 6px;
		pointer-events: none;
		box-shadow: 0 6px 20px rgb(0 0 0 / 0.5);
	}
	.chip {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		padding: 2px 10px;
		border-radius: 999px;
		font-size: 11px;
		background: #202024;
		border: 1px solid #3f3f46;
		color: #e4e4e7;
	}
	.chip:hover {
		border-color: #6366f1;
	}
	.chip-off {
		color: #6b6b74;
		border-style: dashed;
	}
	.chip-off svg {
		opacity: 0.35;
	}
</style>
