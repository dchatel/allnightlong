<script lang="ts">
	import { moonAltitude, moonIllumination, sunAltitude, targetAltitude, type Observer } from '$lib/astro';

	// Hauteur des cibles et de la Lune pendant la nuit, sur le même axe du temps (TU) et avec les mêmes
	// marges que les graphes météo placés dessous : les heures se lisent à la verticale de l'un à l'autre.
	let {
		targets,
		observer,
		t0,
		t1,
		windowStart = null,
		windowEnd = null,
		hoverTime = $bindable(null)
	}: {
		targets: { name: string; coords: { ra: number; dec: number } }[];
		observer: Observer;
		t0: number;
		t1: number;
		windowStart?: number | null;
		windowEnd?: number | null;
		hoverTime?: number | null;
	} = $props();

	// Mêmes marges que WeatherChart
	const LEFT = 44;
	const RIGHT = 16;
	const HEADER_H = 22;
	const PLOT_H = 130;
	const PAD_B = 8;
	const AXIS_H = 18;
	const STEP_MS = 5 * 60_000;
	// Trois premières teintes de la palette validée (fond sombre) ; la Lune en gris pointillé
	const COLORS = ['#3987e5', '#d95926', '#199e70'];
	const MOON = '#a1a1aa';

	// Fonds du ciel selon la hauteur du Soleil, du jour à la nuit noire
	const SKY = [
		{ above: -0.833, fill: '#34353d', label: 'jour' },
		{ above: -6, fill: '#2b2c34', label: 'crépuscule civil' },
		{ above: -12, fill: '#23242b', label: 'crépuscule nautique' },
		{ above: -18, fill: '#1c1d23', label: 'crépuscule astronomique' },
		{ above: -91, fill: '#131317', label: 'nuit noire' }
	];
	const skyOf = (alt: number) => SKY.find(s => alt > s.above) ?? SKY[SKY.length - 1];

	let width = $state(600);
	let plotW = $derived(Math.max(100, width - LEFT - RIGHT));
	const x = (t: number) => LEFT + (t1 > t0 ? ((t - t0) / (t1 - t0)) * plotW : 0);
	const y = (alt: number) => HEADER_H + PLOT_H - (Math.max(0, Math.min(90, alt)) / 90) * PLOT_H;
	let height = $derived(HEADER_H + PLOT_H + PAD_B + AXIS_H);

	// Cibles d'un même champ (moins d'un degré d'écart) : une seule courbe, nommée par toutes ses cibles
	let groups = $derived.by(() => {
		const list: { names: string[]; coords: { ra: number; dec: number } }[] = [];
		for (const t of targets) {
			const near = list.find(g => Math.abs(g.coords.dec - t.coords.dec) < 1 &&
				Math.abs(g.coords.ra - t.coords.ra) * 15 * Math.cos((t.coords.dec * Math.PI) / 180) < 1);
			if (near) near.names.push(t.name);
			else list.push({ names: [t.name], coords: t.coords });
		}
		return list.slice(0, COLORS.length).map((g, i) => ({ ...g, color: COLORS[i] }));
	});

	let samples = $derived.by(() => {
		const list = [];
		for (let t = t0; t <= t1; t += STEP_MS) {
			const date = new Date(t);
			list.push({
				t,
				sun: sunAltitude(date, observer),
				moon: moonAltitude(date, observer),
				targets: groups.map(g => targetAltitude(g.coords, date, observer))
			});
		}
		return list;
	});

	// Bandes de fond : intervalles consécutifs de même catégorie
	let bands = $derived.by(() => {
		const list: { from: number; to: number; fill: string }[] = [];
		for (const s of samples) {
			const fill = skyOf(s.sun).fill;
			const last = list.at(-1);
			if (last && last.fill === fill) last.to = s.t + STEP_MS;
			else list.push({ from: s.t, to: s.t + STEP_MS, fill });
		}
		return list;
	});

	// Points au-dessus de l'horizon seulement : sous 0°, la courbe s'interrompt
	function path(values: number[]) {
		let d = '';
		let pen = false;
		samples.forEach((s, i) => {
			const v = values[i];
			if (v < 0) { pen = false; return; }
			d += `${pen ? 'L' : 'M'}${x(s.t).toFixed(1)},${y(v).toFixed(1)}`;
			pen = true;
		});
		return d;
	}

	let culminations = $derived(groups.map((_, g) => {
		let best = samples[0];
		for (const s of samples) if (s.targets[g] > best.targets[g]) best = s;
		return best;
	}));

	let moonPercent = $derived(Math.round(moonIllumination(new Date((t0 + t1) / 2))));

	let ticks = $derived.by(() => {
		const hours = (t1 - t0) / 3_600_000;
		const step = [1, 2, 3, 4, 6].find(s => (plotW / hours) * s >= 46) ?? 6;
		const list: number[] = [];
		for (let t = Math.ceil(t0 / 3_600_000) * 3_600_000; t <= t1; t += 3_600_000) {
			if (new Date(t).getUTCHours() % step === 0) list.push(t);
		}
		return list;
	});
	const hm = (t: number) => new Date(t).toISOString().slice(11, 16);

	function onMove(e: MouseEvent) {
		const rect = (e.currentTarget as SVGElement).getBoundingClientRect();
		const t = t0 + ((e.clientX - rect.left - LEFT) / plotW) * (t1 - t0);
		hoverTime = t >= t0 && t <= t1 ? t : null;
	}

	let hovered = $derived(hoverTime == null ? null : samples.reduce((a, b) => (Math.abs(b.t - hoverTime!) < Math.abs(a.t - hoverTime!) ? b : a)));
