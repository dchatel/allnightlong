<script lang="ts">
	import { appState, type WeatherReading } from '$lib/state.svelte';

	// Relevés météo de la nuit (session), en lecture. La grille modifiable et le graphe viendront ensuite.
	let { sessionId }: { sessionId: number | null | undefined } = $props();

	let readings = $derived<WeatherReading[]>(sessionId ? appState.weatherBySession[sessionId] ?? [] : []);
	let status = $derived(sessionId ? appState.weatherStatus[sessionId] ?? '' : '');
	let loading = $derived(status === 'loading');

	const SOURCES: Record<string, string> = { 'open-meteo': 'Open-Meteo', meteoblue: 'meteoblue', manuel: 'Saisie' };

	function value(v: number | null, digits = 0) {
		return v == null ? '—' : v.toFixed(digits);
	}
</script>

<div class="bg-[#1e1e21] p-4 rounded-lg border border-[#333] shrink-0">
	<div class="flex items-center justify-between gap-4 border-b border-[#333] pb-1.5 mb-2">
		<span class="text-[10px] uppercase font-bold text-surface-400 whitespace-nowrap">Conditions de la nuit</span>
		{#if sessionId}
			<button
				type="button"
				disabled={loading}
				onclick={() => appState.fetchWeather(sessionId, readings.length > 0)}
				title={readings.length ? 'Met à jour les relevés Open-Meteo ; les valeurs saisies ou corrigées ne sont pas touchées' : ''}
				class="text-[11px] font-bold text-indigo-400 hover:text-indigo-300 disabled:opacity-40 whitespace-nowrap"
			>
				{loading ? 'Récupération…' : readings.length ? '↻ Rafraîchir depuis Open-Meteo' : 'Récupérer la météo (Open-Meteo)'}
			</button>
		{/if}
	</div>

	{#if status && !loading}
		<p class="text-[11px] text-yellow-500 mb-2">{status}</p>
	{/if}

	{#if readings.length === 0}
		<p class="text-xs text-surface-500">
			{sessionId ? 'Aucun relevé pour cette nuit.' : 'La météo sera récupérée à l’enregistrement du rapport.'}
		</p>
	{:else}
		<div class="overflow-x-auto">
			<table class="w-full text-xs text-right tabular-nums">
				<thead>
					<tr class="text-[10px] text-surface-400">
						<th class="text-left font-normal pb-1">Heure TU</th>
						<th class="font-normal" title="Nuages bas / moyens / hauts">Nuages % (b/m/h)</th>
						<th class="font-normal">Seeing ″</th>
						<th class="font-normal">Idx 1/2</th>
						<th class="font-normal">Jet m/s</th>
						<th class="font-normal">Temp °C</th>
						<th class="font-normal">Hum. %</th>
						<th class="font-normal">Rosée °C</th>
						<th class="font-normal">Source</th>
					</tr>
				</thead>
				<tbody class="text-white">
					{#each readings as r (r.time)}
						<tr class="border-t border-[#2a2a2d]" class:edited={r.edited || r.source !== 'open-meteo'}>
							<td class="text-left py-0.5">{r.time.slice(11, 16)}</td>
							<td>{value(r.cloudLow)} / {value(r.cloudMid)} / {value(r.cloudHigh)}</td>
							<td>{value(r.seeing, 2)}</td>
							<td>{r.index1 == null && r.index2 == null ? '—' : `${value(r.index1)}/${value(r.index2)}`}</td>
							<td>{value(r.jetStream)}</td>
							<td>{value(r.temp, 1)}</td>
							<td>{value(r.humidity)}</td>
							<td>{value(r.dewPoint, 1)}</td>
							<td class="text-surface-400">{SOURCES[r.source] ?? r.source}{r.edited ? ' ✎' : ''}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
</div>

<style>
	.edited td:first-child {
		box-shadow: inset 3px 0 0 #6366f1;
		padding-left: 6px;
	}
</style>
