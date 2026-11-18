<script lang="ts">
	import { appState, type WeatherReading } from '$lib/state.svelte';
	import WeatherChart from '$lib/components/WeatherChart.svelte';
	import WeatherGrid from '$lib/components/WeatherGrid.svelte';

	// Conditions de la nuit (session) : graphes ou tableau modifiable, et récupération Open-Meteo.
	// windowStart / windowEnd : créneau de l'observation, mis en évidence sur les graphes.
	let {
		sessionId,
		nightDate = '',
		windowStart = '',
		windowEnd = ''
	}: { sessionId: number | null | undefined; nightDate?: string; windowStart?: string; windowEnd?: string } = $props();

	let tab = $state<'chart' | 'grid'>('chart');
	let readings = $derived<WeatherReading[]>(sessionId ? appState.weatherBySession[sessionId] ?? [] : []);
	let status = $derived(sessionId ? appState.weatherStatus[sessionId] ?? '' : '');
	let loading = $derived(status === 'loading');
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
		<WeatherChart {readings} {windowStart} {windowEnd} />
	{:else}
		<WeatherGrid {sessionId} {nightDate} {readings} />
	{/if}
</div>
