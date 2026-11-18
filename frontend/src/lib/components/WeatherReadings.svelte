<script lang="ts">
	import { appState, parseLegacyCoords, type WeatherReading } from '$lib/state.svelte';
	import { makeObserver, nightEvents, targetCoords, utcDate } from '$lib/astro';
	import AltitudeChart from '$lib/components/AltitudeChart.svelte';
	import WeatherChart from '$lib/components/WeatherChart.svelte';
	import WeatherGrid from '$lib/components/WeatherGrid.svelte';

	// Conditions de la nuit d'une observation : hauteur des cibles et graphes météo sur un même axe du
	// temps, ou tableau météo modifiable, et récupération Open-Meteo.
	let { obs }: { obs: any } = $props();

	let tab = $state<'chart' | 'grid'>('chart');
	// Plage des graphes : la nuit entière (coucher → lever du Soleil) ou le créneau ± marge
	let range = $state<'night' | 'window'>('window');
	let hoverTime = $state<number | null>(null);

	let sessionId = $derived<number | undefined>(obs.sessionId);
	let readings = $derived<WeatherReading[]>(sessionId ? appState.weatherBySession[sessionId] ?? [] : []);
	let status = $derived(sessionId ? appState.weatherStatus[sessionId] ?? '' : '');
	let loading = $derived(status === 'loading');

	let location = $derived(appState.locationById(obs.locationId));

	// Lieu : celui de la session, sinon l'ancienne saisie en texte libre
	let observer = $derived.by(() => {
		const point = location ?? parseLegacyCoords(obs.legacyLocation);
		return point ? makeObserver(point.lat, point.lon, location?.elevationM) : null;
	});

	let windowStart = $derived(obs.start?.length > 10 ? utcDate(obs.start).getTime() : null);
	let windowEnd = $derived(obs.end?.length > 10 ? utcDate(obs.end).getTime() : null);
	let events = $derived(observer && obs.nightDate ? nightEvents(obs.nightDate, observer) : null);

	let bounds = $derived.by(() => {
		const margin = appState.settings.weatherMarginHours * 3_600_000;
		const night = events?.sunset && events?.sunrise ? [events.sunset.getTime(), events.sunrise.getTime()] : null;
		if (range === 'window' && windowStart != null && windowEnd != null) {
			return [windowStart - Math.max(margin, 30 * 60_000), windowEnd + Math.max(margin, 30 * 60_000)];
		}
		return night;
	});

	let targets = $derived(
		(obs.targets ?? [])
			.map((row: any) => appState.targets.find(t => t.id === row.targetId))
			.filter(Boolean)
			.map((t: any) => ({ name: t.name, coords: targetCoords(t) }))
			.filter((t: any) => t.coords)
	);
</script>

<div class="bg-[#1e1e21] p-4 rounded-lg border border-[#333] shrink-0">
	<div class="flex items-center justify-between gap-4 border-b border-[#333] mb-3">
		<span class="text-[10px] uppercase font-bold text-surface-400 whitespace-nowrap pb-1.5">Conditions de la nuit</span>
		<div class="flex items-end gap-4">
			{#if sessionId}
				<button
					type="button"
					disabled={loading}
					onclick={() => appState.fetchWeather(sessionId, readings.length > 0)}
					title={readings.length ? 'Met à jour les relevés Open-Meteo ; les valeurs saisies ou corrigées ne sont pas touchées' : ''}
					class="text-[11px] font-bold text-indigo-400 hover:text-indigo-300 disabled:opacity-40 whitespace-nowrap pb-1.5"
				>
					{loading ? 'Récupération…' : readings.length ? '↻ Rafraîchir depuis Open-Meteo' : 'Récupérer la météo (Open-Meteo)'}
				</button>
				<div class="flex text-[11px] font-bold">
					{#each [{ key: 'chart', label: 'Graphes' }, { key: 'grid', label: 'Tableau météo' }] as t (t.key)}
						<button
							type="button"
							onclick={() => (tab = t.key as 'chart' | 'grid')}
							class="px-3 pb-1.5 border-b-2 transition-colors {tab === t.key ? 'text-white border-indigo-500' : 'text-surface-400 border-transparent hover:text-white'}"
						>{t.label}</button>
					{/each}
				</div>
			{/if}
		</div>
	</div>

	{#if status && !loading}
		<p class="text-[11px] text-yellow-500 mb-2">{status}</p>
	{/if}

	{#if !sessionId}
		<p class="text-xs text-surface-500">La météo sera récupérée à l’enregistrement du rapport.</p>
	{:else if tab === 'chart'}
		{#if events?.sunset && windowStart != null}
			<!-- Plage commune aux graphes de hauteur et de météo -->
			<div class="flex justify-end mb-2">
				<div class="flex rounded-full border border-[#3f3f46] overflow-hidden text-[11px]">
					{#each [{ key: 'window', label: 'Créneau' }, { key: 'night', label: 'Nuit entière' }] as r (r.key)}
						<button
							type="button"
							onclick={() => (range = r.key as 'night' | 'window')}
							class="px-3 py-0.5 transition-colors {range === r.key ? 'bg-indigo-500 text-white font-bold' : 'text-surface-300 hover:text-white'}"
						>{r.label}</button>
					{/each}
				</div>
			</div>
		{/if}

		{#if observer && bounds && targets.length}
			<div class="mb-2">
				<AltitudeChart {targets} {observer} t0={bounds[0]} t1={bounds[1]} {windowStart} {windowEnd}
					horizon={location?.horizon ?? null} minAltitude={location?.minAltitude ?? null} bind:hoverTime />
			</div>
		{:else if !observer}
			<p class="text-xs text-surface-500 mb-2">Choisissez un lieu pour afficher la hauteur des cibles.</p>
		{/if}

		<WeatherChart
			{readings}
			windowStart={obs.start?.length > 10 ? obs.start : ''}
			windowEnd={obs.end?.length > 10 ? obs.end : ''}
			rangeStart={bounds?.[0] ?? null}
			rangeEnd={bounds?.[1] ?? null}
			bind:hoverTime
		/>
	{:else}
		<WeatherGrid {sessionId} nightDate={obs.nightDate} {readings} />
	{/if}
</div>
