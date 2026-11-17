<script lang="ts">
	import type { WeatherReading } from '$lib/state.svelte';

	// Météo de la nuit en petits graphes superposés, sur le même axe du temps (TU).
	// Un graphe par grandeur et par unité : jamais deux échelles sur un même graphe.
	let {
		readings,
		windowStart = '',
		windowEnd = ''
	}: { readings: WeatherReading[]; windowStart?: string; windowEnd?: string } = $props();

	type Field = keyof WeatherReading;
	interface Series { field: Field; label: string; color: string; digits: number }
	interface Panel { key: string; title: string; unit: string; fixed?: [number, number]; series: Series[] }

	// Couleurs validées sur le fond sombre : dégradé d'un seul bleu pour les trois couches de nuages
	// (du plus visible, bas, au plus discret, hauts), puis une teinte distincte par grandeur.
	const PANELS: Panel[] = [
		{ key: 'clouds', title: 'Nuages', unit: '%', fixed: [0, 100], series: [
			{ field: 'cloudLow', label: 'bas', color: '#9ec5f4', digits: 0 },
			{ field: 'cloudMid', label: 'moyens', color: '#5598e7', digits: 0 },
			{ field: 'cloudHigh', label: 'hauts', color: '#256abf', digits: 0 }
		] },
		{ key: 'temp', title: 'Température et point de rosée', unit: '°C', series: [
			{ field: 'temp', label: 'température', color: '#d95926', digits: 1 },
			{ field: 'dewPoint', label: 'point de rosée', color: '#199e70', digits: 1 }
		] },
		{ key: 'humidity', title: 'Humidité', unit: '%', fixed: [0, 100], series: [
			{ field: 'humidity', label: 'humidité', color: '#9085e9', digits: 0 }
		] },
		{ key: 'seeing', title: 'Seeing (meteoblue)', unit: '″', series: [
			{ field: 'seeing', label: 'seeing', color: '#d55181', digits: 2 }
		] },
		{ key: 'jet', title: 'Jet stream', unit: 'm/s', series: [
			{ field: 'jetStream', label: 'jet stream', color: '#c98500', digits: 0 }
		] }
	];

	const PLOT_H = 72;
	const TITLE_H = 20;
	const GAP = 10;
	const AXIS_H = 20;
	const LEFT = 40;
	const RIGHT = 14;

	let width = $state(600);
	let hidden = $state<Record<string, boolean>>({ jet: true });
	let hoverIndex = $state<number | null>(null);

	const toMs = (time: string) => new Date(time.replace(' ', 'T') + 'Z').getTime();
	let points = $derived(readings.map(r => ({ r, t: toMs(r.time) })).sort((a, b) => a.t - b.t));

	let available = $derived(PANELS.filter(p => p.series.some(s => readings.some(r => r[s.field] != null))));
	let shown = $derived(available.filter(p => !hidden[p.key]));

	let t0 = $derived(Math.min(...points.map(p => p.t), windowStart ? toMs(windowStart) : Infinity));
	let t1 = $derived(Math.max(...points.map(p => p.t), windowEnd ? toMs(windowEnd) : -Infinity));
	let plotW = $derived(Math.max(100, width - LEFT - RIGHT));
	const x = (t: number) => LEFT + (t1 > t0 ? ((t - t0) / (t1 - t0)) * plotW : plotW / 2);

	let height = $derived(shown.length * (TITLE_H + PLOT_H + GAP) + AXIS_H);
	const panelTop = (i: number) => i * (TITLE_H + PLOT_H + GAP) + TITLE_H;

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
		const mx = e.clientX - rect.left;
		let best = 0;
		points.forEach((p, i) => { if (Math.abs(x(p.t) - mx) < Math.abs(x(points[best].t) - mx)) best = i; });
		hoverIndex = points.length ? best : null;
	}

	let hovered = $derived(hoverIndex == null ? null : points[hoverIndex] ?? null);
	const format = (v: unknown, digits: number) => (v == null ? '—' : (v as number).toFixed(digits));
</script>

{#if readings.length === 0}
	<p class="text-xs text-surface-500">Aucun relevé pour cette nuit.</p>
{:else}
	<!-- Choix des graphes affichés -->
	<div class="flex flex-wrap gap-1.5 mb-2">
		{#each available as panel (panel.key)}
			<button
				type="button"
				onclick={() => (hidden[panel.key] = !hidden[panel.key])}
				class="chip"
				class:chip-on={!hidden[panel.key]}
			>{panel.title}</button>
		{/each}
	</div>

	<div class="relative" bind:clientWidth={width}>
		<svg
			{width}
			{height}
			role="img"
			aria-label="Météo de la nuit"
			onmousemove={onMove}
			onmouseleave={() => (hoverIndex = null)}
			class="block select-none"
		>
			{#each shown as panel, i (panel.key)}
				{@const top = panelTop(i)}
				{@const dom = domain(panel)}
				<!-- Titre et légende du graphe -->
				<text x={LEFT} y={top - 7} class="title">{panel.title} ({panel.unit})</text>
				{#if panel.series.length > 1}
					{#each panel.series as s, n (s.field)}
						<g transform="translate({width - RIGHT - (panel.series.length - n) * 92}, {top - 11})">
							<rect width="10" height="3" y="3" rx="1.5" fill={s.color} />
							<text x="14" y="8" class="legend">{s.label}</text>
						</g>
					{/each}
				{/if}

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
					{#if pts.length > 1}
						<polyline points={pts.map(p => `${p.x},${p.y}`).join(' ')} fill="none" stroke={s.color} stroke-width="2" stroke-linejoin="round" stroke-linecap="round" />
					{/if}
					{#if pts.length < points.length || pts.length === 1}
						{#each pts as p, k (k)}
							<circle cx={p.x} cy={p.y} r="3" fill={s.color} stroke="#1e1e21" stroke-width="1.5" />
						{/each}
					{/if}
					{#if hovered && hovered.r[s.field] != null}
						<circle cx={x(hovered.t)} cy={y(hovered.r[s.field] as number, dom, top)} r="4" fill={s.color} stroke="#1e1e21" stroke-width="2" />
					{/if}
				{/each}
			{/each}

			<!-- Axe du temps -->
			{#each ticks as t (t)}
				<text x={x(t)} y={height - 5} class="axis" text-anchor="middle">{hourLabel(t)}</text>
			{/each}

			{#if hovered}
				<line x1={x(hovered.t)} x2={x(hovered.t)} y1={TITLE_H - 4} y2={height - AXIS_H} class="crosshair" />
			{/if}
		</svg>

		{#if hovered}
			<!-- Toutes les valeurs de l'heure survolée -->
			<div
				class="tooltip"
				style="left: {Math.min(x(hovered.t) + 12, width - 190)}px; top: 4px"
			>
				<div class="font-bold text-white mb-1">{hovered.r.time.slice(11, 16)} TU</div>
				{#each shown as panel (panel.key)}
					{#each panel.series as s (s.field)}
						<div class="flex items-center gap-2">
							<span class="w-2.5 h-0.5 rounded" style="background: {s.color}"></span>
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
	.title { fill: #e4e4e7; font-size: 11px; font-weight: 700; }
	.legend { fill: #a1a1aa; font-size: 10px; }
	.axis { fill: #8b8b94; font-size: 10px; }
	.grid { stroke: #2e2e33; stroke-width: 1; }
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
		padding: 2px 10px;
		border-radius: 999px;
		font-size: 11px;
		background: #202024;
		border: 1px solid #333;
		color: #8b8b94;
	}
	.chip-on {
		border-color: #6366f1;
		color: white;
	}
</style>