</script>

<div class="relative" bind:clientWidth={width}>
	<svg {width} {height} role="img" aria-label="Hauteur des cibles pendant la nuit" onmousemove={onMove} onmouseleave={() => (hoverTime = null)} class="block select-none">
		<rect x="0.5" y="0.5" width={width - 1} height={HEADER_H + PLOT_H + PAD_B - 1} rx="6" class="frame" />
		<text x="10" y="15" class="title">Hauteur des cibles (°)</text>

		<!-- Légende : une entrée par champ, puis la Lune -->
		{#each [...groups.map(g => ({ label: g.names.join(' + '), color: g.color, dashed: false })), { label: `Lune ${moonPercent} %`, color: MOON, dashed: true }].reverse() as item, n (item.label)}
			<g transform="translate({width - RIGHT - (n + 1) * 150}, 6)">
				<line x1="0" y1="5" x2="14" y2="5" stroke={item.color} stroke-width="2.5" stroke-dasharray={item.dashed ? '4 3' : undefined} />
				<text x="19" y="9" class="legend">{item.label.length > 22 ? item.label.slice(0, 21) + '…' : item.label}</text>
			</g>
		{/each}

		<!-- Ciel : jour, crépuscules, nuit noire -->
		{#each bands as b (b.from)}
			<rect x={x(b.from)} y={HEADER_H} width={Math.max(0, Math.min(x(b.to), LEFT + plotW) - x(b.from))} height={PLOT_H} fill={b.fill} />
		{/each}

		{#if windowStart != null && windowEnd != null}
			<rect x={x(windowStart)} y={HEADER_H} width={Math.max(0, x(windowEnd) - x(windowStart))} height={PLOT_H} class="window" />
		{/if}

		{#each [0, 30, 60, 90] as v (v)}
			<line x1={LEFT} x2={LEFT + plotW} y1={y(v)} y2={y(v)} class="grid" />
			<text x={LEFT - 6} y={y(v) + 3} class="axis" text-anchor="end">{v}</text>
		{/each}

		<path d={path(samples.map(s => s.moon))} fill="none" stroke={MOON} stroke-width="1.5" stroke-dasharray="4 3" />
		{#each groups as g, i (g.names.join())}
			<path d={path(samples.map(s => s.targets[i]))} fill="none" stroke={g.color} stroke-width="2" stroke-linejoin="round" />
			{@const top = culminations[i]}
			{#if top && top.targets[i] > 0}
				<circle cx={x(top.t)} cy={y(top.targets[i])} r="3.5" fill={g.color} stroke="#19191c" stroke-width="1.5" />
				<text x={Math.min(x(top.t), LEFT + plotW - 60)} y={y(top.targets[i]) - 7} class="peak" text-anchor="middle">{hm(top.t)} · {Math.round(top.targets[i])}°</text>
			{/if}
		{/each}

		{#each ticks as t (t)}
			<text x={x(t)} y={height - 4} class="axis" text-anchor="middle">{hm(t).slice(0, 2)}h</text>
		{/each}

		{#if hovered}
			<line x1={x(hovered.t)} x2={x(hovered.t)} y1={HEADER_H} y2={HEADER_H + PLOT_H} class="crosshair" />
		{/if}
	</svg>

	{#if hovered}
		<div class="tooltip" style="left: {Math.min(x(hovered.t) + 12, width - 200)}px; top: 26px">
			<div class="font-bold text-white mb-1">{hm(hovered.t)} TU</div>
			{#each groups as g, i (g.names.join())}
				<div class="flex items-center gap-2">
					<span class="w-2.5 h-0.5 rounded" style="background: {g.color}"></span>
					<span class="flex-1 text-surface-300 truncate">{g.names.join(' + ')}</span>
					<span class="text-white tabular-nums">{Math.round(hovered.targets[i])}°</span>
				</div>
			{/each}
			<div class="flex items-center gap-2">
				<span class="w-2.5 h-0.5 rounded" style="background: {MOON}"></span>
				<span class="flex-1 text-surface-300">Lune</span>
				<span class="text-white tabular-nums">{Math.round(hovered.moon)}°</span>
			</div>
			<div class="text-surface-500 mt-1">{skyOf(hovered.sun).label}</div>
		</div>
	{/if}
</div>

<style>
	.frame { fill: #19191c; stroke: #333; stroke-width: 1; }
	.title { fill: #e4e4e7; font-size: 11px; font-weight: 700; }
	.legend { fill: #a1a1aa; font-size: 10px; }
	.axis { fill: #8b8b94; font-size: 10px; }
	.peak { fill: #e4e4e7; font-size: 10px; font-weight: 700; }
	.grid { stroke: #ffffff10; stroke-width: 1; }
	.window { fill: rgb(99 102 241 / 0.16); }
	.crosshair { stroke: #a1a1aa; stroke-width: 1; stroke-dasharray: 3 3; }
	.tooltip {
		position: absolute;
		width: 190px;
		padding: 8px 10px;
		font-size: 11px;
		background: #17171a;
		border: 1px solid #3f3f46;
		border-radius: 6px;
		pointer-events: none;
		box-shadow: 0 6px 20px rgb(0 0 0 / 0.5);
	}
</style>
